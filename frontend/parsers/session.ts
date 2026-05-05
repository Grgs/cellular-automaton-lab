import { DEFAULT_TOPOLOGY_SPEC } from "../state/constants.js";
import { isPlainObject } from "../runtime-validation.js";
import { defaultCellSizeForTilingFamily } from "../state/sizing-state.js";
import { parseBrushSize, parseEditorTool } from "./editor.js";
import { parseCellSizeByTilingFamily, parsePatchDepthByTilingFamily } from "./sizing.js";
import { createEmptyUiSession } from "../ui-session-state.js";
import type { UiDisclosureId, UiSessionState } from "../types/session.js";

function parsePaintStatesByRule(value: unknown): Record<string, number> {
    if (!isPlainObject(value)) {
        return {};
    }

    return Object.fromEntries(
        Object.entries(value)
            .filter(([ruleName]) => typeof ruleName === "string" && ruleName.length > 0)
            .map(([ruleName, rawState]) => [ruleName, Number(rawState)])
            .filter(([, state]) => Number.isInteger(state)),
    );
}

function parseDisclosureStates(
    value: unknown,
    disclosureIds: readonly UiDisclosureId[],
): Partial<Record<UiDisclosureId, boolean>> {
    if (!isPlainObject(value)) {
        return {};
    }

    return Object.fromEntries(disclosureIds.map((id) => [id, Boolean(value[id])])) as Partial<
        Record<UiDisclosureId, boolean>
    >;
}

export function parseUiSession(
    value: unknown,
    {
        disclosureIds,
        defaultTilingFamily = DEFAULT_TOPOLOGY_SPEC.tiling_family,
    }: {
        disclosureIds: readonly UiDisclosureId[];
        defaultTilingFamily?: string;
    },
): UiSessionState {
    if (!isPlainObject(value)) {
        return createEmptyUiSession(defaultTilingFamily);
    }

    const session = createEmptyUiSession(defaultTilingFamily);
    session.unsafeSizingEnabled = Boolean(value.unsafeSizingEnabled);
    session.tileColorsEnabled = value.tileColorsEnabled !== false;
    if (value.cellSizeByTilingFamily !== null && value.cellSizeByTilingFamily !== undefined) {
        session.cellSizeByTilingFamily = parseCellSizeByTilingFamily(value.cellSizeByTilingFamily, {
            unsafe: session.unsafeSizingEnabled,
        });
    } else if (value.cellSize !== null && value.cellSize !== undefined) {
        session.cellSizeByTilingFamily = {
            [defaultTilingFamily]:
                parseCellSizeByTilingFamily(
                    {
                        [defaultTilingFamily]: value.cellSize,
                    },
                    {
                        unsafe: session.unsafeSizingEnabled,
                    },
                )[defaultTilingFamily] ?? defaultCellSizeForTilingFamily(defaultTilingFamily),
        };
    }
    if (value.editorTool !== null && value.editorTool !== undefined) {
        session.editorTool = parseEditorTool(value.editorTool);
    }
    if (value.brushSize !== null && value.brushSize !== undefined) {
        session.brushSize = parseBrushSize(value.brushSize);
    }
    if (value.drawerOpen !== null && value.drawerOpen !== undefined) {
        session.drawerOpen = Boolean(value.drawerOpen);
    }
    session.paintStatesByRule = parsePaintStatesByRule(value.paintStatesByRule);
    session.patchDepthByTilingFamily = parsePatchDepthByTilingFamily(
        value.patchDepthByTilingFamily,
        {
            unsafe: session.unsafeSizingEnabled,
        },
    );
    session.disclosures = parseDisclosureStates(value.disclosures, disclosureIds);
    session.cellSize =
        session.cellSizeByTilingFamily[defaultTilingFamily] ??
        defaultCellSizeForTilingFamily(defaultTilingFamily);
    return session;
}
