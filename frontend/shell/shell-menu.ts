import {
    applyThemePreference,
    currentTheme,
    readThemePreference,
    type ThemePreference,
} from "../theme.js";
import { resetStoredCompareWorkspaceLayout } from "../compare/compare-workspace-layout.js";

interface ShellMenuOptions {
    menu?: HTMLElement | null;
    menuButton?: HTMLButtonElement | null;
    menuPanel?: HTMLElement | null;
    compareButton?: HTMLButtonElement | null;
    labButton?: HTMLButtonElement | null;
    wallTrigger?: HTMLButtonElement | null;
    labTrigger?: HTMLButtonElement | null;
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
    preferencesButton?.addEventListener("click", onPreferences);
    preferencesThemeInputs.forEach((input) => input.addEventListener("change", onThemePreference));
    preferencesResetCompareLayoutButton?.addEventListener("click", onResetCompareLayout);
    preferencesCloseButton?.addEventListener("click", onClose);
    preferencesDialog?.addEventListener("close", onPreferencesClosed);
    documentNode.addEventListener("pointerdown", onDocumentPointerDown);
    documentNode.addEventListener("keydown", onDocumentKeyDown, true);

    const observer = new MutationObserver(syncPreferences);
    observer.observe(root, { attributes: true, attributeFilter: ["data-theme"] });
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

    return () => {
        menuButton?.removeEventListener("click", onMenuToggle);
        compareButton?.removeEventListener("click", onCompare);
        labButton?.removeEventListener("click", onLab);
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
