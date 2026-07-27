import { describe, expect, it, vi } from "vitest";
import type { SeedFilmstripResult } from "../types/domain.js";
import type { FilmstripViewController } from "./compare-filmstrip-view.js";
import { createCompareFilmstripPresentation } from "./compare-filmstrip-presentation.js";

function filmstrip(): SeedFilmstripResult {
    return {
        rule_name: "conway",
        seed: "1",
        traversal: "bfs",
        frame_count: 1,
        grid_size: 4,
        tilings: [],
    };
}

function stubView(): FilmstripViewController {
    return {
        element: document.createElement("div"),
        load: vi.fn(async () => {}),
        focus: vi.fn(),
        setSelectedBoard: vi.fn(),
        setEditMode: vi.fn(),
        setManagementBusy: vi.fn(),
        setManagementBlocked: vi.fn(),
        refreshAddControl: vi.fn(),
        updateBoardData: vi.fn(),
        removeBoard: vi.fn(() => true),
        currentFrameIndex: vi.fn(() => 0),
        setBoardOverlay: vi.fn(() => true),
        setHeroToolbelt: vi.fn(),
        setHeroToolbeltHome: vi.fn(),
        openReplacePicker: vi.fn(() => true),
        closeTilingPicker: vi.fn(() => false),
        detachPlayer: vi.fn(),
        dispose: vi.fn(),
    };
}

function presentation(view = stubView()) {
    const createView = vi.fn(() => view);
    const patternSelect = document.createElement("select");
    patternSelect.add(new Option("Spaceship: Glider", "glider"));
    const ruleSelect = document.createElement("select");
    ruleSelect.add(new Option("Life-like: Conway's Life", "conway"));
    return {
        controller: createCompareFilmstripPresentation(createView, patternSelect, ruleSelect),
        createView,
        view,
    };
}

describe("compare filmstrip presentation", () => {
    it("creates and reuses the filmstrip view only when a result is loaded", async () => {
        const { controller, createView, view } = presentation();
        const [element, load] = controller;

        expect(createView).not.toHaveBeenCalled();
        expect(element.querySelector(".compare-stage-hero")?.getAttribute("hidden")).toBeNull();

        await load(filmstrip(), { autoplay: true });
        expect(createView).toHaveBeenCalledOnce();
        expect(element.lastElementChild).toBe(view.element);
        expect(view.load).toHaveBeenLastCalledWith(filmstrip(), { autoplay: true });

        await load(filmstrip(), { preserveBoards: true });
        expect(createView).toHaveBeenCalledOnce();
        expect(view.load).toHaveBeenLastCalledWith(filmstrip(), { preserveBoards: true });
    });

    it("coordinates hero, caption, and loading states", async () => {
        const { controller, view } = presentation();
        const [element, load, showHero, updateCaption, setLoading] = controller;

        updateCaption({
            seed: "",
            pattern: "glider",
            rule: "conway",
            traversal: "bfs",
            frames: 20,
            grid_size: 16,
            geometries: ["square", "hex"],
        });
        const caption = element.querySelector<HTMLElement>(".compare-stage-caption");
        expect(caption?.textContent).toBe("Glider · Conway's Life · 2 tilings");
        expect(caption?.hidden).toBe(true);

        await load(filmstrip());
        expect(caption?.hidden).toBe(false);
        showHero(true);
        expect(view.element.hidden).toBe(true);
        expect(caption?.hidden).toBe(true);
        showHero(false);
        expect(view.element.hidden).toBe(false);
        expect(caption?.hidden).toBe(false);

        setLoading("Updating comparison...");
        expect(element.classList.contains("is-loading")).toBe(true);
        expect(element.querySelector(".compare-wall-loading-text")?.textContent).toBe(
            "Updating comparison...",
        );
        setLoading(null);
        expect(element.classList.contains("is-loading")).toBe(false);
    });
});
