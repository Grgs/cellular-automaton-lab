import { createHttpSimulationBackend } from "../api.js";
import type { SimulationBackend } from "../types/controller-api.js";
import type { GridView } from "../types/controller-view.js";
import type {
    AppBootstrapData,
    BootstrappedTopologyDefinition,
    CellIdentifier,
    SimulationSnapshot,
    TopologySpec,
} from "../types/domain.js";

const STORAGE_KEY = "cellular-automaton-lab.live-compare.v1";
const POLL_INTERVAL_MS = 250;

type PaneId = "left" | "right";

interface LiveCompareStorageState {
    initialized?: boolean;
}

export interface LiveCompareWorkspaceOptions {
    trigger: HTMLButtonElement | null;
    gridPanel: HTMLElement | null;
    bootstrapData: AppBootstrapData;
    baseSessionId?: string | null;
    mainBackend?: SimulationBackend;
    backendFactory?: (sessionId: string) => SimulationBackend;
    createGridView?: (canvas: HTMLCanvasElement) => GridView;
    storage?: Storage | null;
    onError?: (error: unknown) => void;
}

export interface LiveCompareWorkspaceHandle {
    dispose(): void;
    isOpen(): boolean;
}

interface PaneElements {
    root: HTMLElement;
    canvas: HTMLCanvasElement;
    status: HTMLElement;
    generation: HTMLElement;
    tilingSelect: HTMLSelectElement;
    runButton: HTMLButtonElement;
    stepButton: HTMLButtonElement;
    resetButton: HTMLButtonElement;
}

interface PaneState {
    id: PaneId;
    title: string;
    sessionId: string;
    backend: SimulationBackend;
    gridView: GridView;
    elements: PaneElements;
    snapshot: SimulationSnapshot | null;
    pollTimer: number | null;
}

function readStorage(storage: Storage | null | undefined): LiveCompareStorageState {
    if (!storage) {
        return {};
    }
    try {
        const raw = storage.getItem(STORAGE_KEY);
        return raw ? (JSON.parse(raw) as LiveCompareStorageState) : {};
    } catch {
        return {};
    }
}

function writeStorage(storage: Storage | null | undefined, state: LiveCompareStorageState): void {
    if (!storage) {
        return;
    }
    try {
        storage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
        // Persistence is best-effort; split view still works for the session.
    }
}

function element<K extends keyof HTMLElementTagNameMap>(
    tag: K,
    className = "",
    text = "",
): HTMLElementTagNameMap[K] {
    const node = document.createElement(tag);
    if (className) {
        node.className = className;
    }
    if (text) {
        node.textContent = text;
    }
    return node;
}

function validSessionIdPart(value: string): string {
    return value.replace(/[^A-Za-z0-9_-]/g, "-").slice(0, 68) || "split";
}

function paneSessionId(baseSessionId: string, paneId: PaneId): string {
    return `${validSessionIdPart(baseSessionId)}-${paneId}`;
}

function topologyGeometry(definition: BootstrappedTopologyDefinition): string {
    return definition.geometry_keys[definition.default_adjacency_mode] || definition.tiling_family;
}

function geometryForSpec(
    definitions: readonly BootstrappedTopologyDefinition[],
    spec: TopologySpec,
): string {
    const definition = definitions.find(
        (candidate) => candidate.tiling_family === spec.tiling_family,
    );
    return definition?.geometry_keys[spec.adjacency_mode] ?? spec.tiling_family;
}

function resetSpecForTopology(
    definition: BootstrappedTopologyDefinition,
    defaults: AppBootstrapData["app_defaults"]["simulation"],
): TopologySpec {
    const defaultSpec = defaults.topology_spec;
    return {
        ...defaultSpec,
        tiling_family: definition.tiling_family,
        adjacency_mode: definition.default_adjacency_mode,
        sizing_mode: definition.sizing_mode,
        patch_depth:
            definition.sizing_policy.control === "patch_depth"
                ? definition.sizing_policy.default
                : defaultSpec.patch_depth,
    };
}

function defaultRuleForTopology(
    definition: BootstrappedTopologyDefinition,
    fallbackRule: string | null,
): string | null {
    return (
        definition.default_rules[definition.default_adjacency_mode] ??
        Object.values(definition.default_rules)[0] ??
        fallbackRule
    );
}

function preferredRightTopology(
    definitions: readonly BootstrappedTopologyDefinition[],
    left: BootstrappedTopologyDefinition,
): BootstrappedTopologyDefinition {
    return (
        definitions.find((definition) => definition.tiling_family === "hex") ??
        definitions.find((definition) => definition.tiling_family !== left.tiling_family) ??
        left
    );
}

function topologyLabel(
    definitions: readonly BootstrappedTopologyDefinition[],
    tilingFamily: string,
): string {
    return (
        definitions.find((definition) => definition.tiling_family === tilingFamily)?.label ??
        tilingFamily
    );
}

function createPaneElements(
    paneId: PaneId,
    title: string,
    definitions: readonly BootstrappedTopologyDefinition[],
): PaneElements {
    const root = element("section", "live-compare-pane");
    root.dataset.pane = paneId;
    root.setAttribute("aria-label", `${title} split view pane`);

    const header = element("header", "live-compare-pane-header");
    const titleNode = element("strong", "live-compare-pane-title", title);
    const status = element("span", "live-compare-pane-status", "Paused");
    const generation = element("span", "live-compare-pane-generation", "Gen 0");
    const meta = element("div", "live-compare-pane-meta");
    meta.append(status, generation);

    const tilingSelect = element("select", "live-compare-tiling-select");
    tilingSelect.setAttribute("aria-label", `${title} tiling`);
    for (const definition of definitions) {
        const option = document.createElement("option");
        option.value = definition.tiling_family;
        option.textContent = definition.label;
        tilingSelect.append(option);
    }

    const runButton = element("button", "live-compare-pane-action", "Run");
    runButton.type = "button";
    const stepButton = element("button", "live-compare-pane-action", "Step");
    stepButton.type = "button";
    const resetButton = element("button", "live-compare-pane-action", "Reset");
    resetButton.type = "button";
    const actions = element("div", "live-compare-pane-actions");
    actions.append(runButton, stepButton, resetButton);
    header.append(titleNode, meta, tilingSelect, actions);

    const viewport = element("div", "live-compare-pane-viewport");
    const canvas = element("canvas", "grid-canvas live-compare-canvas");
    canvas.setAttribute("aria-label", `${title} cellular automaton grid`);
    viewport.append(canvas);
    root.append(header, viewport);

    return {
        root,
        canvas,
        status,
        generation,
        tilingSelect,
        runButton,
        stepButton,
        resetButton,
    };
}

function renderPane(
    pane: PaneState,
    bootstrapData: AppBootstrapData,
    definitions: readonly BootstrappedTopologyDefinition[],
): void {
    const snapshot = pane.snapshot;
    if (!snapshot) {
        pane.elements.status.textContent = "Loading";
        pane.elements.generation.textContent = "Gen -";
        return;
    }
    const geometry = geometryForSpec(definitions, snapshot.topology_spec);
    const cellSize = bootstrapData.app_defaults.ui.cell_size;
    pane.gridView.render?.(
        {
            topology: snapshot.topology,
            cellStates: snapshot.cell_states,
            previewCellStatesById: null,
            tileColorsEnabled: true,
        },
        cellSize,
        snapshot.rule.states,
        geometry,
    );
    pane.elements.status.textContent = snapshot.running ? "Running" : "Paused";
    pane.elements.generation.textContent = `Gen ${snapshot.generation}`;
    pane.elements.runButton.textContent = snapshot.running ? "Pause" : "Run";
    pane.elements.tilingSelect.value = snapshot.topology_spec.tiling_family;
    pane.elements.root.dataset.running = snapshot.running ? "true" : "false";
    pane.elements.root.dataset.tilingLabel = topologyLabel(
        definitions,
        snapshot.topology_spec.tiling_family,
    );
}

export function mountLiveCompareWorkspace({
    trigger,
    gridPanel,
    bootstrapData,
    baseSessionId,
    mainBackend,
    backendFactory = (sessionId) => createHttpSimulationBackend({ sessionId }),
    createGridView = () => {
        throw new Error("Live compare requires a grid view factory.");
    },
    storage = typeof window !== "undefined" ? window.localStorage : null,
    onError = (error) => console.error(error),
}: LiveCompareWorkspaceOptions): LiveCompareWorkspaceHandle {
    if (!trigger || !gridPanel) {
        return { dispose() {}, isOpen: () => false };
    }
    const triggerButton = trigger;
    const hostGridPanel = gridPanel;

    const definitions = [...bootstrapData.topology_catalog].sort(
        (left, right) => left.picker_order - right.picker_order,
    );
    const defaultTopology = definitions[0];
    if (!baseSessionId || !defaultTopology) {
        triggerButton.disabled = true;
        triggerButton.title = "Live split view requires independent server sessions.";
        return { dispose() {}, isOpen: () => false };
    }

    const root = element("section", "live-compare-workspace");
    root.hidden = true;
    root.setAttribute("aria-label", "Live split tiling comparison");
    const mainStage = hostGridPanel.closest(".main-stage");

    const toolbar = element("div", "live-compare-toolbar");
    const summary = element("span", "live-compare-summary", "Split View");
    const runBoth = element("button", "live-compare-action", "Run Both");
    runBoth.type = "button";
    const pauseBoth = element("button", "live-compare-action", "Pause Both");
    pauseBoth.type = "button";
    const stepBoth = element("button", "live-compare-action", "Step Both");
    stepBoth.type = "button";
    toolbar.append(summary, runBoth, pauseBoth, stepBoth);

    const paneGrid = element("div", "live-compare-panes");
    root.append(toolbar, paneGrid);
    hostGridPanel.append(root);

    const paneDefinitions: Record<PaneId, BootstrappedTopologyDefinition> = {
        left: defaultTopology,
        right: preferredRightTopology(definitions, defaultTopology),
    };

    const panes: PaneState[] = (["left", "right"] as PaneId[]).map((paneId) => {
        const elements = createPaneElements(
            paneId,
            paneId === "left" ? "Left" : "Right",
            definitions,
        );
        paneGrid.append(elements.root);
        return {
            id: paneId,
            title: paneId === "left" ? "Left" : "Right",
            sessionId: paneSessionId(baseSessionId, paneId),
            backend: backendFactory(paneSessionId(baseSessionId, paneId)),
            gridView: createGridView(elements.canvas),
            elements,
            snapshot: null,
            pollTimer: null,
        };
    });

    let open = false;
    let disposed = false;

    function clearPoll(pane: PaneState): void {
        if (pane.pollTimer !== null) {
            window.clearInterval(pane.pollTimer);
            pane.pollTimer = null;
        }
    }

    function syncPoll(pane: PaneState): void {
        if (disposed || !open || !pane.snapshot?.running) {
            clearPoll(pane);
            return;
        }
        if (pane.pollTimer !== null) {
            return;
        }
        pane.pollTimer = window.setInterval(() => {
            void refreshPane(pane);
        }, POLL_INTERVAL_MS);
    }

    async function applyPaneSnapshot(pane: PaneState, snapshot: SimulationSnapshot): Promise<void> {
        pane.snapshot = snapshot;
        renderPane(pane, bootstrapData, definitions);
        syncPoll(pane);
    }

    async function refreshPane(pane: PaneState): Promise<void> {
        try {
            await applyPaneSnapshot(pane, await pane.backend.getState());
        } catch (error) {
            onError(error);
            clearPoll(pane);
        }
    }

    async function resetPaneToTopology(
        pane: PaneState,
        definition: BootstrappedTopologyDefinition,
        randomize = false,
    ): Promise<void> {
        const fallbackRule = pane.snapshot?.rule.name ?? bootstrapData.app_defaults.simulation.rule;
        const snapshot = await pane.backend.postControl("/api/control/reset", {
            topology_spec: resetSpecForTopology(definition, bootstrapData.app_defaults.simulation),
            speed: pane.snapshot?.speed ?? bootstrapData.app_defaults.simulation.speed,
            rule: defaultRuleForTopology(definition, fallbackRule),
            randomize,
        });
        await applyPaneSnapshot(pane, snapshot);
    }

    async function initializePaneSessions(): Promise<void> {
        const stored = readStorage(storage);
        if (!stored.initialized) {
            await Promise.all(
                panes.map((pane) => resetPaneToTopology(pane, paneDefinitions[pane.id])),
            );
            writeStorage(storage, { initialized: true });
            return;
        }
        await Promise.all(panes.map((pane) => refreshPane(pane)));
    }

    async function sendPaneRunToggle(pane: PaneState): Promise<void> {
        const snapshot = pane.snapshot ?? (await pane.backend.getState());
        if (snapshot.running) {
            await applyPaneSnapshot(pane, await pane.backend.postControl("/api/control/pause"));
            return;
        }
        const path = snapshot.generation > 0 ? "/api/control/resume" : "/api/control/start";
        await applyPaneSnapshot(pane, await pane.backend.postControl(path));
    }

    async function editPaneCell(pane: PaneState, cell: CellIdentifier): Promise<void> {
        const wasRunning = Boolean(pane.snapshot?.running);
        if (wasRunning) {
            await applyPaneSnapshot(pane, await pane.backend.postControl("/api/control/pause"));
        }
        await applyPaneSnapshot(pane, await pane.backend.toggleCell(cell));
        if (wasRunning) {
            await applyPaneSnapshot(pane, await pane.backend.postControl("/api/control/resume"));
        }
    }

    function setOpen(nextOpen: boolean): void {
        if (open === nextOpen || disposed) {
            return;
        }
        open = nextOpen;
        root.hidden = !open;
        hostGridPanel.classList.toggle("is-live-compare", open);
        mainStage?.classList.toggle("is-live-compare", open);
        triggerButton.setAttribute("aria-pressed", open ? "true" : "false");
        triggerButton.textContent = open ? "Single View" : "Split View";
        if (open) {
            void mainBackend?.postControl("/api/control/pause").catch(onError);
            void initializePaneSessions().catch(onError);
        } else {
            panes.forEach(clearPoll);
        }
    }

    function handleTriggerClick(): void {
        setOpen(!open);
    }

    triggerButton.setAttribute("aria-pressed", "false");
    triggerButton.textContent = "Split View";
    triggerButton.addEventListener("click", handleTriggerClick);

    for (const pane of panes) {
        pane.elements.root.addEventListener("pointerdown", (event) => {
            panes.forEach((candidate) =>
                candidate.elements.root.classList.toggle("is-active", candidate === pane),
            );
            pane.elements.root.focus();
            event.stopPropagation();
        });
        pane.elements.canvas.addEventListener("click", (event) => {
            const cell = pane.gridView.getCellFromPointerEvent?.(event) ?? null;
            if (!cell) {
                return;
            }
            void editPaneCell(pane, cell).catch(onError);
        });
        pane.elements.tilingSelect.addEventListener("change", () => {
            const definition = definitions.find(
                (candidate) => candidate.tiling_family === pane.elements.tilingSelect.value,
            );
            if (definition) {
                void resetPaneToTopology(pane, definition).catch(onError);
            }
        });
        pane.elements.runButton.addEventListener("click", () => {
            void sendPaneRunToggle(pane).catch(onError);
        });
        pane.elements.stepButton.addEventListener("click", () => {
            void pane.backend
                .postControl("/api/control/step")
                .then((snapshot) => applyPaneSnapshot(pane, snapshot))
                .catch(onError);
        });
        pane.elements.resetButton.addEventListener("click", () => {
            const definition =
                definitions.find(
                    (candidate) => candidate.tiling_family === pane.elements.tilingSelect.value,
                ) ?? paneDefinitions[pane.id];
            void resetPaneToTopology(pane, definition).catch(onError);
        });
    }

    runBoth.addEventListener("click", () => {
        void Promise.all(
            panes.map(async (pane) => {
                const snapshot = pane.snapshot ?? (await pane.backend.getState());
                if (!snapshot.running) {
                    await sendPaneRunToggle(pane);
                }
            }),
        ).catch(onError);
    });
    pauseBoth.addEventListener("click", () => {
        void Promise.all(
            panes.map(async (pane) => {
                const snapshot = pane.snapshot ?? (await pane.backend.getState());
                if (snapshot.running) {
                    await applyPaneSnapshot(
                        pane,
                        await pane.backend.postControl("/api/control/pause"),
                    );
                }
            }),
        ).catch(onError);
    });
    stepBoth.addEventListener("click", () => {
        void Promise.all(
            panes.map((pane) =>
                pane.backend
                    .postControl("/api/control/step")
                    .then((snapshot) => applyPaneSnapshot(pane, snapshot)),
            ),
        ).catch(onError);
    });

    function handleResize(): void {
        if (open) {
            panes.forEach((pane) => renderPane(pane, bootstrapData, definitions));
        }
    }

    window.addEventListener("resize", handleResize);

    return {
        dispose(): void {
            disposed = true;
            panes.forEach((pane) => {
                clearPoll(pane);
                void Promise.resolve(pane.backend.dispose()).catch(onError);
            });
            root.remove();
            hostGridPanel.classList.remove("is-live-compare");
            mainStage?.classList.remove("is-live-compare");
            window.removeEventListener("resize", handleResize);
            triggerButton.removeEventListener("click", handleTriggerClick);
            triggerButton.setAttribute("aria-pressed", "false");
            triggerButton.textContent = "Split View";
        },
        isOpen: () => open,
    };
}

export const liveCompareInternals = {
    paneSessionId,
    resetSpecForTopology,
    topologyGeometry,
    geometryForSpec,
};
