import { currentTheme, resetThemeToDefault, toggleTheme } from "../theme.js";

interface ShellMenuOptions {
    menu?: HTMLDetailsElement | null;
    compareButton?: HTMLButtonElement | null;
    labButton?: HTMLButtonElement | null;
    wallTrigger?: HTMLButtonElement | null;
    labTrigger?: HTMLButtonElement | null;
    preferencesButton?: HTMLButtonElement | null;
    preferencesDialog?: HTMLDialogElement | null;
    preferencesThemeButton?: HTMLButtonElement | null;
    preferencesSystemButton?: HTMLButtonElement | null;
    preferencesStatus?: HTMLElement | null;
    preferencesCloseButton?: HTMLButtonElement | null;
    root?: HTMLElement;
    storage?: Storage;
    media?: ((query: string) => MediaQueryList) | undefined;
}

function closeMenu(menu: HTMLDetailsElement | null | undefined): void {
    if (menu) {
        menu.open = false;
    }
}

/** Wire shell-only navigation and preferences without coupling them to either workspace. */
export function wireShellMenu({
    menu = document.getElementById("shell-menu") as HTMLDetailsElement | null,
    compareButton = document.getElementById("shell-menu-compare") as HTMLButtonElement | null,
    labButton = document.getElementById("shell-menu-lab") as HTMLButtonElement | null,
    wallTrigger = document.getElementById("wall-view-btn") as HTMLButtonElement | null,
    labTrigger = document.getElementById("open-lab-btn") as HTMLButtonElement | null,
    preferencesButton = document.getElementById(
        "shell-preferences-btn",
    ) as HTMLButtonElement | null,
    preferencesDialog = document.getElementById("shell-preferences") as HTMLDialogElement | null,
    preferencesThemeButton = document.getElementById(
        "shell-preferences-theme-btn",
    ) as HTMLButtonElement | null,
    preferencesSystemButton = document.getElementById(
        "shell-preferences-system-btn",
    ) as HTMLButtonElement | null,
    preferencesStatus = document.getElementById("shell-preferences-status"),
    preferencesCloseButton = document.getElementById(
        "shell-preferences-close",
    ) as HTMLButtonElement | null,
    root = document.documentElement,
    storage = window.localStorage,
    media = typeof window !== "undefined" ? window.matchMedia?.bind(window) : undefined,
}: ShellMenuOptions = {}): () => void {
    const openPreferences = (): void => {
        closeMenu(menu);
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
        }
    };
    const navigate = (trigger: HTMLButtonElement | null | undefined): void => {
        closeMenu(menu);
        trigger?.click();
    };
    const syncPreferences = (): void => {
        const theme = currentTheme(root);
        const nextTheme = theme === "dark" ? "light" : "dark";
        preferencesThemeButton?.replaceChildren(`Use ${nextTheme} mode`);
        if (preferencesStatus) {
            preferencesStatus.textContent = `Currently using ${theme} mode.`;
        }
    };
    const onCompare = (): void => navigate(wallTrigger);
    const onLab = (): void => navigate(labTrigger);
    const onPreferences = (): void => openPreferences();
    const onTheme = (): void => {
        toggleTheme({ root, storage });
        syncPreferences();
    };
    const onSystem = (): void => {
        resetThemeToDefault({ root, storage, media });
        syncPreferences();
    };
    const onClose = (): void => closePreferences();

    compareButton?.addEventListener("click", onCompare);
    labButton?.addEventListener("click", onLab);
    preferencesButton?.addEventListener("click", onPreferences);
    preferencesThemeButton?.addEventListener("click", onTheme);
    preferencesSystemButton?.addEventListener("click", onSystem);
    preferencesCloseButton?.addEventListener("click", onClose);

    const observer = new MutationObserver(syncPreferences);
    observer.observe(root, { attributes: true, attributeFilter: ["data-theme"] });
    syncPreferences();

    return () => {
        compareButton?.removeEventListener("click", onCompare);
        labButton?.removeEventListener("click", onLab);
        preferencesButton?.removeEventListener("click", onPreferences);
        preferencesThemeButton?.removeEventListener("click", onTheme);
        preferencesSystemButton?.removeEventListener("click", onSystem);
        preferencesCloseButton?.removeEventListener("click", onClose);
        observer.disconnect();
    };
}
