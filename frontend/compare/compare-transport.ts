/**
 * The filmstrip transport: the play/pause/step/scrub/speed bar together with the
 * playback clock. It is created once and pinned below the stage, rendering in a
 * disabled idle state until a run attaches a {@link FilmstripPlayer}.
 *
 * On `attach` it drives the shared clock (a fixed-rate interval calling
 * `player.advance()`) and mirrors player state into the controls. Board
 * rendering stays with the filmstrip view, which subscribes to the same player
 * independently -- both are notified in lockstep off the one shared index.
 */

import type { FilmstripPlayer, FilmstripPlayerState } from "./filmstrip-player.js";

const DEFAULT_FPS = 8;

/** Playback speed multipliers offered in the transport bar. */
const SPEED_OPTIONS: readonly { label: string; value: number }[] = [
    { label: "0.5×", value: 0.5 },
    { label: "1×", value: 1 },
    { label: "2×", value: 2 },
    { label: "4×", value: 4 },
];

/** Injectable interval clock so playback is deterministic under test. */
export interface IntervalScheduler {
    setInterval(handler: () => void, ms: number): number;
    clearInterval(id: number): void;
}

const WINDOW_SCHEDULER: IntervalScheduler = {
    setInterval: (handler, ms) => window.setInterval(handler, ms),
    clearInterval: (id) => window.clearInterval(id),
};

export interface FilmstripTransportOptions {
    /** Base frames per second at 1× speed. */
    fps?: number;
    /** Overridable clock; defaults to `window.setInterval`. */
    scheduler?: IntervalScheduler;
    /**
     * Before any run is attached, the play button doubles as the primary
     * "Run comparison" action so the dock carries a single control instead of
     * a transport plus a separate run button. Once a player attaches it reverts
     * to play/pause.
     */
    onRun?: () => void;
    /**
     * Fired when playback starts or stops (including a detach while playing).
     * Called only on transitions, never once per frame.
     */
    onPlayStateChange?: (playing: boolean) => void;
}

export interface FilmstripTransportController {
    element: HTMLElement;
    /** Bind to a player: subscribe, drive the clock, and enable the controls. */
    attach(player: FilmstripPlayer): void;
    /** Unbind: stop the clock, unsubscribe, and return the controls to idle. */
    detach(): void;
    /** Pause playback without detaching the current player. */
    pause(): void;
    /** Set the playback speed multiplier (must match a speed-selector option). */
    setSpeed(multiplier: number): void;
    /** Toggle play/pause on the attached player (used by keyboard idioms). */
    toggle(): void;
    /** Step the attached player by `delta` frames (used by keyboard idioms). */
    step(delta: number): void;
    /** Return to generation 0 and pause playback. */
    reset(): void;
    /** Enable/disable the idle "Run comparison" action (needs `onRun`). */
    setIdleRunEnabled(enabled: boolean): void;
    /**
     * Disable the controls while the wall rebuilds. A press accepted mid-rebuild
     * would be wiped when the new filmstrip attaches paused at the seed, so the
     * controls go quiet instead of silently dropping the intent.
     */
    setBusy(busy: boolean): void;
}

function el(tag: string, className: string, text?: string): HTMLElement {
    const node = document.createElement(tag);
    node.className = className;
    if (text !== undefined) {
        node.textContent = text;
    }
    return node;
}

function button(label: string, title: string, onClick: () => void): HTMLButtonElement {
    const node = document.createElement("button");
    node.type = "button";
    node.className = "compare-filmstrip-btn";
    node.textContent = label;
    node.title = title;
    node.setAttribute("aria-label", title);
    node.addEventListener("click", onClick);
    return node;
}

export function createFilmstripTransport(
    options: FilmstripTransportOptions = {},
): FilmstripTransportController {
    const fps = options.fps ?? DEFAULT_FPS;
    const scheduler = options.scheduler ?? WINDOW_SCHEDULER;
    const onRun = options.onRun;

    let currentPlayer: FilmstripPlayer | null = null;
    let unsubscribe: (() => void) | null = null;
    let tickHandle: number | null = null;
    let idleRunEnabled = false;
    let busy = false;
    let lastReportedPlaying = false;

    function reportPlaying(playing: boolean): void {
        if (playing === lastReportedPlaying) {
            return;
        }
        lastReportedPlaying = playing;
        options.onPlayStateChange?.(playing);
    }

    const transport = el("div", "compare-filmstrip-transport");
    transport.setAttribute("role", "group");
    transport.setAttribute("aria-label", "Filmstrip playback controls");

    // Idle (no attached player) the play button runs the comparison; once a
    // player attaches the same button toggles playback.
    const playButton = button("▶ Play", "Play / pause", () => {
        if (currentPlayer) {
            currentPlayer.toggle();
        } else if (onRun && idleRunEnabled) {
            onRun();
        }
    });
    const stepBackButton = button("⏮", "Step back one generation", () => currentPlayer?.step(-1));
    const stepForwardButton = button("⏭", "Step forward one generation", () =>
        currentPlayer?.step(1),
    );
    const resetButton = button("↺", "Back to the seed", () => currentPlayer?.reset());
    const scrubber = document.createElement("input");
    scrubber.type = "range";
    scrubber.className = "compare-filmstrip-scrubber";
    scrubber.min = "0";
    scrubber.max = "0";
    scrubber.value = "0";
    scrubber.setAttribute("aria-label", "Generation");
    scrubber.addEventListener("input", () => currentPlayer?.seek(Number(scrubber.value)));
    const counter = el("span", "compare-filmstrip-counter", "—");
    counter.setAttribute("aria-live", "polite");

    const speedSelect = document.createElement("select");
    speedSelect.className = "compare-filmstrip-speed";
    speedSelect.setAttribute("aria-label", "Playback speed");
    for (const option of SPEED_OPTIONS) {
        const node = document.createElement("option");
        node.value = String(option.value);
        node.textContent = option.label;
        if (option.value === 1) {
            node.selected = true;
        }
        speedSelect.append(node);
    }
    speedSelect.addEventListener("change", () => {
        // Re-time an in-flight clock so the speed change takes effect immediately.
        if (tickHandle !== null) {
            stopTick();
            startTick();
        }
    });

    transport.append(
        resetButton,
        stepBackButton,
        playButton,
        stepForwardButton,
        scrubber,
        counter,
        speedSelect,
    );

    function intervalMs(): number {
        const multiplier = Number(speedSelect.value) || 1;
        return Math.max(16, Math.round(1000 / (fps * multiplier)));
    }

    function startTick(): void {
        tickHandle = scheduler.setInterval(() => currentPlayer?.advance(), intervalMs());
    }

    function stopTick(): void {
        if (tickHandle !== null) {
            scheduler.clearInterval(tickHandle);
            tickHandle = null;
        }
    }

    function disableAllControls(): void {
        for (const control of [playButton, stepBackButton, stepForwardButton, resetButton]) {
            control.disabled = true;
        }
        scrubber.disabled = true;
        speedSelect.disabled = true;
    }

    function setIdle(): void {
        for (const control of [stepBackButton, stepForwardButton, resetButton]) {
            control.disabled = true;
        }
        scrubber.disabled = true;
        scrubber.max = "0";
        scrubber.value = "0";
        speedSelect.disabled = true;
        counter.textContent = "—";
        // With a run action wired, the idle play button is the primary
        // "run comparison" control rather than a dead play/pause.
        if (onRun) {
            playButton.textContent = "Run comparison";
            playButton.title = "Run every selected tiling on a shared clock";
            playButton.setAttribute("aria-label", "Run comparison");
            playButton.disabled = !idleRunEnabled;
        } else {
            playButton.textContent = "▶ Play";
            playButton.title = "Play / pause";
            playButton.setAttribute("aria-label", "Play / pause");
            playButton.disabled = true;
        }
        if (busy) {
            disableAllControls();
        }
    }

    function onState(state: FilmstripPlayerState): void {
        playButton.textContent = state.playing ? "⏸ Pause" : "▶ Play";
        playButton.title = "Play / pause";
        playButton.setAttribute("aria-label", "Play / pause");
        const playable = state.frameCount > 1;
        playButton.disabled = !playable;
        scrubber.disabled = !playable;
        for (const control of [stepBackButton, stepForwardButton, resetButton]) {
            control.disabled = false;
        }
        speedSelect.disabled = false;
        scrubber.max = String(Math.max(0, state.frameCount - 1));
        scrubber.value = String(state.index);
        counter.textContent =
            state.frameCount === 0 ? "—" : `gen ${state.index} / ${state.frameCount - 1}`;

        if (busy) {
            // A rebuild is in flight; the new filmstrip's attach must not
            // re-enable the controls before setBusy(false) lifts the gate.
            disableAllControls();
        }

        if (state.playing && tickHandle === null) {
            startTick();
        } else if (!state.playing && tickHandle !== null) {
            stopTick();
        }
        reportPlaying(state.playing);
    }

    setIdle();

    return {
        element: transport,
        attach(player: FilmstripPlayer): void {
            stopTick();
            unsubscribe?.();
            currentPlayer = player;
            unsubscribe = player.subscribe(onState);
            onState(player.state);
        },
        detach(): void {
            stopTick();
            unsubscribe?.();
            unsubscribe = null;
            currentPlayer = null;
            setIdle();
            reportPlaying(false);
        },
        pause(): void {
            currentPlayer?.pause();
        },
        setSpeed(multiplier: number): void {
            const value = String(multiplier);
            if (SPEED_OPTIONS.some((option) => String(option.value) === value)) {
                speedSelect.value = value;
                if (tickHandle !== null) {
                    stopTick();
                    startTick();
                }
            }
        },
        toggle(): void {
            if (!busy) {
                currentPlayer?.toggle();
            }
        },
        step(delta: number): void {
            if (!busy) {
                currentPlayer?.step(delta);
            }
        },
        reset(): void {
            if (!busy) {
                currentPlayer?.reset();
            }
        },
        setIdleRunEnabled(enabled: boolean): void {
            idleRunEnabled = enabled;
            // Only the idle state exposes the run action; a live player owns the
            // button otherwise.
            if (!currentPlayer && onRun && !busy) {
                playButton.disabled = !enabled;
            }
        },
        setBusy(next: boolean): void {
            busy = next;
            if (busy) {
                disableAllControls();
            } else if (currentPlayer) {
                onState(currentPlayer.state);
            } else {
                setIdle();
            }
        },
    };
}
