import { beforeEach, describe, expect, it } from "vitest";

import { bindDrawerNavSectionFeedback } from "./drawer-nav-bindings.js";
import type { DomElements } from "../types/dom.js";

class FakeIntersectionObserver {
    static instances: FakeIntersectionObserver[] = [];

    observed: Element[] = [];
    readonly callback: IntersectionObserverCallback;
    readonly options: IntersectionObserverInit | undefined;

    constructor(callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {
        this.callback = callback;
        this.options = options;
        FakeIntersectionObserver.instances.push(this);
    }

    observe(element: Element): void {
        this.observed.push(element);
    }

    disconnect(): void {
        this.observed = [];
    }

    unobserve(element: Element): void {
        this.observed = this.observed.filter((observed) => observed !== element);
    }

    emit(entries: Array<Partial<IntersectionObserverEntry> & { target: Element }>): void {
        this.callback(
            entries as IntersectionObserverEntry[],
            this as unknown as IntersectionObserver,
        );
    }
}

function section(id: string): HTMLElement {
    const element = document.createElement("section");
    element.id = id;
    element.className = "drawer-section";
    return element;
}

function stubRect(element: Element, top: number): void {
    element.getBoundingClientRect = () =>
        ({
            bottom: top + 100,
            height: 100,
            left: 0,
            right: 100,
            top,
            width: 100,
            x: 0,
            y: top,
            toJSON: () => ({}),
        }) as DOMRect;
}

function createElements(): DomElements {
    const drawer = document.createElement("aside");
    drawer.id = "control-drawer";
    const inner = document.createElement("div");
    inner.className = "control-drawer-inner";
    const nav = document.createElement("nav");
    nav.id = "drawer-nav";
    nav.className = "drawer-nav";
    nav.innerHTML = `
        <a href="#topology-section" class="drawer-nav-pill">Topology</a>
        <a href="#sim-section" class="drawer-nav-pill">Simulation</a>
        <a href="#patterns-section" class="drawer-nav-pill">Patterns</a>
    `;
    inner.append(
        nav,
        section("topology-section"),
        section("sim-section"),
        section("patterns-section"),
    );
    drawer.append(inner);
    document.body.replaceChildren(drawer);

    return {
        controlDrawer: drawer,
        drawerNav: nav,
    } as DomElements;
}

function currentNavText(elements: DomElements): string | null {
    return (
        elements.drawerNav?.querySelector(".drawer-nav-pill[aria-current='true']")?.textContent ??
        null
    );
}

describe("controls/drawer-nav-bindings", () => {
    beforeEach(() => {
        FakeIntersectionObserver.instances = [];
        document.body.replaceChildren();
    });

    it("marks the first drawer section link current initially", () => {
        const elements = createElements();

        bindDrawerNavSectionFeedback(elements, {
            intersectionObserverFactory: FakeIntersectionObserver,
        });

        expect(currentNavText(elements)).toBe("Topology");
        expect(elements.drawerNav?.querySelectorAll(".drawer-nav-pill.is-active")).toHaveLength(1);
    });

    it("updates the active drawer link immediately when a nav pill is clicked", () => {
        const elements = createElements();
        bindDrawerNavSectionFeedback(elements, {
            intersectionObserverFactory: FakeIntersectionObserver,
        });

        const patternsLink = elements.drawerNav?.querySelector<HTMLAnchorElement>(
            "a[href='#patterns-section']",
        );
        patternsLink?.click();

        expect(currentNavText(elements)).toBe("Patterns");
        expect(
            elements.drawerNav
                ?.querySelector("a[href='#topology-section']")
                ?.hasAttribute("aria-current"),
        ).toBe(false);
    });

    it("tracks the most visible drawer section from intersection changes", () => {
        const elements = createElements();
        bindDrawerNavSectionFeedback(elements, {
            intersectionObserverFactory: FakeIntersectionObserver,
        });
        const observer = FakeIntersectionObserver.instances[0];
        expect(observer).toBeDefined();
        const topology = document.getElementById("topology-section");
        const simulation = document.getElementById("sim-section");
        const patterns = document.getElementById("patterns-section");

        expect(observer?.observed.map((element) => element.id)).toEqual([
            "topology-section",
            "sim-section",
            "patterns-section",
        ]);

        observer?.emit([
            { target: topology as Element, isIntersecting: true, intersectionRatio: 0.2 },
            { target: simulation as Element, isIntersecting: true, intersectionRatio: 0.7 },
            { target: patterns as Element, isIntersecting: true, intersectionRatio: 0.4 },
        ]);

        expect(currentNavText(elements)).toBe("Simulation");

        observer?.emit([
            { target: simulation as Element, isIntersecting: false, intersectionRatio: 0 },
            { target: patterns as Element, isIntersecting: true, intersectionRatio: 0.8 },
        ]);

        expect(currentNavText(elements)).toBe("Patterns");
    });

    it("prefers the section closest to the sticky nav marker while scrolling", () => {
        const elements = createElements();
        bindDrawerNavSectionFeedback(elements, {
            intersectionObserverFactory: FakeIntersectionObserver,
        });
        const observer = FakeIntersectionObserver.instances[0];
        expect(observer).toBeDefined();
        const topology = document.getElementById("topology-section") as HTMLElement;
        const simulation = document.getElementById("sim-section") as HTMLElement;
        const patterns = document.getElementById("patterns-section") as HTMLElement;

        stubRect(elements.drawerNav as HTMLElement, 0);
        stubRect(topology, 24);
        stubRect(simulation, 86);
        stubRect(patterns, 122);

        observer?.emit([
            { target: topology, isIntersecting: true, intersectionRatio: 0.9 },
            { target: simulation, isIntersecting: true, intersectionRatio: 0.4 },
            { target: patterns, isIntersecting: true, intersectionRatio: 0.8 },
        ]);

        expect(currentNavText(elements)).toBe("Simulation");
    });

    it("keeps the current link when the observer reports no visible sections", () => {
        const elements = createElements();
        bindDrawerNavSectionFeedback(elements, {
            intersectionObserverFactory: FakeIntersectionObserver,
        });
        const observer = FakeIntersectionObserver.instances[0];
        expect(observer).toBeDefined();

        observer?.emit([
            {
                target: document.getElementById("topology-section") as Element,
                isIntersecting: false,
                intersectionRatio: 0,
            },
            {
                target: document.getElementById("sim-section") as Element,
                isIntersecting: false,
                intersectionRatio: 0,
            },
        ]);

        expect(currentNavText(elements)).toBe("Topology");
    });

    it("still supports click feedback when IntersectionObserver is unavailable", () => {
        const elements = createElements();
        bindDrawerNavSectionFeedback(elements);

        elements.drawerNav?.querySelector<HTMLAnchorElement>("a[href='#sim-section']")?.click();

        expect(currentNavText(elements)).toBe("Simulation");
    });
});
