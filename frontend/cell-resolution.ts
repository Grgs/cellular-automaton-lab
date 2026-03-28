import type { GridView } from "./types/controller.js";
import type { CellIdentifier } from "./types/domain.js";
import type { AppState } from "./types/state.js";

export function createSurfaceCellResolver({
    state,
    gridView,
}: {
    state: AppState;
    gridView: GridView;
}): (event: Event) => CellIdentifier | null {
    return (event: Event) => {
        if (typeof gridView.getCellFromPointerEvent !== "function") {
            return null;
        }
        const resolvedCell = gridView.getCellFromPointerEvent(event);
        if (!resolvedCell || typeof resolvedCell.id !== "string" || resolvedCell.id.length === 0) {
            return null;
        }
        return state.topologyIndex?.byId?.get(resolvedCell.id) ?? resolvedCell;
    };
}
