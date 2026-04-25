import type { BlockingActivityConfig } from "./types/controller.js";

export const BLOCKING_ACTIVITY_DELAY_MS = 200;
export const BLOCKING_ACTIVITY_ESCALATE_MS = 1000;

const BOARD_ACTIVITY_HINT = "Dense tilings can take a moment.";
const PATTERN_ACTIVITY_HINT = "Large patterns can take a moment.";

function createBlockingActivity(
    kind: string,
    message: string,
    detail: string,
    {
    delayMs = BLOCKING_ACTIVITY_DELAY_MS,
    escalateAfterMs = BLOCKING_ACTIVITY_ESCALATE_MS,
}: {
    delayMs?: number;
    escalateAfterMs?: number;
} = {}): Readonly<Required<BlockingActivityConfig>> {
    return Object.freeze({
        kind,
        message,
        detail,
        delayMs,
        escalateAfterMs,
    }) as Readonly<Required<BlockingActivityConfig>>;
}

export const BLOCKING_ACTIVITY_BUILD_TILING = createBlockingActivity(
    "build-tiling",
    "Building tiling...",
    BOARD_ACTIVITY_HINT,
);

export const BLOCKING_ACTIVITY_RESET_BOARD = createBlockingActivity(
    "reset-board",
    "Resetting board...",
    BOARD_ACTIVITY_HINT,
);

export const BLOCKING_ACTIVITY_RESTORE_DEFAULTS = createBlockingActivity(
    "restore-defaults",
    "Restoring defaults and loading default board...",
    BOARD_ACTIVITY_HINT,
    {
        delayMs: 0,
    },
);

export const BLOCKING_ACTIVITY_RESIZE_BOARD = createBlockingActivity(
    "resize-board",
    "Resizing board...",
    BOARD_ACTIVITY_HINT,
);

export const BLOCKING_ACTIVITY_APPLY_PRESET = createBlockingActivity(
    "apply-preset",
    "Applying preset...",
    BOARD_ACTIVITY_HINT,
);

export const BLOCKING_ACTIVITY_LOAD_DEMO = createBlockingActivity(
    "load-demo",
    "Loading demo...",
    BOARD_ACTIVITY_HINT,
);

export const BLOCKING_ACTIVITY_IMPORT_PATTERN = createBlockingActivity(
    "import-pattern",
    "Importing pattern...",
    PATTERN_ACTIVITY_HINT,
);

export const BLOCKING_ACTIVITY_PASTE_PATTERN = createBlockingActivity(
    "paste-pattern",
    "Pasting pattern...",
    PATTERN_ACTIVITY_HINT,
);

export const BLOCKING_ACTIVITY_APPLY_SHARE_LINK = createBlockingActivity(
    "apply-share-link",
    "Loading shared board...",
    PATTERN_ACTIVITY_HINT,
);
