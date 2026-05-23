import { describe, expect, it } from "vitest";

import canonicalDefaults from "../config/defaults.json";
import { FRONTEND_DEFAULTS } from "./defaults.js";

describe("frontend defaults", () => {
    it("uses config/defaults.json as the no-bootstrap fallback", () => {
        expect(FRONTEND_DEFAULTS).toEqual(canonicalDefaults);
    });
});
