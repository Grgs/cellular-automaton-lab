export const COMPARE_LAYOUT_STORAGE_KEY = "cellular-automaton-lab.compare-layout.v1";
export const COMPARE_LAYOUT_RESET_EVENT = "cellular-automaton-lab:reset-compare-layout";

export const COMPARE_LAYOUT_DEFAULTS = {
    setupWidth: 250,
    inspectorWidth: 270,
    setupCollapsed: true,
    inspectorCollapsed: true,
} as const satisfies CompareWorkspaceLayoutState;

const SETUP_MIN = 220;
const SETUP_MAX = 420;
const INSPECTOR_MIN = 240;
const INSPECTOR_MAX = 440;
const WALL_MIN = 400;
const SPLITTER_WIDTH = 10;
const DESKTOP_BREAKPOINT = 960;

interface CompareWorkspaceLayoutOptions {
    setup: HTMLElement;
    boardWall: HTMLElement;
    inspector: HTMLElement;
    dock: HTMLElement;
    setupToggle: HTMLButtonElement;
    inspectorToggle: HTMLButtonElement;
    storage?: Storage | null;
    resetEventTarget?: EventTarget;
}

export interface CompareWorkspaceLayoutState {
    setupWidth: number;
    inspectorWidth: number;
    setupCollapsed: boolean;
    inspectorCollapsed: boolean;
}

export interface CompareWorkspaceLayout {
    element: HTMLElement;
    setupSeparator: HTMLElement;
    inspectorSeparator: HTMLElement;
    getState(): CompareWorkspaceLayoutState;
    openSetup(): void;
    openInspector(): void;
    closeSetup(): boolean;
    closeInspector(): boolean;
    closeDrawer(): boolean;
    reset(): void;
    dispose(): void;
}

let panelId = 0;

function safeStorage(): Storage | null {
    try {
        return window.localStorage;
    } catch {
        return null;
    }
}

function finiteNumber(value: unknown, fallback: number): number {
    return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function booleanValue(value: unknown, fallback: boolean): boolean {
    return typeof value === "boolean" ? value : fallback;
}

function clamp(value: number, minimum: number, maximum: number): number {
    return Math.min(maximum, Math.max(minimum, value));
}

function readState(storage: Storage | null): {
    state: CompareWorkspaceLayoutState;
    hadStoredValue: boolean;
} {
    let raw: string | null = null;
    try {
        raw = storage?.getItem(COMPARE_LAYOUT_STORAGE_KEY) ?? null;
    } catch {
        return { state: { ...COMPARE_LAYOUT_DEFAULTS }, hadStoredValue: false };
    }
    if (raw === null) {
        return { state: { ...COMPARE_LAYOUT_DEFAULTS }, hadStoredValue: false };
    }
    try {
        const parsed = JSON.parse(raw) as Record<string, unknown> | null;
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
            return { state: { ...COMPARE_LAYOUT_DEFAULTS }, hadStoredValue: true };
        }
        return {
            state: {
                setupWidth: clamp(
                    finiteNumber(parsed.setupWidth, COMPARE_LAYOUT_DEFAULTS.setupWidth),
                    SETUP_MIN,
                    SETUP_MAX,
                ),
                inspectorWidth: clamp(
                    finiteNumber(parsed.inspectorWidth, COMPARE_LAYOUT_DEFAULTS.inspectorWidth),
                    INSPECTOR_MIN,
                    INSPECTOR_MAX,
                ),
                setupCollapsed: booleanValue(
                    parsed.setupCollapsed,
                    COMPARE_LAYOUT_DEFAULTS.setupCollapsed,
                ),
                inspectorCollapsed: booleanValue(
                    parsed.inspectorCollapsed,
                    COMPARE_LAYOUT_DEFAULTS.inspectorCollapsed,
                ),
            },
            hadStoredValue: true,
        };
    } catch {
        return { state: { ...COMPARE_LAYOUT_DEFAULTS }, hadStoredValue: true };
    }
}

/** Clear the Compare-only layout preference and notify a mounted workspace immediately. */
export function resetStoredCompareWorkspaceLayout({
    storage = safeStorage(),
    eventTarget = window,
}: {
    storage?: Storage | null;
    eventTarget?: EventTarget;
} = {}): void {
    try {
        storage?.removeItem(COMPARE_LAYOUT_STORAGE_KEY);
    } catch {
        // Storage can be unavailable or blocked; the live reset still applies.
    }
    eventTarget.dispatchEvent(new Event(COMPARE_LAYOUT_RESET_EVENT));
}

/** Compose existing workspace nodes without recreating their interactive DOM. */
export function createCompareWorkspaceLayout(
    options: CompareWorkspaceLayoutOptions,
): CompareWorkspaceLayout {
    const {
        setup,
        boardWall,
        inspector,
        dock,
        setupToggle,
        inspectorToggle,
        storage = safeStorage(),
        resetEventTarget = window,
    } = options;
    const loaded = readState(storage);
    let state: CompareWorkspaceLayoutState = loaded.state;
    let returnFocus: HTMLElement | null = null;
    let activePointer:
        | {
              side: "setup" | "inspector";
              pointerId: number;
              startX: number;
              startWidth: number;
          }
        | undefined;
    let wasNarrow = window.innerWidth < DESKTOP_BREAKPOINT;
    let observedWorkspaceWidth = 0;

    if (!setup.id) {
        setup.id = `compare-setup-panel-${++panelId}`;
    }
    if (!inspector.id) {
        inspector.id = `compare-inspector-panel-${++panelId}`;
    }

    const backdrop = document.createElement("button");
    backdrop.className = "compare-workspace-backdrop";
    backdrop.type = "button";
    backdrop.tabIndex = -1;
    backdrop.setAttribute("aria-label", "Close Compare drawer");

    function separator(side: "setup" | "inspector"): HTMLElement {
        const node = document.createElement("div");
        const label = side === "setup" ? "Resize Setup panel" : "Resize Inspector panel";
        node.className = `compare-workspace-separator compare-workspace-separator-${side}`;
        node.tabIndex = 0;
        node.setAttribute("role", "separator");
        node.setAttribute("aria-label", label);
        node.setAttribute("aria-orientation", "vertical");
        node.setAttribute("aria-controls", side === "setup" ? setup.id : inspector.id);
        return node;
    }

    const setupSeparator = separator("setup");
    const inspectorSeparator = separator("inspector");
    const grid = document.createElement("div");
    grid.className = "compare-workspace-grid";
    grid.append(setup, setupSeparator, boardWall, inspectorSeparator, inspector);
    const root = document.createElement("div");
    root.className = "wall-screen compare-workspace";
    root.append(grid, dock, backdrop);

    const isNarrow = (): boolean => window.innerWidth < DESKTOP_BREAKPOINT;

    function workspaceWidth(): number {
        const measured = grid.getBoundingClientRect().width || root.getBoundingClientRect().width;
        return measured > 0 ? measured : window.innerWidth;
    }

    function activeSeparatorCount(candidate?: {
        side: "setup" | "inspector";
        open: boolean;
    }): number {
        const setupOpen = candidate?.side === "setup" ? candidate.open : !state.setupCollapsed;
        const inspectorOpen =
            candidate?.side === "inspector" ? candidate.open : !state.inspectorCollapsed;
        return Number(setupOpen) + Number(inspectorOpen);
    }

    function applicableMaximum(side: "setup" | "inspector"): number {
        const otherWidth =
            side === "setup"
                ? state.inspectorCollapsed
                    ? 0
                    : state.inspectorWidth
                : state.setupCollapsed
                  ? 0
                  : state.setupWidth;
        const available =
            workspaceWidth() -
            WALL_MIN -
            activeSeparatorCount({ side, open: true }) * SPLITTER_WIDTH -
            otherWidth;
        const staticMaximum = side === "setup" ? SETUP_MAX : INSPECTOR_MAX;
        const minimum = side === "setup" ? SETUP_MIN : INSPECTOR_MIN;
        return Math.max(minimum, Math.min(staticMaximum, Math.floor(available)));
    }

    function reconcileWidths(): boolean {
        const before = `${state.setupWidth}:${state.inspectorWidth}`;
        state.setupWidth = clamp(state.setupWidth, SETUP_MIN, SETUP_MAX);
        state.inspectorWidth = clamp(state.inspectorWidth, INSPECTOR_MIN, INSPECTOR_MAX);
        if (!state.setupCollapsed && !state.inspectorCollapsed) {
            const budget = workspaceWidth() - WALL_MIN - activeSeparatorCount() * SPLITTER_WIDTH;
            let overflow = state.setupWidth + state.inspectorWidth - budget;
            if (overflow > 0) {
                const inspectorReduction = Math.min(overflow, state.inspectorWidth - INSPECTOR_MIN);
                state.inspectorWidth -= inspectorReduction;
                overflow -= inspectorReduction;
                state.setupWidth -= Math.min(overflow, state.setupWidth - SETUP_MIN);
            }
        }
        return before !== `${state.setupWidth}:${state.inspectorWidth}`;
    }

    function persist(): void {
        try {
            storage?.setItem(COMPARE_LAYOUT_STORAGE_KEY, JSON.stringify(state));
        } catch {
            // The layout remains fully usable when storage is disabled or full.
        }
    }

    function rememberFocus(): void {
        returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    }

    function syncSeparator(node: HTMLElement, side: "setup" | "inspector", visible: boolean): void {
        const value = side === "setup" ? state.setupWidth : state.inspectorWidth;
        const minimum = side === "setup" ? SETUP_MIN : INSPECTOR_MIN;
        const maximum = applicableMaximum(side);
        node.tabIndex = visible ? 0 : -1;
        node.setAttribute("aria-hidden", visible ? "false" : "true");
        node.setAttribute("aria-valuemin", String(minimum));
        node.setAttribute("aria-valuemax", String(maximum));
        node.setAttribute("aria-valuenow", String(value));
        node.setAttribute(
            "aria-valuetext",
            `${side === "setup" ? "Setup" : "Inspector"} width ${value} pixels`,
        );
    }

    function sync(): void {
        const narrow = isNarrow();
        if (!narrow) {
            setup.classList.toggle("is-open", !state.setupCollapsed);
            inspector.classList.toggle("is-open", !state.inspectorCollapsed);
        }
        const setupOpen = setup.classList.contains("is-open");
        const inspectorOpen = inspector.classList.contains("is-open");
        setup.toggleAttribute("inert", !setupOpen);
        inspector.toggleAttribute("inert", !inspectorOpen);
        setupToggle.setAttribute("aria-expanded", setupOpen ? "true" : "false");
        inspectorToggle.setAttribute("aria-expanded", inspectorOpen ? "true" : "false");
        root.classList.toggle("has-open-drawer", narrow && (setupOpen || inspectorOpen));
        root.style.setProperty("--compare-setup-width", `${state.setupWidth}px`);
        root.style.setProperty("--compare-inspector-width", `${state.inspectorWidth}px`);
        root.style.setProperty(
            "--compare-setup-column",
            setupOpen ? `${state.setupWidth}px` : "0px",
        );
        root.style.setProperty(
            "--compare-inspector-column",
            inspectorOpen ? `${state.inspectorWidth}px` : "0px",
        );
        root.style.setProperty(
            "--compare-setup-splitter",
            setupOpen ? `${SPLITTER_WIDTH}px` : "0px",
        );
        root.style.setProperty(
            "--compare-inspector-splitter",
            inspectorOpen ? `${SPLITTER_WIDTH}px` : "0px",
        );
        syncSeparator(setupSeparator, "setup", !narrow && setupOpen);
        syncSeparator(inspectorSeparator, "inspector", !narrow && inspectorOpen);
    }

    function close(node: HTMLElement, side: "setup" | "inspector"): boolean {
        if (!node.classList.contains("is-open")) {
            return false;
        }
        node.classList.remove("is-open");
        if (!isNarrow()) {
            if (side === "setup") {
                state.setupCollapsed = true;
            } else {
                state.inspectorCollapsed = true;
            }
            persist();
        }
        sync();
        returnFocus?.focus();
        returnFocus = null;
        return true;
    }

    function open(node: HTMLElement, other: HTMLElement, side: "setup" | "inspector"): void {
        rememberFocus();
        if (isNarrow()) {
            other.classList.remove("is-open");
        } else if (side === "setup") {
            state.setupCollapsed = false;
        } else {
            state.inspectorCollapsed = false;
        }
        node.classList.add("is-open");
        if (!isNarrow()) {
            reconcileWidths();
            persist();
        }
        sync();
    }

    function updateWidth(
        side: "setup" | "inspector",
        requested: number,
        persistChange: boolean,
    ): void {
        const minimum = side === "setup" ? SETUP_MIN : INSPECTOR_MIN;
        const next = clamp(Math.round(requested), minimum, applicableMaximum(side));
        if (side === "setup") {
            state.setupWidth = next;
        } else {
            state.inspectorWidth = next;
        }
        sync();
        if (persistChange) {
            persist();
        }
    }

    function handlePointerDown(side: "setup" | "inspector", event: PointerEvent): void {
        if (isNarrow() || event.button !== 0) {
            return;
        }
        event.preventDefault();
        const startWidth = side === "setup" ? state.setupWidth : state.inspectorWidth;
        activePointer = {
            side,
            pointerId: event.pointerId,
            startX: event.clientX,
            startWidth,
        };
        const node = side === "setup" ? setupSeparator : inspectorSeparator;
        node.classList.add("is-dragging");
        root.classList.add("is-resizing");
        node.focus();
        window.addEventListener("pointermove", onPointerMove);
        window.addEventListener("pointerup", onPointerEnd);
        window.addEventListener("pointercancel", onPointerEnd);
    }

    function onPointerMove(event: PointerEvent): void {
        if (!activePointer || event.pointerId !== activePointer.pointerId) {
            return;
        }
        event.preventDefault();
        const delta = event.clientX - activePointer.startX;
        updateWidth(
            activePointer.side,
            activePointer.startWidth + (activePointer.side === "setup" ? delta : -delta),
            false,
        );
    }

    function onPointerEnd(event: PointerEvent): void {
        if (!activePointer || event.pointerId !== activePointer.pointerId) {
            return;
        }
        const node = activePointer.side === "setup" ? setupSeparator : inspectorSeparator;
        node.classList.remove("is-dragging");
        root.classList.remove("is-resizing");
        activePointer = undefined;
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("pointerup", onPointerEnd);
        window.removeEventListener("pointercancel", onPointerEnd);
        persist();
    }

    function handleKeydown(side: "setup" | "inspector", event: KeyboardEvent): void {
        if (isNarrow()) {
            return;
        }
        const current = side === "setup" ? state.setupWidth : state.inspectorWidth;
        const step = event.shiftKey ? 40 : 10;
        let next: number;
        if (event.key === "Home") {
            next = side === "setup" ? SETUP_MIN : INSPECTOR_MIN;
        } else if (event.key === "End") {
            next = applicableMaximum(side);
        } else if (event.key === "ArrowLeft") {
            next = current + (side === "setup" ? -step : step);
        } else if (event.key === "ArrowRight") {
            next = current + (side === "setup" ? step : -step);
        } else {
            return;
        }
        event.preventDefault();
        event.stopPropagation();
        updateWidth(side, next, true);
    }

    const layout: CompareWorkspaceLayout = {
        element: root,
        setupSeparator,
        inspectorSeparator,
        getState: () => ({ ...state }),
        openSetup: () => open(setup, inspector, "setup"),
        openInspector: () => open(inspector, setup, "inspector"),
        closeSetup: () => close(setup, "setup"),
        closeInspector: () => close(inspector, "inspector"),
        closeDrawer(): boolean {
            return layout.closeInspector() || layout.closeSetup();
        },
        reset(): void {
            state = { ...COMPARE_LAYOUT_DEFAULTS };
            setup.classList.remove("is-open");
            inspector.classList.remove("is-open");
            try {
                storage?.removeItem(COMPARE_LAYOUT_STORAGE_KEY);
            } catch {
                // A live reset does not depend on storage access.
            }
            sync();
        },
        dispose(): void {
            backdrop.removeEventListener("click", layout.closeDrawer);
            setupSeparator.removeEventListener("pointerdown", onSetupPointerDown);
            inspectorSeparator.removeEventListener("pointerdown", onInspectorPointerDown);
            setupSeparator.removeEventListener("keydown", onSetupKeydown);
            inspectorSeparator.removeEventListener("keydown", onInspectorKeydown);
            window.removeEventListener("pointermove", onPointerMove);
            window.removeEventListener("pointerup", onPointerEnd);
            window.removeEventListener("pointercancel", onPointerEnd);
            window.removeEventListener("resize", handleBreakpointChange);
            resetEventTarget.removeEventListener(COMPARE_LAYOUT_RESET_EVENT, handleResetEvent);
            resizeObserver?.disconnect();
        },
    };

    function handleBreakpointChange(): void {
        const nowNarrow = isNarrow();
        if (nowNarrow && !wasNarrow) {
            setup.classList.remove("is-open");
            inspector.classList.remove("is-open");
        } else if (!nowNarrow) {
            if (reconcileWidths()) {
                persist();
            }
        }
        wasNarrow = nowNarrow;
        sync();
    }

    const resizeObserver =
        typeof ResizeObserver === "undefined"
            ? null
            : new ResizeObserver((entries) => {
                  const width = Math.floor(entries[0]?.contentRect.width ?? workspaceWidth());
                  if (width <= 0 || width === observedWorkspaceWidth) {
                      return;
                  }
                  observedWorkspaceWidth = width;
                  if (!isNarrow() && reconcileWidths()) {
                      persist();
                  }
                  sync();
              });

    const onSetupPointerDown = (event: PointerEvent): void => handlePointerDown("setup", event);
    const onInspectorPointerDown = (event: PointerEvent): void =>
        handlePointerDown("inspector", event);
    const onSetupKeydown = (event: KeyboardEvent): void => handleKeydown("setup", event);
    const onInspectorKeydown = (event: KeyboardEvent): void => handleKeydown("inspector", event);
    const handleResetEvent = (): void => layout.reset();

    backdrop.addEventListener("click", layout.closeDrawer);
    setupSeparator.addEventListener("pointerdown", onSetupPointerDown);
    inspectorSeparator.addEventListener("pointerdown", onInspectorPointerDown);
    setupSeparator.addEventListener("keydown", onSetupKeydown);
    inspectorSeparator.addEventListener("keydown", onInspectorKeydown);
    window.addEventListener("resize", handleBreakpointChange);
    resetEventTarget.addEventListener(COMPARE_LAYOUT_RESET_EVENT, handleResetEvent);
    resizeObserver?.observe(grid);

    if (loaded.hadStoredValue && reconcileWidths()) {
        persist();
    } else if (loaded.hadStoredValue) {
        // Normalize malformed and obsolete shapes to the current v1 contract.
        persist();
    }
    if (wasNarrow) {
        setup.classList.remove("is-open");
        inspector.classList.remove("is-open");
    }
    sync();
    return layout;
}
