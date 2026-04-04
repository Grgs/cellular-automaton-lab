import type { SimulationSnapshot } from "../types/domain.js";

type MaybePromise<TResult> = TResult | Promise<TResult>;
export type AsyncControlResult = MaybePromise<boolean | void | null | SimulationSnapshot>;
export type AsyncButtonResult = MaybePromise<boolean | void | null | SimulationSnapshot>;

export function bindInputControl<TValue>(
    element: HTMLElement | null,
    eventName: "input" | "change",
    valueFactory: () => TValue,
    handler: ((value: TValue) => AsyncControlResult) | undefined,
): void {
    if (!element || !handler) {
        return;
    }
    element.addEventListener(eventName, () => {
        void handler(valueFactory());
    });
}

export function bindButtonControl(
    element: HTMLButtonElement | null,
    handler: (() => AsyncButtonResult) | undefined,
): void {
    if (!element || !handler) {
        return;
    }
    element.addEventListener("click", () => {
        void handler();
    });
}

export function bindDelegatedControl(
    container: HTMLElement | null,
    selector: string,
    handler: ((button: HTMLElement) => AsyncControlResult) | undefined,
): void {
    if (!container || !handler) {
        return;
    }
    container.addEventListener("click", (event) => {
        if (!(event.target instanceof Element)) {
            return;
        }
        const button = event.target.closest(selector);
        if (!(button instanceof HTMLElement)) {
            return;
        }
        void handler(button);
    });
}
