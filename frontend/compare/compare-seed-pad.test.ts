import { afterEach, describe, expect, it } from "vitest";

import {
    chunkBits,
    createSeedPad,
    derivePadHeight,
    inferWidth,
    seedBitAt,
    setSeedBit,
    toBits,
    trimTrailingZeros,
} from "./compare-seed-pad.js";

describe("seed-pad bit helpers", () => {
    it("strips non-bit characters", () => {
        expect(toBits("01100 11000 01000")).toBe("011001100001000");
        expect(toBits("0,1,x,1")).toBe("011");
    });

    it("trims trailing zeros", () => {
        expect(trimTrailingZeros("0110100")).toBe("01101");
        expect(trimTrailingZeros("0000")).toBe("");
    });

    it("derives an at-least-square pad height", () => {
        expect(derivePadHeight(0, 5)).toBe(5);
        expect(derivePadHeight(15, 5)).toBe(5);
        expect(derivePadHeight(40, 5)).toBe(8);
    });

    it("reads a bit by row/col", () => {
        const bits = "0110011000"; // row0=01100, row1=11000
        expect(seedBitAt(bits, 5, 0, 1)).toBe(true);
        expect(seedBitAt(bits, 5, 0, 0)).toBe(false);
        expect(seedBitAt(bits, 5, 1, 0)).toBe(true);
        expect(seedBitAt(bits, 5, 5, 0)).toBe(false); // out of range
    });

    it("sets a bit, extending and trimming as needed", () => {
        expect(setSeedBit("", 5, 0, 2, true)).toBe("001");
        expect(setSeedBit("00100", 5, 0, 2, false)).toBe("");
        expect(setSeedBit("01100", 5, 1, 0, true)).toBe("011001");
    });

    it("chunks bits into width-sized rows", () => {
        expect(chunkBits("011001100001000", 5)).toBe("01100 11000 01000");
        expect(chunkBits("", 5)).toBe("");
    });

    it("infers width from equal whitespace groups", () => {
        expect(inferWidth("01100 11000 01000")).toBe(5);
        expect(inferWidth("11011")).toBeNull();
        expect(inferWidth("011 00 1")).toBeNull();
    });
});

describe("createSeedPad controller", () => {
    afterEach(() => {
        document.body.innerHTML = "";
    });

    function mount(initial = "") {
        let seed = initial;
        const pad = createSeedPad({
            getSeed: () => seed,
            onSeedChange: (formatted) => {
                seed = formatted;
            },
            initialWidth: 5,
        });
        document.body.append(pad.element);
        return { pad, getSeed: () => seed };
    }

    function cell(row: number, col: number): HTMLButtonElement {
        const node = document.querySelector<HTMLButtonElement>(
            `.compare-seedpad-cell[data-row="${row}"][data-col="${col}"]`,
        );
        if (!node) {
            throw new Error(`missing cell ${row},${col}`);
        }
        return node;
    }

    it("renders an at-least-square grid for an empty seed", () => {
        mount("");
        expect(document.querySelectorAll(".compare-seedpad-cell")).toHaveLength(25); // 5x5
    });

    it("painting a cell updates the seed and marks it on", () => {
        const { getSeed } = mount("");
        cell(0, 2).dispatchEvent(new Event("pointerdown", { bubbles: true }));
        expect(getSeed()).toBe("001");
        expect(cell(0, 2).classList.contains("is-on")).toBe(true);

        // painting the same cell again clears it
        cell(0, 2).dispatchEvent(new Event("pointerdown", { bubbles: true }));
        expect(getSeed()).toBe("");
    });

    it("reflects an external seed and infers width on sync", () => {
        const { pad } = mount("111 000 111");
        pad.syncFromSeed();
        expect(document.querySelectorAll('.compare-seedpad-cell[data-row="0"]')).toHaveLength(3);
        expect(document.querySelectorAll(".compare-seedpad-cell.is-on")).toHaveLength(6);
    });
});
