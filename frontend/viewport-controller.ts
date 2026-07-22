import { BLOCKING_ACTIVITY_RESIZE_BOARD } from "./blocking-activity.js";
import type {
    BrowserClearTimeout,
    BrowserSetTimeout,
    BrowserTimerId,
    ConfigSyncBody,
    ViewportControllerDependencies,
    ViewportController,
    ViewportDimensions,
    ViewportSyncOptions,
} from "./types/controller.js";

export function createViewportController({
    getCurrentDimensions,
    getViewportDimensions,
    collectConfig,
    applyPreview,
    renderPresentation = () => {},
    isPointerGestureActive = () => false,
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
    unsafeSizeOverrideEnabled = () => false,
}: ViewportControllerDependencies & {
    setTimeoutFn?: BrowserSetTimeout;
    clearTimeoutFn?: BrowserClearTimeout;
    createResizeObserver?: (callback: ResizeObserverCallback) => ResizeObserver | null;
    addWindowResizeListener?: (listener: () => void) => (() => void) | null;
}): ViewportController {
    let viewportSyncTimer: BrowserTimerId | null = null;
    let presentationResizeTimer: BrowserTimerId | null = null;
    let pendingViewportDimensions: ViewportDimensions | null = null;
    let resizeObserver: ResizeObserver | null = null;
    let removeWindowResizeListener: (() => void) | null = null;
    let suppressAutoSyncUntil = 0;
    let lastObservedViewportDimensions: ViewportDimensions | null = null;
    let lastPresentationViewportDimensions: ViewportDimensions | null = null;

    function presentationViewportDimensions(viewportElement: HTMLElement): ViewportDimensions {
        return {
            width: Math.max(0, viewportElement.clientWidth),
            height: Math.max(0, viewportElement.clientHeight),
        };
    }

    function schedulePresentationResize(): void {
        if (presentationResizeTimer !== null) {
            clearTimeoutFn(presentationResizeTimer);
        }
        presentationResizeTimer = setTimeoutFn(() => {
            presentationResizeTimer = null;
            if (isPointerGestureActive()) {
                schedulePresentationResize();
                return;
            }
            renderPresentation();
        }, 32);
    }

    function isAutoSyncSuppressed(): boolean {
        return Date.now() < suppressAutoSyncUntil;
    }

    function buildRequestBody(
        options: ViewportSyncOptions = {},
        desiredDimensions = getViewportDimensions(),
    ): ConfigSyncBody {
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
                      ...(unsafeSizeOverrideEnabled() ? { unsafe_size_override: true } : {}),
                      ...(body.topology_spec ?? {}),
                  },
              }
            : {
                  ...body,
                  topology_spec: {
                      ...topologySpec,
                      ...(unsafeSizeOverrideEnabled() ? { unsafe_size_override: true } : {}),
                      ...(body.topology_spec ?? {}),
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

        if (
            pendingViewportDimensions &&
            sameDimensions(desiredDimensions, pendingViewportDimensions)
        ) {
            return false;
        }

        if (
            !options.force &&
            !options.previewApplied &&
            sameDimensions(desiredDimensions, getCurrentDimensions())
        ) {
            return false;
        }

        pendingViewportDimensions = desiredDimensions;
        try {
            await sendControl("/api/config", buildRequestBody(options, desiredDimensions), {
                blockingActivity: options.blockingActivity ?? BLOCKING_ACTIVITY_RESIZE_BOARD,
            });
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
        if (
            pendingViewportDimensions &&
            sameDimensions(desiredDimensions, pendingViewportDimensions)
        ) {
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
                options.preview === false ? options : { ...options, previewApplied: true },
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
                lastObservedViewportDimensions &&
                sameDimensions(desiredDimensions, lastObservedViewportDimensions)
            ) {
                return;
            }
            lastObservedViewportDimensions = desiredDimensions;
            schedule({ desiredDimensions });
        };

        // Internal chrome changes (arming the editor, hiding the inspector when
        // a run starts) resize only the canvas presentation. Observe that box
        // separately from the window-only topology sync above, and never move
        // the canvas beneath an active pointer gesture.
        if (viewportElement) {
            lastPresentationViewportDimensions = presentationViewportDimensions(viewportElement);
            resizeObserver = createResizeObserver(() => {
                const dimensions = presentationViewportDimensions(viewportElement);
                if (sameDimensions(dimensions, lastPresentationViewportDimensions)) {
                    return;
                }
                lastPresentationViewportDimensions = dimensions;
                schedulePresentationResize();
            });
            resizeObserver?.observe(viewportElement);
        }
        removeWindowResizeListener = addWindowResizeListener(onResize);
    }

    function dispose(): void {
        if (viewportSyncTimer !== null) {
            clearTimeoutFn(viewportSyncTimer);
            viewportSyncTimer = null;
        }
        if (presentationResizeTimer !== null) {
            clearTimeoutFn(presentationResizeTimer);
            presentationResizeTimer = null;
        }
        resizeObserver?.disconnect();
        resizeObserver = null;
        if (typeof removeWindowResizeListener === "function") {
            removeWindowResizeListener();
            removeWindowResizeListener = null;
        }
    }

    return {
        sync,
        schedule,
        flush,
        suppressAutoSync,
        install,
        dispose,
    };
}
