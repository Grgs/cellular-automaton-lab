import type { DomElements } from "../types/dom.js";

const ACTIVE_CLASS = "is-active";
const CURRENT_SECTION = "true";
const DRAWER_INNER_SELECTOR = ".control-drawer-inner";
const NAV_LINK_SELECTOR = ".drawer-nav-pill[href^='#']";

type IntersectionObserverFactory = new (
    callback: IntersectionObserverCallback,
    options?: IntersectionObserverInit,
) => Pick<IntersectionObserver, "observe">;

export interface DrawerNavFeedbackOptions {
    intersectionObserverFactory?: IntersectionObserverFactory;
}

function sectionIdFromLink(link: HTMLAnchorElement): string | null {
    const href = link.getAttribute("href") ?? "";
    if (!href.startsWith("#") || href.length <= 1) {
        return null;
    }
    try {
        return decodeURIComponent(href.slice(1));
    } catch {
        return href.slice(1);
    }
}

function setActiveNavLink(
    links: readonly HTMLAnchorElement[],
    activeSectionId: string | null,
): void {
    for (const link of links) {
        const isActive = sectionIdFromLink(link) === activeSectionId;
        link.classList.toggle(ACTIVE_CLASS, isActive);
        if (isActive) {
            link.setAttribute("aria-current", CURRENT_SECTION);
        } else {
            link.removeAttribute("aria-current");
        }
    }
}

export function bindDrawerNavSectionFeedback(
    elements: DomElements,
    options: DrawerNavFeedbackOptions = {},
): void {
    const nav = elements.drawerNav;
    const drawer = elements.controlDrawer;
    if (!nav || !drawer) {
        return;
    }

    const links = Array.from(nav.querySelectorAll<HTMLAnchorElement>(NAV_LINK_SELECTOR));
    const sectionLinks = links
        .map((link) => {
            const sectionId = sectionIdFromLink(link);
            const section = sectionId ? document.getElementById(sectionId) : null;
            return section ? { link, section } : null;
        })
        .filter((pair): pair is { link: HTMLAnchorElement; section: HTMLElement } => pair !== null);
    if (sectionLinks.length === 0) {
        return;
    }

    const sectionOrder = new Map<HTMLElement, number>(
        sectionLinks.map(({ section }, index) => [section, index]),
    );
    const sectionRatios = new Map<HTMLElement, number>();

    const updateFromRatios = (): void => {
        const navBottom = nav.getBoundingClientRect().bottom;
        const visibleSections = sectionLinks
            .map(({ section }) => ({
                section,
                ratio: sectionRatios.get(section) ?? 0,
                top: section.getBoundingClientRect().top,
                order: sectionOrder.get(section) ?? 0,
            }))
            .filter(({ ratio }) => ratio > 0)
            .sort((first, second) => {
                const firstAtMarker = first.top <= navBottom + 8;
                const secondAtMarker = second.top <= navBottom + 8;
                if (firstAtMarker && secondAtMarker) {
                    return (
                        second.top - first.top ||
                        second.ratio - first.ratio ||
                        first.order - second.order
                    );
                }
                if (firstAtMarker) {
                    return -1;
                }
                if (secondAtMarker) {
                    return 1;
                }
                return (
                    first.top - second.top ||
                    second.ratio - first.ratio ||
                    first.order - second.order
                );
            });
        const activeSection = visibleSections[0]?.section;
        if (activeSection) {
            setActiveNavLink(links, activeSection.id);
        }
    };

    const initialSection = sectionLinks[0]?.section;
    if (!initialSection) {
        return;
    }
    setActiveNavLink(links, initialSection.id);

    for (const { link, section } of sectionLinks) {
        link.addEventListener("click", (event) => {
            event.preventDefault();
            const sectionId = sectionIdFromLink(link);
            if (sectionId) {
                setActiveNavLink(links, sectionId);
                section.scrollIntoView?.({ block: "start", inline: "nearest" });
            }
        });
    }

    const Observer = options.intersectionObserverFactory ?? globalThis.IntersectionObserver ?? null;
    if (!Observer) {
        return;
    }

    const observerRoot =
        drawer.querySelector<HTMLElement>(DRAWER_INNER_SELECTOR) ?? elements.controlDrawer;
    const observer = new Observer(
        (entries) => {
            for (const entry of entries) {
                if (!(entry.target instanceof HTMLElement)) {
                    continue;
                }
                sectionRatios.set(entry.target, entry.isIntersecting ? entry.intersectionRatio : 0);
            }
            updateFromRatios();
        },
        {
            root: observerRoot,
            threshold: [0.18, 0.35, 0.55, 0.8],
        },
    );

    for (const { section } of sectionLinks) {
        observer.observe(section);
    }
}
