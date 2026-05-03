import type { AppActionSet } from "./types/actions.js";

function isTextInputTarget(target: EventTarget | null): boolean {
    return target instanceof Element
        && Boolean(target.closest("input, textarea, select, [contenteditable='true']"));
}

export function bindControlShortcuts(actions: AppActionSet, {
    documentNode = document,
    isTextInputTargetFn = isTextInputTarget,
}: {
    documentNode?: Document;
    isTextInputTargetFn?: (target: EventTarget | null) => boolean;
} = {}): void {
    documentNode.addEventListener("keydown", (event) => {
        if (isTextInputTargetFn(event.target)) {
            return;
        }

        const key = event.key.toLowerCase();
        const isCommand = event.ctrlKey || event.metaKey;

        if (isCommand && key === "z") {
            event.preventDefault();
            if (event.shiftKey) {
                void actions.redoEdit?.();
                return;
            }
            void actions.undoEdit?.();
            return;
        }

        if (isCommand && key === "y") {
            event.preventDefault();
            void actions.redoEdit?.();
            return;
        }

        if (key === "escape") {
            event.preventDefault();
            void actions.cancelEditorPreview?.();
            return;
        }

        if (key === "b") {
            actions.setEditorTool?.("brush");
            return;
        }
        if (key === "l") {
            actions.setEditorTool?.("line");
            return;
        }
        if (key === "r") {
            actions.setEditorTool?.("rectangle");
            return;
        }
        if (key === "f") {
            actions.setEditorTool?.("fill");
            return;
        }
        if (key === "e") {
            actions.setPaintState?.(0);
            return;
        }

        if (key === "1" || key === "2" || key === "3") {
            actions.setBrushSize?.(Number(key));
        }
    });
}
