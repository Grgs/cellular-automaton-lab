const INTERACTIVE_CHROME_SELECTOR = [
    "button",
    "input",
    "select",
    "textarea",
    "label",
    "summary",
    "a[href]",
    "[role='button']",
    "[role='link']",
    "[contenteditable='true']",
].join(", ");

export function eventTargetElement(event: Event): Element | null {
    return event.target instanceof Element ? event.target : null;
}

export function isInteractiveChromeClick(event: Event, container: HTMLElement | null): boolean {
    const target = eventTargetElement(event);
    if (!target || !container || !container.contains(target)) {
        return false;
    }
    return Boolean(target.closest(INTERACTIVE_CHROME_SELECTOR));
}
