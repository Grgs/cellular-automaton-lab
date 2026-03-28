import { BLOCKING_ACTIVITY_RESIZE_BOARD } from "./blocking-activity.js";
import type {
    BrowserClearTimeout,
    BrowserSetTimeout,
    BrowserTimerId,
    ViewportControllerDependencies,
    ViewportController,
    ViewportDimensions,
} from "./types/controller.js";

interface ViewportSyncOptions {
    includeConfig?: boolean;
    force?: boolean;
    preview?: boolean;
    previewApplied?: boolean;
    clearConfig?: boolean;
    delay?: number;
    path?: string;
    body?: Record<string, unknown>;
    desiredDimensions?: ViewportDimensions;
    blockingActivity?: Record<string, unknown> | null;
}

export function createViewportController({
    getCurrentDimensions,
    getViewportDimensions,
    collectConfig,
    applyPreview,
    sendControl,
    sameDimensions,
    setTimeoutFn = (callback, delay) => window.setTimeout(callback, delay),
    clearTimeoutFn = (timerId) => window.clearTimeout(timerId),
    createResizeObserver = (callback) => {
        if (typeof ResizeObserver === "undefined") {
            return null;
        }
        return new ResizeObserver(callback);
    },
    addWindowResizeListener = (listener) => {
        window.addEventListener("resize", listener);
        return () => window.removeEventListener("resize", listener);
    },
}: ViewportControllerDependencies & {
    setTimeoutFn?: BrowserSetTimeout;
    clearTimeoutFn?: BrowserClearTimeout;
    createResizeObserver?: (callback: ResizeObserverCallback) => ResizeObserver | null;
    addWindowResizeListener?: (listener: () => void) => (() => void) | null;
}): ViewportController {
    let viewportSyncTimer: BrowserTimerId | null = null;
    let pendingViewportDimensions: ViewportDimensions | null = null;
    let resizeObserver: ResizeObserver | null = null;
    let removeWindowResizeListener: (() => void) | null = null;
    let suppressAutoSyncUntil = 0;
    let lastObservedViewportDimensions: ViewportDimensions | null = null;

    function isAutoSyncSuppressed(): boolean {
        return Date.now() < suppressAutoSyncUntil;
    }

    function buildRequestBody(
        options: ViewportSyncOptions = {},
        desiredDimensions = getViewportDimensions(),
    ): Record<string, unknown> {
        const { includeConfig = false, body = {} } = options;
        const topologySpec = {
            width: desiredDimensions.width,
            height: desiredDimensions.height,
        };
        return includeConfig
            ? {
                ...collectConfig(),
                ...body,
                topology_spec: {
                    ...topologySpec,
                    ...((body && typeof body === "object" && body.topology_spec) || {}),
                },
            }
            : {
                ...body,
                topology_spec: {
                    ...topologySpec,
                    ...((body && typeof body === "object" && body.topology_spec) || {}),
                },
            };
    }

    async function syncDesiredDimensions(
        desiredDimensions: ViewportDimensions,
        options: ViewportSyncOptions = {},
    ): Promise<boolean> {
        if (!options.force && isAutoSyncSuppressed()) {
            return false;
        }

        if (pendingViewportDimensions && sameDimensions(desiredDimensions, pendingViewportDimensions)) {
            return false;
        }

        if (!options.force && !options.previewApplied && sameDimensions(desiredDimensions, getCurrentDimensions())) {
            return false;
        }

        pendingViewportDimensions = desiredDimensions;
        try {
            await sendControl(
                options.path ?? "/api/config",
                buildRequestBody(options, desiredDimensions),
                {
                    clearConfig: Boolean(options.clearConfig),
                    blockingActivity: options.blockingActivity ?? BLOCKING_ACTIVITY_RESIZE_BOARD,
                },
            );
            return true;
        } finally {
            pendingViewportDimensions = null;
        }
    }

    async function sync(options: ViewportSyncOptions = {}): Promise<boolean> {
        return syncDesiredDimensions(getViewportDimensions(), options);
    }

    function schedule(options: ViewportSyncOptions = {}): boolean {
        if (!options.force && isAutoSyncSuppressed()) {
            return false;
        }

        const desiredDimensions = options.desiredDimensions ?? getViewportDimensions();
        if (pendingViewportDimensions && sameDimensions(desiredDimensions, pendingViewportDimensions)) {
            return false;
        }
        if (!options.force && sameDimensions(desiredDimensions, getCurrentDimensions())) {
            return false;
        }

        if (viewportSyncTimer !== null) {
            clearTimeoutFn(viewportSyncTimer);
        }

        if (options.preview !== false) {
            applyPreview(desiredDimensions);
        }

        viewportSyncTimer = setTimeoutFn(() => {
            viewportSyncTimer = null;
            void syncDesiredDimensions(
                desiredDimensions,
                options.preview === false ? options : { ...options, previewApplied: true }
            );
        }, options.delay ?? 120);
        return true;
    }

    function flush(options: ViewportSyncOptions = {}): Promise<boolean> {
        if (!options.force && isAutoSyncSuppressed()) {
            return Promise.resolve(false);
        }

        const desiredDimensions = options.desiredDimensions ?? getViewportDimensions();
        if (viewportSyncTimer !== null) {
            clearTimeoutFn(viewportSyncTimer);
            viewportSyncTimer = null;
        }

        if (options.preview !== false) {
            applyPreview(desiredDimensions);
        }

        return syncDesiredDimensions(
            desiredDimensions,
            options.preview === false ? options : { ...options, previewApplied: true },
        );
    }

    function suppressAutoSync(durationMs = 400): void {
        suppressAutoSyncUntil = Date.now() + durationMs;
        if (viewportSyncTimer !== null) {
            clearTimeoutFn(viewportSyncTimer);
            viewportSyncTimer = null;
        }
    }

    function install(viewportElement: HTMLElement | null): void {
        lastObservedViewportDimensions = getViewportDimensions();
        const onResize = () => {
            const desiredDimensions = getViewportDimensions();
            if (
                lastObservedViewportDimensions
                && sameDimensions(desiredDimensions, lastObservedViewportDimensions)
            ) {
                return;
            }
            lastObservedViewportDimensions = desiredDimensions;
            schedule({ desiredDimensions });
        };

        resizeObserver = createResizeObserver(onResize);
        if (resizeObserver && viewportElement) {
            resizeObserver.observe(viewportElement);
        }
        removeWindowResizeListener = addWindowResizeListener(onResize);
    }

    function dispose(): void {
        if (viewportSyncTimer !== null) {
            clearTimeoutFn(viewportSyncTimer);
            viewportSyncTimer = null;
        }
        if (resizeObserver && typeof resizeObserver.disconnect === "function") {
            resizeObserver.disconnect();
        }
        if (typeof removeWindowResizeListener === "function") {
            removeWindowResizeListener();
            removeWindowResizeListener = null;
        }
    }

    return {
        buildRequestBody,
        sync,
        schedule,
        flush,
        suppressAutoSync,
        install,
        dispose,
    };
}
