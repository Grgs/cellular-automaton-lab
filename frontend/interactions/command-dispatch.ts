import type {
    ConfigSyncBody,
    ControlCommandMap,
    EmptyControlCommandPath,
    PostControlFunction,
    ResetControlBody,
    SetCellRequestFunction,
    SimulationMutationOptions,
    ToggleCellRequestFunction,
} from "../types/controller.js";
import type { PaintableCell } from "../types/editor.js";
import type { SimulationSnapshot } from "../types/domain.js";
import type { SimulationMutations } from "../types/controller.js";

interface InteractionCommandDispatch {
    paintCell(cell: PaintableCell, stateValue?: number): Promise<void>;
    resolveDirectGestureTargetState(cell: PaintableCell): number;
    toggleCell(cell: PaintableCell): Promise<void>;
    sendControl(path: EmptyControlCommandPath, options?: SimulationMutationOptions): Promise<SimulationSnapshot | null>;
    sendControl(
        path: "/api/control/reset",
        body: ResetControlBody,
        options?: SimulationMutationOptions,
    ): Promise<SimulationSnapshot | null>;
    sendControl(
        path: "/api/config",
        body: ConfigSyncBody,
        options?: SimulationMutationOptions,
    ): Promise<SimulationSnapshot | null>;
    runSerialized<T>(task: () => Promise<T>, options?: SimulationMutationOptions): Promise<T>;
}

export function createInteractionCommandDispatch({
    mutations,
    toggleCellRequest,
    setCellRequest,
    postControl,
    getPaintState,
    getCellState,
}: {
    mutations: Pick<SimulationMutations, "runStateMutation" | "runSerialized">;
    toggleCellRequest: ToggleCellRequestFunction;
    setCellRequest: SetCellRequestFunction;
    postControl: PostControlFunction;
    getPaintState: () => number;
    getCellState: (cell: PaintableCell) => number;
}): InteractionCommandDispatch {
    async function paintCell(cell: PaintableCell, stateValue = getPaintState()): Promise<void> {
        if (typeof cell !== "object" || cell === null) {
            throw new Error("Cell painting requires a resolved topology cell.");
        }
        await mutations.runStateMutation(() => setCellRequest(cell, stateValue), { source: "editor" }).catch(() => null);
    }

    async function toggleCell(cell: PaintableCell): Promise<void> {
        if (typeof cell !== "object" || cell === null) {
            throw new Error("Cell toggles require a resolved topology cell.");
        }
        await mutations.runStateMutation(() => toggleCellRequest(cell), { source: "editor" }).catch(() => null);
    }

    function resolveDirectGestureTargetState(cell: PaintableCell): number {
        if (typeof cell !== "object" || cell === null) {
            throw new Error("Cell toggles require a resolved topology cell.");
        }
        return getCellState(cell) === 0 ? getPaintState() : 0;
    }

    async function sendControl(path: EmptyControlCommandPath, options?: SimulationMutationOptions): Promise<SimulationSnapshot | null>;
    async function sendControl(
        path: "/api/control/reset",
        body: ResetControlBody,
        options?: SimulationMutationOptions,
    ): Promise<SimulationSnapshot | null>;
    async function sendControl(
        path: "/api/config",
        body: ConfigSyncBody,
        options?: SimulationMutationOptions,
    ): Promise<SimulationSnapshot | null>;
    async function sendControl<TPath extends keyof ControlCommandMap>(
        path: TPath,
        bodyOrOptions?: ControlCommandMap[TPath] | SimulationMutationOptions,
        maybeOptions: SimulationMutationOptions = {},
    ): Promise<SimulationSnapshot | null> {
        if (path === "/api/control/reset") {
            const body = bodyOrOptions as ResetControlBody;
            return await mutations.runStateMutation(
                () => postControl(path, body),
                { source: "control", ...maybeOptions },
            ).catch(() => null);
        }
        if (path === "/api/config") {
            const body = bodyOrOptions as ConfigSyncBody;
            return await mutations.runStateMutation(
                () => postControl(path, body),
                { source: "control", ...maybeOptions },
            ).catch(() => null);
        }

        const options = (bodyOrOptions as SimulationMutationOptions | undefined) ?? {};
        return await mutations.runStateMutation(
            () => postControl(path),
            { source: "control", ...options },
        ).catch(() => null);
    }

    return {
        paintCell,
        resolveDirectGestureTargetState,
        toggleCell,
        sendControl,
        runSerialized: (task, options = {}) => mutations.runSerialized(task, options),
    };
}
