import { parseUiSession } from "./session.js";
import { isPlainObject } from "../runtime-validation.js";
import { cloneUiSession, createEmptyUiSession } from "../ui-session-state.js";
import type { UiDisclosureId, UiSessionState } from "../types/session.js";

export const UI_SESSION_STORAGE_VERSION = 3;

interface PersistedUiSessionV2 {
    version: typeof UI_SESSION_STORAGE_VERSION;
    session: UiSessionState;
}

export function parseStoredUiSession(
    value: unknown,
    {
        disclosureIds,
        defaultTilingFamily,
    }: {
        disclosureIds: readonly UiDisclosureId[];
        defaultTilingFamily: string;
    },
): UiSessionState {
    if (!isPlainObject(value) || value.version !== UI_SESSION_STORAGE_VERSION) {
        return createEmptyUiSession(defaultTilingFamily);
    }

    return parseUiSession(value.session, {
        disclosureIds,
        defaultTilingFamily,
    });
}

export function serializeUiSession(
    session: UiSessionState,
    {
        disclosureIds,
        defaultTilingFamily,
    }: {
        disclosureIds: readonly UiDisclosureId[];
        defaultTilingFamily: string;
    },
): PersistedUiSessionV2 {
    return {
        version: UI_SESSION_STORAGE_VERSION,
        session: cloneUiSession(
            parseUiSession(session, {
                disclosureIds,
                defaultTilingFamily,
            }),
        ),
    };
}
