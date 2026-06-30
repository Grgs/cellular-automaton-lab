import { matchSorter, rankings } from "match-sorter";

export interface TilingSearchData {
    value: string;
    label: string;
    group: string;
    family: string;
    previewKey: string;
    renderKind: string;
    sizingMode: string;
    searchAliases: readonly string[];
}

function normalizeTilingSearchText(value: string): string {
    return value
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/&/g, " and ")
        .replace(/[^a-z0-9]+/g, " ")
        .trim();
}

function tilingSearchForms(value: string): string[] {
    const normalized = normalizeTilingSearchText(value);
    if (!normalized) {
        return [];
    }
    const compact = normalized.replace(/\s+/g, "");
    return compact === normalized ? [normalized] : [normalized, compact];
}

export function tilingSearchQueryForms(value: string): string[] {
    const normalized = normalizeTilingSearchText(value);
    if (!normalized) {
        return [];
    }
    const compact = normalized.replace(/\s+/g, "");
    return compact !== normalized && compact.length <= 5 ? [normalized, compact] : [normalized];
}

export function tilingSearchTextFromTerms(terms: readonly string[]): string {
    return [...new Set(terms.flatMap(tilingSearchForms))].join(" ");
}

export function tilingSearchText(optionData: TilingSearchData): string {
    return tilingSearchTextFromTerms([
        optionData.label,
        optionData.value,
        optionData.group,
        optionData.family,
        optionData.sizingMode === "patch_depth" ? "patch depth substitution" : "grid cell size",
        optionData.renderKind,
        optionData.previewKey,
        ...optionData.searchAliases,
    ]);
}

export function matchTilingSearchItems<T>(
    items: readonly T[],
    rawQuery: string,
    getSearchText: (item: T) => string,
): Set<T> {
    const queries = tilingSearchQueryForms(rawQuery);
    return new Set(
        queries.length === 0
            ? items
            : queries.flatMap((query) =>
                  matchSorter(items, query, {
                      keys: [getSearchText],
                      threshold: rankings.CONTAINS,
                  }),
              ),
    );
}
