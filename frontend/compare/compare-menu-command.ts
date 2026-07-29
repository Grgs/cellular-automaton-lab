export type CompareConfigTab = "setup" | "tilings" | "saved" | "help";

/** Semantic actions the app shell may ask the Compare workspace to perform. */
export type CompareMenuCommand =
    | { type: "open-config"; tab: CompareConfigTab }
    | { type: "focus-rule" }
    | { type: "copy-run-link" };
