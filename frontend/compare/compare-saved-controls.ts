import { element as el } from "./compare-dom.js";
import type { CompareRunConfig } from "./compare-run-link.js";
import {
    deleteSavedCompareRun,
    deleteSavedTilingSet,
    listSavedCompareRuns,
    listSavedTilingSets,
    saveCompareRun,
    saveTilingSet,
    type SavedTilingSet,
} from "./compare-storage.js";
import type { CompareWorkspaceStore } from "./compare-workspace-store.js";

export interface CompareSavedControlsOptions {
    workspaceStore: CompareWorkspaceStore;
    currentRunConfig(): CompareRunConfig;
    selectedGeometries(): readonly string[];
    applyRunConfig(config: CompareRunConfig): Promise<void>;
    applyTilingSet(saved: SavedTilingSet): string;
    statusElement: HTMLElement;
}

export interface CompareSavedControls {
    element: HTMLElement;
    refresh(): void;
}

/**
 * Owns the saved-run and saved-tiling-set UI state. The compare panel supplies
 * only the domain transitions needed to apply a persisted selection.
 */
export function createCompareSavedControls({
    workspaceStore,
    currentRunConfig,
    selectedGeometries,
    applyRunConfig,
    applyTilingSet,
    statusElement,
}: CompareSavedControlsOptions): CompareSavedControls {
    let editingSavedRunId = "";
    let editingSavedTilingSetId = "";

    const savedRunNameInput = el("input", {
        class: "compare-field compare-saved-name",
        type: "text",
        placeholder: "Run name",
        "aria-label": "Saved run name",
    });
    const savedRunSelect = el("select", {
        class: "compare-field compare-saved-select",
        "aria-label": "Saved compare runs",
    });
    const saveRunButton = el("button", {
        class: "compare-mini",
        type: "button",
        textContent: "Save run",
    });
    const loadRunButton = el("button", {
        class: "compare-mini",
        type: "button",
        textContent: "Load run",
    });
    const deleteRunButton = el("button", {
        class: "compare-mini",
        type: "button",
        textContent: "Delete run",
    });
    const savedRunHint = el("div", {
        class: "compare-saved-empty",
        id: "compare-saved-runs-hint",
    });
    const savedTilingSetNameInput = el("input", {
        class: "compare-field compare-saved-name",
        type: "text",
        placeholder: "Tiling set name",
        "aria-label": "Saved tiling set name",
    });
    const savedTilingSetSelect = el("select", {
        class: "compare-field compare-saved-select",
        "aria-label": "Saved tiling sets",
    });
    const saveTilingSetButton = el("button", {
        class: "compare-mini",
        type: "button",
        textContent: "Save set",
    });
    const loadTilingSetButton = el("button", {
        class: "compare-mini",
        type: "button",
        textContent: "Load set",
    });
    const deleteTilingSetButton = el("button", {
        class: "compare-mini",
        type: "button",
        textContent: "Delete set",
    });
    const savedTilingSetHint = el("div", {
        class: "compare-saved-empty",
        id: "compare-saved-tilings-hint",
    });

    const element = el("div", { class: "compare-saved" }, [
        el(
            "section",
            { class: "compare-saved-section", "aria-labelledby": "compare-saved-runs-title" },
            [
                el("h3", {
                    class: "compare-saved-title",
                    id: "compare-saved-runs-title",
                    textContent: "Saved runs",
                }),
                el("div", { class: "compare-saved-row" }, [
                    savedRunNameInput,
                    saveRunButton,
                    savedRunSelect,
                    loadRunButton,
                    deleteRunButton,
                ]),
                savedRunHint,
            ],
        ),
        el(
            "section",
            {
                class: "compare-saved-section",
                "aria-labelledby": "compare-saved-tilings-title",
            },
            [
                el("h3", {
                    class: "compare-saved-title",
                    id: "compare-saved-tilings-title",
                    textContent: "Saved tiling sets",
                }),
                el("div", { class: "compare-saved-row" }, [
                    savedTilingSetNameInput,
                    saveTilingSetButton,
                    savedTilingSetSelect,
                    loadTilingSetButton,
                    deleteTilingSetButton,
                ]),
                savedTilingSetHint,
            ],
        ),
    ]);

    function populateSavedSelect(
        select: HTMLSelectElement,
        items: readonly { id: string; name: string }[],
        emptyLabel: string,
        preferredId: string,
    ): void {
        select.replaceChildren();
        if (items.length === 0) {
            select.append(el("option", { value: "", textContent: emptyLabel }));
            select.disabled = true;
            return;
        }
        select.disabled = false;
        for (const item of items) {
            select.append(el("option", { value: item.id, textContent: item.name }));
        }
        if (preferredId && [...select.options].some((option) => option.value === preferredId)) {
            select.value = preferredId;
        }
    }

    function refresh(
        preferredRunId = savedRunSelect.value,
        preferredTilingSetId = savedTilingSetSelect.value,
    ): void {
        const runs = listSavedCompareRuns();
        const tilingSets = listSavedTilingSets();
        workspaceStore.update((state) => ({
            ...state,
            saved: { runs, tilingSets },
        }));
        populateSavedSelect(savedRunSelect, runs, "No saved runs", preferredRunId);
        populateSavedSelect(
            savedTilingSetSelect,
            tilingSets,
            "No saved tiling sets",
            preferredTilingSetId,
        );
        const hasRuns = runs.length > 0;
        const hasTilingSets = tilingSets.length > 0;
        loadRunButton.disabled = !hasRuns;
        deleteRunButton.disabled = !hasRuns;
        loadTilingSetButton.disabled = !hasTilingSets;
        deleteTilingSetButton.disabled = !hasTilingSets;
        savedRunHint.textContent = hasRuns
            ? `${runs.length} saved run${runs.length === 1 ? "" : "s"} available.`
            : "No saved runs yet. Name the current setup and choose Save run.";
        savedTilingSetHint.textContent = hasTilingSets
            ? `${tilingSets.length} saved tiling set${tilingSets.length === 1 ? "" : "s"} available.`
            : "No saved tiling sets yet. Select tilings, name the set, and choose Save set.";
    }

    function saveCurrentRun(): void {
        try {
            const replaceId = editingSavedRunId;
            const saved = saveCompareRun(savedRunNameInput.value, currentRunConfig());
            if (replaceId && replaceId !== saved.id) {
                deleteSavedCompareRun(replaceId);
            }
            editingSavedRunId = saved.id;
            savedRunNameInput.value = saved.name;
            refresh(saved.id, savedTilingSetSelect.value);
            statusElement.textContent = `Saved run "${saved.name}".`;
        } catch (error) {
            statusElement.textContent = `Could not save run: ${
                error instanceof Error ? error.message : String(error)
            }`;
        }
    }

    async function loadSelectedRun(): Promise<void> {
        const saved = workspaceStore
            .getState()
            .saved.runs.find((run) => run.id === savedRunSelect.value);
        if (!saved) {
            return;
        }
        await applyRunConfig(saved.config);
        editingSavedRunId = saved.id;
        savedRunNameInput.value = saved.name;
        refresh(saved.id, savedTilingSetSelect.value);
    }

    function deleteSelectedRun(): void {
        const saved = workspaceStore
            .getState()
            .saved.runs.find((run) => run.id === savedRunSelect.value);
        if (!saved) {
            return;
        }
        deleteSavedCompareRun(saved.id);
        if (editingSavedRunId === saved.id) {
            editingSavedRunId = "";
        }
        refresh("", savedTilingSetSelect.value);
        statusElement.textContent = `Deleted run "${saved.name}".`;
    }

    function saveCurrentTilingSet(): void {
        try {
            const replaceId = editingSavedTilingSetId;
            const saved = saveTilingSet(savedTilingSetNameInput.value, selectedGeometries());
            if (replaceId && replaceId !== saved.id) {
                deleteSavedTilingSet(replaceId);
            }
            editingSavedTilingSetId = saved.id;
            savedTilingSetNameInput.value = saved.name;
            refresh(savedRunSelect.value, saved.id);
            statusElement.textContent = `Saved tiling set "${saved.name}".`;
        } catch (error) {
            statusElement.textContent = `Could not save tiling set: ${
                error instanceof Error ? error.message : String(error)
            }`;
        }
    }

    function loadSelectedTilingSet(): void {
        const saved = workspaceStore
            .getState()
            .saved.tilingSets.find((set) => set.id === savedTilingSetSelect.value);
        if (!saved) {
            return;
        }
        const status = applyTilingSet(saved);
        editingSavedTilingSetId = saved.id;
        savedTilingSetNameInput.value = saved.name;
        refresh(savedRunSelect.value, saved.id);
        statusElement.textContent = status;
    }

    function deleteSelectedTilingSet(): void {
        const saved = workspaceStore
            .getState()
            .saved.tilingSets.find((set) => set.id === savedTilingSetSelect.value);
        if (!saved) {
            return;
        }
        deleteSavedTilingSet(saved.id);
        if (editingSavedTilingSetId === saved.id) {
            editingSavedTilingSetId = "";
        }
        refresh(savedRunSelect.value, "");
        statusElement.textContent = `Deleted tiling set "${saved.name}".`;
    }

    saveRunButton.addEventListener("click", saveCurrentRun);
    loadRunButton.addEventListener("click", () => void loadSelectedRun());
    deleteRunButton.addEventListener("click", deleteSelectedRun);
    saveTilingSetButton.addEventListener("click", saveCurrentTilingSet);
    loadTilingSetButton.addEventListener("click", loadSelectedTilingSet);
    deleteTilingSetButton.addEventListener("click", deleteSelectedTilingSet);

    return {
        element,
        refresh,
    };
}
