import type { SeedFilmstripResult } from "../types/domain.js";
import type { CompareRunConfig } from "./compare-run-link.js";
import { element as el } from "./compare-dom.js";
import type { FilmstripLoadOptions, FilmstripViewController } from "./compare-filmstrip-view.js";

export type CompareFilmstripPresentationController = readonly [
    element: HTMLElement,
    load: (filmstrip: SeedFilmstripResult, options?: FilmstripLoadOptions) => Promise<void>,
    showHero: (visible: boolean) => void,
    updateCaption: (config: CompareRunConfig) => void,
    setLoading: (message: string | null) => void,
];

/**
 * Owns the wall stage's empty/loading/boards states and the lazily-created
 * filmstrip view. Request scheduling remains with the panel; this controller
 * presents whichever authoritative result the scheduler installs.
 */
export function createCompareFilmstripPresentation(
    createView: () => FilmstripViewController,
    patternSelect: HTMLSelectElement,
    ruleSelect: HTMLSelectElement,
): CompareFilmstripPresentationController {
    const hero = el("div", { class: "compare-stage-hero" }, [
        el("div", { class: "compare-stage-hero-glyph", "aria-hidden": "true", text: "▦" }),
        el("div", {
            class: "compare-stage-hero-title",
            text: "Watch one seed evolve across every tiling",
        }),
        el("p", {
            class: "compare-stage-hero-blurb",
            text: "Pick a rule and tilings, then run every board on one shared clock.",
        }),
    ]);
    const loadingText = el("span", { class: "compare-wall-loading-text" });
    const loading = el(
        "div",
        {
            class: "compare-wall-loading",
            role: "status",
            "aria-live": "polite",
            hidden: true,
        },
        [
            loadingText,
            el("div", { class: "compare-wall-loading-grid", "aria-hidden": "true" }, [
                el("span", { class: "compare-wall-loading-card" }),
                el("span", { class: "compare-wall-loading-card" }),
                el("span", { class: "compare-wall-loading-card" }),
                el("span", { class: "compare-wall-loading-card" }),
            ]),
        ],
    );
    const caption = el("div", { class: "compare-stage-caption" });
    const element = el("div", { class: "compare-filmstrip-area" }, [caption, hero, loading]);
    let view: FilmstripViewController | null = null;

    function show(heroVisible: boolean): void {
        hero.hidden = !heroVisible;
        caption.hidden = heroVisible || !caption.textContent;
        if (view) {
            view.element.hidden = heroVisible;
        }
    }

    function load(filmstrip: SeedFilmstripResult, options?: FilmstripLoadOptions): Promise<void> {
        if (!view) {
            view = createView();
            element.append(view.element);
        }
        show(false);
        return view.load(filmstrip, options);
    }

    function updateCaption(config: CompareRunConfig): void {
        const seedLabel = config.pattern
            ? (patternSelect.selectedOptions[0]?.textContent ?? "").replace(/^[^:]*: /, "") ||
              config.pattern
            : "Custom seed";
        const displayedRule =
            (ruleSelect.selectedOptions[0]?.textContent ?? "").replace(/^[^:]*: /, "") ||
            config.rule;
        const count = config.geometries.length;
        caption.textContent = `${seedLabel} · ${displayedRule} · ${count} tiling${
            count === 1 ? "" : "s"
        }`;
        caption.hidden = hero.hidden === false;
    }

    function setLoading(message: string | null): void {
        loading.hidden = !message;
        element.classList.toggle("is-loading", !!message);
        if (message) {
            loadingText.textContent = message;
        }
    }

    return [element, load, show, updateCaption, setLoading];
}
