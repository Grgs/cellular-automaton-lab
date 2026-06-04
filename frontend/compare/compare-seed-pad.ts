/**
 * A small paint grid for designing the compare seed by drawing.
 *
 * The seed is a bit string; this pad is the exact inverse of the traversal
 * mapping: the grid is read row-major to produce bits, and a bit string fills
 * the grid row-major. Editing the pad and editing the seed text field stay in
 * sync. The pad width controls how the 1-D bit string wraps into rows; it is
 * independent of how a comparison's traversal later consumes the bits.
 */

const MIN_WIDTH = 1;
const MAX_WIDTH = 16;

export function toBits(seed: string): string {
    return seed.replace(/[^01]/g, "");
}

export function trimTrailingZeros(bits: string): string {
    let end = bits.length;
    while (end > 0 && bits[end - 1] === "0") {
        end -= 1;
    }
    return bits.slice(0, end);
}

/** Pad height for a bit string at the given width: at least square, taller if needed. */
export function derivePadHeight(bitLength: number, width: number): number {
    return Math.max(width, Math.ceil(bitLength / width));
}

export function seedBitAt(bits: string, width: number, row: number, col: number): boolean {
    const index = row * width + col;
    return index < bits.length && bits[index] === "1";
}

export function setSeedBit(
    bits: string,
    width: number,
    row: number,
    col: number,
    value: boolean,
): string {
    const index = row * width + col;
    const chars = bits.split("");
    while (chars.length <= index) {
        chars.push("0");
    }
    chars[index] = value ? "1" : "0";
    return trimTrailingZeros(chars.join(""));
}

/** Group bits into width-sized rows separated by spaces (the seed text display). */
export function chunkBits(bits: string, width: number): string {
    const rows: string[] = [];
    for (let index = 0; index < bits.length; index += width) {
        rows.push(bits.slice(index, index + width));
    }
    return rows.join(" ");
}

/** Infer a pad width from equally sized whitespace groups (e.g. "01100 11000"). */
export function inferWidth(seed: string): number | null {
    const groups = seed
        .trim()
        .split(/\s+/)
        .filter((group) => /^[01]+$/.test(group));
    const first = groups[0];
    if (
        first !== undefined &&
        groups.length >= 2 &&
        groups.every((g) => g.length === first.length)
    ) {
        return first.length;
    }
    return null;
}

function clampWidth(value: number): number {
    if (!Number.isFinite(value)) {
        return MIN_WIDTH;
    }
    return Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, Math.round(value)));
}

function element<K extends keyof HTMLElementTagNameMap>(
    tag: K,
    attrs: Record<string, string> = {},
    text?: string,
): HTMLElementTagNameMap[K] {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
        node.setAttribute(key, value);
    }
    if (text !== undefined) {
        node.textContent = text;
    }
    return node;
}

export interface SeedPadOptions {
    getSeed(): string;
    onSeedChange(formatted: string): void;
    initialWidth?: number;
}

export interface SeedPadController {
    element: HTMLElement;
    /** Re-read the seed (e.g. after the text field was edited) and re-render. */
    syncFromSeed(): void;
    dispose(): void;
}

export function createSeedPad(options: SeedPadOptions): SeedPadController {
    let width = clampWidth(options.initialWidth ?? 5);

    const grid = element("div", { class: "compare-seedpad-grid" });
    const widthInput = element("input", {
        type: "number",
        class: "compare-seedpad-width",
        value: String(width),
        min: String(MIN_WIDTH),
        max: String(MAX_WIDTH),
        "aria-label": "Pad width",
    });
    const clearButton = element("button", { type: "button", class: "compare-mini" }, "Clear");
    const info = element("span", { class: "compare-seedpad-info" });

    const controls = element("div", { class: "compare-seedpad-controls" });
    const widthLabel = element("label", { class: "compare-seedpad-widthlabel" }, "width");
    widthLabel.append(widthInput);
    controls.append(widthLabel, clearButton, info);

    const root = element("div", { class: "compare-seedpad" });
    root.append(controls, grid);

    function currentBits(): string {
        return toBits(options.getSeed());
    }

    function commit(bits: string): void {
        options.onSeedChange(chunkBits(bits, width));
        render();
    }

    function render(): void {
        const bits = currentBits();
        const height = derivePadHeight(bits.length, width);
        grid.style.gridTemplateColumns = `repeat(${width}, 1fr)`;
        grid.replaceChildren();
        for (let row = 0; row < height; row += 1) {
            for (let col = 0; col < width; col += 1) {
                const on = seedBitAt(bits, width, row, col);
                const cell = element("button", {
                    type: "button",
                    class: on ? "compare-seedpad-cell is-on" : "compare-seedpad-cell",
                    "data-row": String(row),
                    "data-col": String(col),
                    "aria-label": `cell ${row}, ${col}`,
                    "aria-pressed": on ? "true" : "false",
                });
                grid.append(cell);
            }
        }
        const liveCount = (bits.match(/1/g) ?? []).length;
        info.textContent = `${liveCount} cells · ${bits.length} bits`;
    }

    function cellPosition(target: EventTarget | null): { row: number; col: number } | null {
        if (!(target instanceof HTMLElement)) {
            return null;
        }
        const row = target.getAttribute("data-row");
        const col = target.getAttribute("data-col");
        if (row === null || col === null) {
            return null;
        }
        return { row: Number(row), col: Number(col) };
    }

    let painting = false;
    let paintValue = false;

    function applyAt(position: { row: number; col: number }): void {
        commit(setSeedBit(currentBits(), width, position.row, position.col, paintValue));
    }

    function onPointerDown(event: PointerEvent): void {
        const position = cellPosition(event.target);
        if (!position) {
            return;
        }
        event.preventDefault();
        painting = true;
        paintValue = !seedBitAt(currentBits(), width, position.row, position.col);
        applyAt(position);
    }

    function onPointerMove(event: PointerEvent): void {
        if (!painting) {
            return;
        }
        const position = cellPosition(event.target);
        if (position) {
            applyAt(position);
        }
    }

    function onPointerUp(): void {
        painting = false;
    }

    grid.addEventListener("pointerdown", onPointerDown);
    grid.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);

    widthInput.addEventListener("change", () => {
        width = clampWidth(Number(widthInput.value));
        widthInput.value = String(width);
        render();
    });
    clearButton.addEventListener("click", () => commit(""));

    function syncFromSeed(): void {
        const inferred = inferWidth(options.getSeed());
        if (inferred !== null) {
            width = clampWidth(inferred);
            widthInput.value = String(width);
        }
        render();
    }

    render();

    return {
        element: root,
        syncFromSeed,
        dispose(): void {
            window.removeEventListener("pointerup", onPointerUp);
        },
    };
}
