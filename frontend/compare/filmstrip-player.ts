/**
 * Synchronized playback model for the live side-by-side compare view.
 *
 * The filmstrip engine returns, per tiling, one board state per generation,
 * with every tiling sharing the same frame count. Playback is therefore a
 * single shared index advanced on one clock: rendering `frames[index]` for
 * every tiling keeps them in lockstep. This model owns only that index and the
 * play/pause state -- it does not render or own a timer. The view drives it by
 * calling `advance()` on each clock tick and reads `index` to draw the frame.
 */

export interface FilmstripPlayerState {
    /** Current frame index, always within [0, frameCount - 1] (0 when empty). */
    index: number;
    playing: boolean;
    frameCount: number;
    atEnd: boolean;
}

export interface FilmstripPlayerOptions {
    /** Loop back to the first frame after the last instead of stopping. */
    loop?: boolean;
}

export type FilmstripPlayerListener = (state: FilmstripPlayerState) => void;

function clampIndex(index: number, frameCount: number): number {
    if (frameCount <= 0) {
        return 0;
    }
    if (index < 0) {
        return 0;
    }
    if (index > frameCount - 1) {
        return frameCount - 1;
    }
    return Math.trunc(index);
}

export class FilmstripPlayer {
    private indexValue = 0;
    private playingValue = false;
    private frameCountValue: number;
    private readonly loop: boolean;
    private readonly listeners = new Set<FilmstripPlayerListener>();

    constructor(frameCount: number, options: FilmstripPlayerOptions = {}) {
        this.frameCountValue = Math.max(0, Math.trunc(frameCount));
        this.loop = options.loop ?? false;
    }

    get index(): number {
        return this.indexValue;
    }

    get playing(): boolean {
        return this.playingValue;
    }

    get frameCount(): number {
        return this.frameCountValue;
    }

    get atEnd(): boolean {
        return this.frameCountValue === 0 || this.indexValue >= this.frameCountValue - 1;
    }

    get state(): FilmstripPlayerState {
        return {
            index: this.indexValue,
            playing: this.playingValue,
            frameCount: this.frameCountValue,
            atEnd: this.atEnd,
        };
    }

    subscribe(listener: FilmstripPlayerListener): () => void {
        this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    }

    play(): void {
        if (this.frameCountValue <= 1) {
            return;
        }
        // Replaying from the end restarts from the first frame.
        if (this.atEnd && !this.loop) {
            this.indexValue = 0;
        }
        this.setPlaying(true);
    }

    pause(): void {
        this.setPlaying(false);
    }

    toggle(): void {
        if (this.playingValue) {
            this.pause();
        } else {
            this.play();
        }
    }

    /** Move by `delta` frames (clamped), pausing playback for manual control. */
    step(delta = 1): void {
        const next = clampIndex(this.indexValue + delta, this.frameCountValue);
        this.update(next, false);
    }

    seek(index: number): void {
        this.update(clampIndex(index, this.frameCountValue), false);
    }

    reset(): void {
        this.update(0, false);
    }

    /** Called by the clock once per tick; advances one frame while playing. */
    advance(): void {
        if (!this.playingValue || this.frameCountValue <= 1) {
            return;
        }
        if (this.indexValue < this.frameCountValue - 1) {
            this.update(this.indexValue + 1, true);
            return;
        }
        if (this.loop) {
            this.update(0, true);
            return;
        }
        // Reached the end of a non-looping filmstrip: stop on the last frame.
        this.setPlaying(false);
    }

    /** Load a new filmstrip length, re-clamping the index and stopping playback. */
    setFrameCount(frameCount: number): void {
        this.frameCountValue = Math.max(0, Math.trunc(frameCount));
        this.indexValue = clampIndex(this.indexValue, this.frameCountValue);
        this.playingValue = false;
        this.notify();
    }

    private setPlaying(playing: boolean): void {
        if (this.playingValue === playing) {
            return;
        }
        this.playingValue = playing;
        this.notify();
    }

    private update(index: number, keepPlaying: boolean): void {
        const changed = index !== this.indexValue || (!keepPlaying && this.playingValue);
        this.indexValue = index;
        if (!keepPlaying) {
            this.playingValue = false;
        }
        if (changed) {
            this.notify();
        }
    }

    private notify(): void {
        const snapshot = this.state;
        for (const listener of this.listeners) {
            listener(snapshot);
        }
    }
}
