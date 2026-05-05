import type { BrowserClearTimeout, BrowserSetTimeout } from "../types/controller.js";

export interface ControlBindingTimerOptions {
    setTimeoutFn?: BrowserSetTimeout;
    clearTimeoutFn?: BrowserClearTimeout;
}
