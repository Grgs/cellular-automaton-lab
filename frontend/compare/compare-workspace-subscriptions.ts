import type { CompareWorkspaceStore } from "./compare-workspace-store.js";

/**
 * One-level structural equality. Primitives compare with `Object.is`; arrays
 * compare length then elements with `Object.is`; plain objects compare their
 * own enumerable keys' values with `Object.is`. Deliberately shallow: selector
 * outputs are flat tuples/records of the store fields a view depends on, so a
 * one-level compare is enough to tell "my slice changed" from "some other
 * slice changed". Nested changes must surface as a changed reference or a
 * changed top-level field, which the immutable store already guarantees.
 */
export function shallowEqual(a: unknown, b: unknown): boolean {
    if (Object.is(a, b)) {
        return true;
    }
    if (Array.isArray(a) && Array.isArray(b)) {
        if (a.length !== b.length) {
            return false;
        }
        return a.every((value, index) => Object.is(value, b[index]));
    }
    if (typeof a === "object" && a !== null && typeof b === "object" && b !== null) {
        const aKeys = Object.keys(a as Record<string, unknown>);
        const bKeys = Object.keys(b as Record<string, unknown>);
        if (aKeys.length !== bKeys.length) {
            return false;
        }
        return aKeys.every(
            (key) =>
                Object.prototype.hasOwnProperty.call(b, key) &&
                Object.is((a as Record<string, unknown>)[key], (b as Record<string, unknown>)[key]),
        );
    }
    return false;
}

/**
 * Subscribe to a derived slice of the workspace store, invoking `listener`
 * only when that slice changes by `isEqual`. This is what keeps frame-index
 * churn from re-rendering unrelated views: a selector that omits
 * `playback.frameIndex` never fires while playback advances the clock, even
 * though every tick publishes a new frozen state.
 *
 * The listener is not called on subscribe (the caller does the initial render);
 * `previous` on the first firing is the slice value captured at subscription.
 * Returns the store's unsubscribe handle.
 */
export function subscribeSelector<T>(
    store: CompareWorkspaceStore,
    selector: (state: ReturnType<CompareWorkspaceStore["getState"]>) => T,
    listener: (value: T, previous: T) => void,
    isEqual: (a: T, b: T) => boolean = shallowEqual,
): () => void {
    let current = selector(store.getState());
    return store.subscribe((state) => {
        const next = selector(state);
        if (isEqual(next, current)) {
            return;
        }
        const previous = current;
        current = next;
        listener(next, previous);
    });
}
