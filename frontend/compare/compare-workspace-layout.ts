interface CompareWorkspaceLayoutOptions {
    setup: HTMLElement;
    boardWall: HTMLElement;
    inspector: HTMLElement;
    dock: HTMLElement;
    setupToggle: HTMLButtonElement;
    inspectorToggle: HTMLButtonElement;
}

export interface CompareWorkspaceLayout {
    element: HTMLElement;
    openSetup(): void;
    openInspector(): void;
    closeSetup(): boolean;
    closeInspector(): boolean;
    closeDrawer(): boolean;
    dispose(): void;
}

/** Compose existing workspace nodes without recreating their interactive DOM. */
export function createCompareWorkspaceLayout(
    options: CompareWorkspaceLayoutOptions,
): CompareWorkspaceLayout {
    const { setup, boardWall, inspector, dock, setupToggle, inspectorToggle } = options;
    const backdrop = document.createElement("button");
    backdrop.className = "compare-workspace-backdrop";
    backdrop.type = "button";
    backdrop.tabIndex = -1;
    backdrop.setAttribute("aria-label", "Close Compare drawer");
    let returnFocus: HTMLElement | null = null;
    const isNarrow = (): boolean => window.innerWidth < 960;

    const grid = document.createElement("div");
    grid.className = "compare-workspace-grid";
    grid.append(setup, boardWall, inspector);
    const root = document.createElement("div");
    root.className = "wall-screen compare-workspace";
    root.append(grid, dock, backdrop);

    function rememberFocus(): void {
        returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    }

    function sync(): void {
        const setupOpen = setup.classList.contains("is-open");
        const inspectorOpen = inspector.classList.contains("is-open");
        setup.toggleAttribute("inert", !setupOpen);
        inspector.toggleAttribute("inert", !inspectorOpen);
        setupToggle.setAttribute("aria-expanded", setupOpen ? "true" : "false");
        inspectorToggle.setAttribute("aria-expanded", inspectorOpen ? "true" : "false");
        root.classList.toggle("has-open-drawer", setupOpen || inspectorOpen);
    }

    function close(node: HTMLElement): boolean {
        if (!node.classList.contains("is-open")) {
            return false;
        }
        node.classList.remove("is-open");
        node.setAttribute("inert", "");
        sync();
        returnFocus?.focus();
        returnFocus = null;
        return true;
    }

    function open(node: HTMLElement, other: HTMLElement): void {
        rememberFocus();
        if (isNarrow()) {
            other.classList.remove("is-open");
        }
        node.removeAttribute("inert");
        node.classList.add("is-open");
        sync();
    }

    const layout: CompareWorkspaceLayout = {
        element: root,
        openSetup: () => open(setup, inspector),
        openInspector: () => open(inspector, setup),
        closeSetup: () => close(setup),
        closeInspector: () => close(inspector),
        closeDrawer(): boolean {
            return layout.closeInspector() || layout.closeSetup();
        },
        dispose(): void {
            backdrop.removeEventListener("click", layout.closeDrawer);
            window.removeEventListener("resize", handleBreakpointChange);
        },
    };
    function handleBreakpointChange(): void {
        if (isNarrow()) {
            setup.classList.remove("is-open");
            inspector.classList.remove("is-open");
        } else {
            setup.classList.add("is-open");
            inspector.classList.add("is-open");
        }
        sync();
    }
    backdrop.addEventListener("click", layout.closeDrawer);
    window.addEventListener("resize", handleBreakpointChange);
    handleBreakpointChange();
    return layout;
}
