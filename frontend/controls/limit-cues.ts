import type { BrowserClearTimeout, BrowserSetTimeout, BrowserTimerId } from "../types/controller.js";
import type { AsyncControlResult } from "./binding-primitives.js";

const LIMIT_CUE_DURATION_MS = 1800;

function parseNumericConstraint(value: string): number | null {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
}

function rangeLimitMessage(input: HTMLInputElement | null): string {
    if (!input) {
        return "";
    }
    const rawValue = String(input.value ?? "").trim();
    if (rawValue === "") {
        return "";
    }
    const value = Number(rawValue);
    if (!Number.isFinite(value)) {
        return "";
    }
    const minimum = parseNumericConstraint(input.min);
    const maximum = parseNumericConstraint(input.max);
    if (minimum !== null && value < minimum) {
        return maximum !== null
            ? `Allowed: ${minimum}-${maximum}.`
            : `Minimum: ${minimum}.`;
    }
    if (maximum !== null && value > maximum) {
        return minimum !== null
            ? `Allowed: ${minimum}-${maximum}.`
            : `Maximum: ${maximum}.`;
    }
    return "";
}

function stepBoundaryLimitMessage(
    input: HTMLInputElement | null,
    direction: "up" | "down" | null,
): string {
    if (!input || (direction !== "up" && direction !== "down")) {
        return "";
    }
    const rawValue = String(input.value ?? "").trim();
    if (rawValue === "") {
        return "";
    }
    const value = Number(rawValue);
    if (!Number.isFinite(value)) {
        return "";
    }
    const minimum = parseNumericConstraint(input.min);
    const maximum = parseNumericConstraint(input.max);
    if (direction === "up" && maximum !== null && value >= maximum) {
        return minimum !== null
            ? `Allowed: ${minimum}-${maximum}.`
            : `Maximum: ${maximum}.`;
    }
    if (direction === "down" && minimum !== null && value <= minimum) {
        return maximum !== null
            ? `Allowed: ${minimum}-${maximum}.`
            : `Minimum: ${minimum}.`;
    }
    return "";
}

function stepDirectionFromPointer(
    input: HTMLInputElement | null,
    event: PointerEvent,
): "up" | "down" | null {
    if (!input || typeof input.getBoundingClientRect !== "function") {
        return null;
    }
    const rect = input.getBoundingClientRect();
    const spinnerWidth = Math.min(24, Math.max(16, rect.width * 0.3));
    if (event.clientX < rect.right - spinnerWidth) {
        return null;
    }
    return event.clientY <= rect.top + rect.height / 2 ? "up" : "down";
}

function ensureLimitCue(field: HTMLElement | null): HTMLSpanElement | null {
    if (!field) {
        return null;
    }
    let cue = field.querySelector(".top-control-limit-cue") as HTMLSpanElement | null;
    if (cue) {
        return cue;
    }
    cue = document.createElement("span");
    cue.className = "top-control-limit-cue";
    cue.hidden = true;
    cue.setAttribute("aria-live", "polite");
    field.appendChild(cue);
    return cue;
}

function clearLimitCue(
    field: HTMLElement | null,
    input: HTMLInputElement | null,
    cueTimeouts: WeakMap<HTMLInputElement, BrowserTimerId>,
    clearTimeoutFn: BrowserClearTimeout,
): void {
    if (!field || !input) {
        return;
    }
    const timeoutId = cueTimeouts.get(input);
    if (timeoutId !== undefined) {
        clearTimeoutFn(timeoutId);
        cueTimeouts.delete(input);
    }
    field.classList.remove("has-limit-cue");
    delete field.dataset.limitCueText;
    input.classList.remove("is-limit-cue");
    input.removeAttribute("aria-invalid");
    const cue = field.querySelector(".top-control-limit-cue") as HTMLSpanElement | null;
    if (cue) {
        cue.hidden = true;
        cue.textContent = "";
    }
}

function showLimitCue(
    field: HTMLElement | null,
    input: HTMLInputElement | null,
    message: string,
    cueTimeouts: WeakMap<HTMLInputElement, BrowserTimerId>,
    setTimeoutFn: BrowserSetTimeout,
    clearTimeoutFn: BrowserClearTimeout,
): void {
    if (!field || !input || !message) {
        return;
    }
    clearLimitCue(field, input, cueTimeouts, clearTimeoutFn);
    const cue = ensureLimitCue(field);
    field.classList.add("has-limit-cue");
    field.dataset.limitCueText = message;
    input.classList.add("is-limit-cue");
    input.setAttribute("aria-invalid", "true");
    if (cue) {
        cue.hidden = false;
        cue.textContent = message;
    }
    const timeoutId = setTimeoutFn(() => {
        clearLimitCue(field, input, cueTimeouts, clearTimeoutFn);
    }, LIMIT_CUE_DURATION_MS);
    cueTimeouts.set(input, timeoutId);
}

export function bindConstrainedNumericControl({
    input,
    field,
    onInput,
    onChange,
    cueTimeouts,
    setTimeoutFn,
    clearTimeoutFn,
}: {
    input: HTMLInputElement | null;
    field: HTMLElement | null;
    onInput?: (value: number) => AsyncControlResult;
    onChange?: (value: number) => AsyncControlResult;
    cueTimeouts: WeakMap<HTMLInputElement, BrowserTimerId>;
    setTimeoutFn: BrowserSetTimeout;
    clearTimeoutFn: BrowserClearTimeout;
}): void {
    if (!input) {
        return;
    }
    if (onInput) {
        input.addEventListener("input", () => {
            const message = rangeLimitMessage(input);
            onInput(Number(input.value));
            if (message) {
                showLimitCue(field, input, message, cueTimeouts, setTimeoutFn, clearTimeoutFn);
                return;
            }
            clearLimitCue(field, input, cueTimeouts, clearTimeoutFn);
        });
    }
    if (onChange) {
        input.addEventListener("change", () => {
            onChange(Number(input.value));
        });
    }
    input.addEventListener("keydown", (event) => {
        const direction = event.key === "ArrowUp"
            ? "up"
            : (event.key === "ArrowDown" ? "down" : null);
        if (!direction) {
            return;
        }
        const message = stepBoundaryLimitMessage(input, direction);
        if (!message) {
            return;
        }
        showLimitCue(field, input, message, cueTimeouts, setTimeoutFn, clearTimeoutFn);
    });
    input.addEventListener("pointerdown", (event) => {
        const direction = stepDirectionFromPointer(input, event);
        if (!direction) {
            return;
        }
        const message = stepBoundaryLimitMessage(input, direction);
        if (!message) {
            return;
        }
        showLimitCue(field, input, message, cueTimeouts, setTimeoutFn, clearTimeoutFn);
    });
}
