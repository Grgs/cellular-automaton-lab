import {
    applyThemePreference,
    currentTheme,
    readThemePreference,
    type ThemePreference,
} from "../theme.js";
import { resetStoredCompareWorkspaceLayout } from "../compare/compare-workspace-layout.js";
import type { CompareMenuCommand } from "../compare/compare-menu-command.js";

interface ShellMenuOptions {
    menu?: HTMLElement | null;
    menuButton?: HTMLButtonElement | null;
    menuPanel?: HTMLElement | null;
    compareButton?: HTMLButtonElement | null;
    labButton?: HTMLButtonElement | null;
    wallTrigger?: HTMLButtonElement | null;
    labTrigger?: HTMLButtonElement | null;
    executeCompareMenuCommand?: (command: CompareMenuCommand) => void | Promise<void>;
    preferencesButton?: HTMLButtonElement | null;
    preferencesDialog?: HTMLDialogElement | null;
    preferencesThemeInputs?: readonly HTMLInputElement[];
    preferencesStatus?: HTMLElement | null;
    preferencesResetCompareLayoutButton?: HTMLButtonElement | null;
    preferencesCompareLayoutStatus?: HTMLElement | null;
    preferencesCloseButton?: HTMLButtonElement | null;
    root?: HTMLElement;
    documentNode?: Document;
    storage?: Storage;
    compareLayoutEventTarget?: EventTarget;
    media?: ((query: string) => MediaQueryList) | undefined;
}

/** Wire global navigation, the controlled app-menu disclosure, and Preferences. */
export function wireShellMenu({
    menu = document.getElementById("shell-menu"),
    menuButton = document.getElementById("shell-menu-toggle") as HTMLButtonElement | null,
    menuPanel = document.getElementById("shell-menu-panel"),
    compareButton = document.getElementById("shell-menu-compare") as HTMLButtonElement | null,
    labButton = document.getElementById("shell-menu-lab") as HTMLButtonElement | null,
    wallTrigger = document.getElementById("wall-view-btn") as HTMLButtonElement | null,
    labTrigger = document.getElementById("open-lab-btn") as HTMLButtonElement | null,
    executeCompareMenuCommand,
    preferencesButton = document.getElementById(
        "shell-preferences-btn",
    ) as HTMLButtonElement | null,
    preferencesDialog = document.getElementById("shell-preferences") as HTMLDialogElement | null,
    preferencesThemeInputs = Array.from(
        document.querySelectorAll<HTMLInputElement>('input[name="shell-theme-preference"]'),
    ),
    preferencesStatus = document.getElementById("shell-preferences-status"),
    preferencesResetCompareLayoutButton = document.getElementById(
        "shell-preferences-reset-compare-layout",
    ) as HTMLButtonElement | null,
    preferencesCompareLayoutStatus = document.getElementById(
        "shell-preferences-compare-layout-status",
    ),
    preferencesCloseButton = document.getElementById(
        "shell-preferences-close",
    ) as HTMLButtonElement | null,
    root = document.documentElement,
    documentNode = document,
    storage = window.localStorage,
    compareLayoutEventTarget = window,
    media = typeof window !== "undefined" ? window.matchMedia?.bind(window) : undefined,
}: ShellMenuOptions = {}): () => void {
    let menuOpen = false;
    const shellButton = (id: string): HTMLButtonElement | null =>
        documentNode.getElementById(id) as HTMLButtonElement | null;
    const labActions = documentNode.getElementById("shell-menu-lab-actions");
    const compareActions = documentNode.getElementById("shell-menu-compare-actions");

    const setMenuOpen = (open: boolean, { restoreFocus = false } = {}): void => {
        menuOpen = open;
        if (menuPanel) {
            menuPanel.hidden = !open;
        }
        menuButton?.setAttribute("aria-expanded", open ? "true" : "false");
        menu?.classList.toggle("is-open", open);
        if (!open && restoreFocus) {
            menuButton?.focus();
        }
    };
    const openPreferences = (): void => {
        setMenuOpen(false);
        if (!preferencesDialog) {
            return;
        }
        if (typeof preferencesDialog.showModal === "function") {
            if (!preferencesDialog.open) {
                preferencesDialog.showModal();
            }
        } else {
            preferencesDialog.hidden = false;
        }
        syncPreferences();
    };
    const closePreferences = (): void => {
        if (!preferencesDialog) {
            return;
        }
        if (typeof preferencesDialog.close === "function") {
            preferencesDialog.close();
        } else {
            preferencesDialog.hidden = true;
            menuButton?.focus();
        }
    };
    const navigate = (trigger: HTMLButtonElement | null | undefined): void => {
        setMenuOpen(false, { restoreFocus: true });
        trigger?.click();
    };
    const perform = (action: () => void): (() => void) => {
        return () => {
            setMenuOpen(false);
            action();
        };
    };
    const performCompare = (command: CompareMenuCommand): (() => void) => {
        return perform(() => {
            void executeCompareMenuCommand?.(command);
        });
    };
    const showLabSection = (sectionId: string): void => {
        const drawer = documentNode.getElementById("control-drawer");
        if (drawer && drawer.dataset.open !== "true") {
            shellButton("drawer-toggle-btn")?.click();
        }
        documentNode.querySelector<HTMLAnchorElement>(`a[href="#${sectionId}"]`)?.click();
    };
    const syncContext = (): void => {
        const route = root.dataset.workspaceRoute;
        if (labActions) {
            labActions.hidden = route !== "lab";
        }
        if (compareActions) {
            compareActions.hidden = route !== "wall";
        }
    };
    const syncPreferences = (): void => {
        const preference = readThemePreference({ storage });
        for (const input of preferencesThemeInputs) {
            input.checked = input.value === preference;
        }
        if (preferencesStatus) {
            const theme = currentTheme(root);
            preferencesStatus.textContent =
                preference === "system"
                    ? `Following system preference (currently ${theme} mode).`
                    : `Using ${theme} mode.`;
        }
    };
    const onMenuToggle = (): void => setMenuOpen(!menuOpen);
    const onCompare = (): void => navigate(wallTrigger);
    const onLab = (): void => navigate(labTrigger);
    const onLabControls = perform(() => shellButton("drawer-toggle-btn")?.click());
    const onLabRule = perform(() => showLabSection("sim-section"));
    const onLabImport = perform(() => shellButton("import-pattern-btn")?.click());
    const onLabExport = perform(() => shellButton("export-pattern-btn")?.click());
    const onLabCopy = perform(() => shellButton("copy-pattern-btn")?.click());
    const onLabPaste = perform(() => shellButton("paste-pattern-btn")?.click());
    const onLabShare = perform(() => shellButton("share-link-btn")?.click());
    const onLabPreset = perform(() => shellButton("preset-seed-btn")?.click());
    const onCompareWall = performCompare({ type: "open-config", tab: "tilings" });
    const onCompareRule = performCompare({ type: "focus-rule" });
    const onCompareSaved = performCompare({ type: "open-config", tab: "saved" });
    const onCompareShare = performCompare({ type: "copy-run-link" });
    const onCompareHelp = performCompare({ type: "open-config", tab: "help" });
    const onPreferences = (): void => openPreferences();
    const onThemePreference = (event: Event): void => {
        const input = event.currentTarget;
        if (!(input instanceof HTMLInputElement) || !input.checked) {
            return;
        }
        applyThemePreference(input.value as ThemePreference, { root, storage, media });
        syncPreferences();
    };
    const onResetCompareLayout = (): void => {
        resetStoredCompareWorkspaceLayout({
            storage,
            eventTarget: compareLayoutEventTarget,
        });
        if (preferencesCompareLayoutStatus) {
            preferencesCompareLayoutStatus.textContent = "Compare layout reset.";
        }
    };
    const onClose = (): void => closePreferences();
    const onPreferencesClosed = (): void => menuButton?.focus();
    const onDocumentPointerDown = (event: PointerEvent): void => {
        if (menuOpen && menu && event.target instanceof Node && !menu.contains(event.target)) {
            setMenuOpen(false);
        }
    };
    const onDocumentKeyDown = (event: KeyboardEvent): void => {
        if (menuOpen && event.key === "Escape") {
            event.preventDefault();
            event.stopPropagation();
            setMenuOpen(false, { restoreFocus: true });
        }
    };

    menuButton?.addEventListener("click", onMenuToggle);
    compareButton?.addEventListener("click", onCompare);
    labButton?.addEventListener("click", onLab);
    shellButton("shell-menu-lab-controls")?.addEventListener("click", onLabControls);
    shellButton("shell-menu-lab-rule")?.addEventListener("click", onLabRule);
    shellButton("shell-menu-lab-import")?.addEventListener("click", onLabImport);
    shellButton("shell-menu-lab-export")?.addEventListener("click", onLabExport);
    shellButton("shell-menu-lab-copy")?.addEventListener("click", onLabCopy);
    shellButton("shell-menu-lab-paste")?.addEventListener("click", onLabPaste);
    shellButton("shell-menu-lab-share")?.addEventListener("click", onLabShare);
    shellButton("shell-menu-lab-preset")?.addEventListener("click", onLabPreset);
    shellButton("shell-menu-compare-wall")?.addEventListener("click", onCompareWall);
    shellButton("shell-menu-compare-rule")?.addEventListener("click", onCompareRule);
    shellButton("shell-menu-compare-saved")?.addEventListener("click", onCompareSaved);
    shellButton("shell-menu-compare-share")?.addEventListener("click", onCompareShare);
    shellButton("shell-menu-compare-help")?.addEventListener("click", onCompareHelp);
    preferencesButton?.addEventListener("click", onPreferences);
    preferencesThemeInputs.forEach((input) => input.addEventListener("change", onThemePreference));
    preferencesResetCompareLayoutButton?.addEventListener("click", onResetCompareLayout);
    preferencesCloseButton?.addEventListener("click", onClose);
    preferencesDialog?.addEventListener("close", onPreferencesClosed);
    documentNode.addEventListener("pointerdown", onDocumentPointerDown);
    documentNode.addEventListener("keydown", onDocumentKeyDown, true);

    const observer = new MutationObserver(() => {
        syncPreferences();
        syncContext();
    });
    observer.observe(root, {
        attributes: true,
        attributeFilter: ["data-theme", "data-workspace-route"],
    });
    const systemQuery = media?.("(prefers-color-scheme: dark)") ?? null;
    const onOsChange = (): void => {
        if (readThemePreference({ storage }) === "system") {
            applyThemePreference("system", { root, storage, media });
            syncPreferences();
        }
    };
    systemQuery?.addEventListener?.("change", onOsChange);
    setMenuOpen(false);
    syncPreferences();
    syncContext();

    return () => {
        menuButton?.removeEventListener("click", onMenuToggle);
        compareButton?.removeEventListener("click", onCompare);
        labButton?.removeEventListener("click", onLab);
        shellButton("shell-menu-lab-controls")?.removeEventListener("click", onLabControls);
        shellButton("shell-menu-lab-rule")?.removeEventListener("click", onLabRule);
        shellButton("shell-menu-lab-import")?.removeEventListener("click", onLabImport);
        shellButton("shell-menu-lab-export")?.removeEventListener("click", onLabExport);
        shellButton("shell-menu-lab-copy")?.removeEventListener("click", onLabCopy);
        shellButton("shell-menu-lab-paste")?.removeEventListener("click", onLabPaste);
        shellButton("shell-menu-lab-share")?.removeEventListener("click", onLabShare);
        shellButton("shell-menu-lab-preset")?.removeEventListener("click", onLabPreset);
        shellButton("shell-menu-compare-wall")?.removeEventListener("click", onCompareWall);
        shellButton("shell-menu-compare-rule")?.removeEventListener("click", onCompareRule);
        shellButton("shell-menu-compare-saved")?.removeEventListener("click", onCompareSaved);
        shellButton("shell-menu-compare-share")?.removeEventListener("click", onCompareShare);
        shellButton("shell-menu-compare-help")?.removeEventListener("click", onCompareHelp);
        preferencesButton?.removeEventListener("click", onPreferences);
        preferencesThemeInputs.forEach((input) =>
            input.removeEventListener("change", onThemePreference),
        );
        preferencesResetCompareLayoutButton?.removeEventListener("click", onResetCompareLayout);
        preferencesCloseButton?.removeEventListener("click", onClose);
        preferencesDialog?.removeEventListener("close", onPreferencesClosed);
        documentNode.removeEventListener("pointerdown", onDocumentPointerDown);
        documentNode.removeEventListener("keydown", onDocumentKeyDown, true);
        observer.disconnect();
        systemQuery?.removeEventListener?.("change", onOsChange);
    };
}
