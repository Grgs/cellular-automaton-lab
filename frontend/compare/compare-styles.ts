export const COMPARE_PANEL_STYLES = `
.compare-thumb-link:focus-visible,
.compare-field:focus-visible,
.compare-seedpad-width:focus-visible,
.compare-seedpad-cell:focus-visible,
.compare-mini:focus-visible,
.compare-run:focus-visible,
.compare-link:focus-visible {
    outline: 2px solid var(--focus, #7aa7ff);
    outline-offset: 2px;
}
/* The wall fills the shared shell's content slot beneath the static header;
   the shell (styles.css) owns the header and the dock idiom. */
.wall-page {
    height: 100%;
    min-height: 0;
    display: flex;
    flex-direction: column;
    background: var(--panel-strong, #fff);
    color: var(--ink, #1f2430);
    font-family: var(--sans, sans-serif);
}
.wall-page[hidden] { display: none; }
.wall-page:focus { outline: none; }
/* The body under the fixed header is exactly one screen: the stage fills it and
   the docked transport pins beneath. Configuration overlays from the bottom
   sheet rather than scrolling below the fold, so nothing here scrolls. */
.compare-content {
    flex: 1 1 auto;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}
.wall-screen {
    height: 100%;
    min-height: 0;
    display: grid;
    grid-template-rows: minmax(0, 1fr) auto;
}
.compare-intro { color: var(--muted, #6d756f); font-size: 13px; margin: 6px 0 14px; }
/* Stage-first: the synchronized side-by-side fills the first screen. */
.compare-stage {
    min-width: 0;
    min-height: 0;
    display: flex;
    padding: 12px 18px;
}
.compare-stage-main {
    flex: 1 1 auto;
    min-width: 0;
    min-height: 0;
    display: flex;
}
/* Speaker view keeps the hero board bound to the stage's height (nowrap), so
   it fills rather than overflowing. Seed editing is edit mode's job in either
   layout, so the stage is the hero area alone. */
.compare-stage-main.is-speaker {
    display: flex;
    align-items: stretch;
    gap: 16px;
    flex-wrap: nowrap;
    min-height: 0;
}
.compare-stage-main.is-speaker .compare-filmstrip-area {
    flex: 1 1 480px;
    min-width: 0;
    min-height: 0;
}
.compare-stage-hero {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    text-align: center;
    min-height: 200px;
    padding: 28px 20px;
    border: 1px dashed var(--line, rgba(0, 0, 0, 0.18));
    border-radius: 12px;
    background: var(--help-bg, rgba(0, 0, 0, 0.03));
    color: var(--muted, #6d756f);
}
.compare-stage-hero[hidden] { display: none; }
.compare-stage-hero-glyph { font-size: 30px; line-height: 1; opacity: 0.5; }
.compare-stage-hero-title { font-size: 15px; color: var(--ink, #1f2430); }
.compare-stage-hero-blurb { font-size: 12px; margin: 0; max-width: 360px; line-height: 1.4; }
/* One dock: the transport plus the config/copy icons and the status line on a
   single row, pinned to the bottom of the first screen and reachable while the
   configuration disclosures scroll underneath. */
/* The dock idiom itself lives in styles.css (shared with the Lab dock); only
   the wall-specific composition remains here. */
.compare-dock .compare-filmstrip-transport { flex: 1 1 420px; }
.compare-edit-toggle.is-active {
    background: var(--btn-primary-bg, #bf5a36);
    border-color: var(--btn-primary-line, rgba(0, 0, 0, 0.2));
    color: var(--btn-primary-text, #fff);
}
.compare-config-actions { margin-bottom: 12px; }
/* Configuration lives in a bottom sheet the dock gear slides up over the stage. */
.compare-config-sheet {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 80;
    display: flex;
    flex-direction: column;
    max-height: 82dvh;
    background: var(--panel-strong, #fff);
    border-top: 1px solid var(--line, rgba(0, 0, 0, 0.12));
    box-shadow: 0 -14px 34px rgba(0, 0, 0, 0.28);
    transform: translateY(100%);
    transition: transform 0.24s ease;
}
.compare-config-sheet.is-open { transform: translateY(0); }
.compare-config-sheet-header {
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 18px;
    border-bottom: 1px solid var(--line, rgba(0, 0, 0, 0.12));
}
.compare-config-sheet-title { font-size: 14px; font-weight: 600; }
.compare-config-sheet-close { font-size: 18px; }
.compare-config-sheet-body {
    min-height: 0;
    overflow-y: auto;
    padding: 8px 18px 18px;
}
@media (prefers-reduced-motion: reduce) {
    .compare-config-sheet { transition: none; }
}
.compare-config {
    margin-top: 12px;
    border: 1px solid var(--line, rgba(0, 0, 0, 0.1));
    border-radius: 10px;
    background: var(--help-bg, rgba(0, 0, 0, 0.02));
}
.compare-config-summary {
    cursor: pointer;
    padding: 10px 12px;
    font-size: 13px;
    font-weight: 600;
    color: var(--ink, #1f2430);
    list-style: none;
}
.compare-config-summary::-webkit-details-marker { display: none; }
.compare-config-summary::before {
    content: "▸";
    margin-right: 8px;
    font-size: 10px;
    color: var(--muted, #6d756f);
}
.compare-config[open] > .compare-config-summary::before { content: "▾"; }
.compare-config-summary:focus-visible {
    outline: 2px solid var(--focus, #7aa7ff);
    outline-offset: -2px;
}
.compare-config-body { padding: 4px 12px 14px; }
.compare-form {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 10px 14px;
}
.compare-label { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--muted, #6d756f); }
.compare-field {
    box-sizing: border-box;
    width: 100%;
    min-width: 0;
    padding: 7px 9px;
    border-radius: 8px;
    border: 1px solid var(--field-border, rgba(0, 0, 0, 0.15));
    background: var(--field-bg, #fff);
    color: var(--field-text, #1f2430);
    font-family: var(--mono, monospace);
    font-size: 13px;
}
.compare-field:disabled {
    color: var(--muted, #6d756f);
    background: var(--help-bg, rgba(0, 0, 0, 0.03));
    cursor: not-allowed;
}
.compare-seed-workspace {
    display: grid;
    grid-template-columns: max-content minmax(0, 1fr);
    gap: 14px 22px;
    align-items: start;
    margin-top: 14px;
}
.compare-seed-workspace.is-shape-mode { grid-template-columns: 1fr; }
.compare-seedpad-block { min-width: 0; }
.compare-seedpreview-block { min-width: 0; }
.compare-seedpad-title { font-size: 12px; color: var(--muted, #6d756f); margin-bottom: 6px; }
.compare-seedpad { display: flex; flex-direction: column; gap: 8px; }
.compare-seedpad-controls { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.compare-seedpad-widthlabel { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; color: var(--muted, #6d756f); }
.compare-seedpad-width {
    width: 52px;
    padding: 4px 6px;
    border-radius: 6px;
    border: 1px solid var(--field-border, rgba(0, 0, 0, 0.15));
    background: var(--field-bg, #fff);
    color: var(--field-text, #1f2430);
    font-family: var(--mono, monospace);
    font-size: 12px;
}
.compare-seedpad-info { font-size: 12px; color: var(--muted, #6d756f); }
.compare-seedbits { max-width: 180px; }
.compare-seedbits-summary {
    width: max-content;
    color: var(--muted, #6d756f);
    cursor: pointer;
    font-size: 12px;
}
.compare-seedbits .compare-label { margin-top: 6px; }
.compare-seedpad-grid {
    display: grid;
    gap: 2px;
    width: max-content;
    max-width: 100%;
    touch-action: none;
}
.compare-seedpad-cell {
    width: 20px;
    height: 20px;
    padding: 0;
    border: 1px solid var(--field-border, rgba(31, 36, 48, 0.18));
    border-radius: 3px;
    background: var(--cell-dead, #fdf8ef);
    cursor: pointer;
}
.compare-seedpad-cell.is-on { background: var(--accent, #bf5a36); border-color: var(--accent-dark, #8a3d20); }
.compare-seedpreview { display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-start; }
.compare-seedpreview-empty { font-size: 12px; color: var(--muted, #6d756f); }
.compare-seedpreview-item { display: flex; flex-direction: column; gap: 3px; align-items: center; }
.compare-seedpreview-label { font-size: 10px; color: var(--muted, #6d756f); max-width: 100px; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.compare-seedpreview-slot { display: flex; align-items: center; justify-content: center; min-width: 96px; min-height: 60px; font-size: 11px; color: var(--muted, #6d756f); }
.compare-tilings-block { margin-top: 14px; }
.compare-tilings-controls { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }
.compare-tilings-summary { flex: 1 1 220px; font-size: 12px; color: var(--muted, #6d756f); }
.compare-tilings-tools {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
    flex: 1 1 420px;
    min-width: 0;
}
.compare-tilings-search { max-width: 180px; }
.compare-tilings-presets { display: flex; align-items: center; justify-content: flex-end; gap: 6px; flex-wrap: wrap; }
.compare-mini {
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 7px;
    border: 1px solid var(--btn-soft-line, rgba(0, 0, 0, 0.12));
    background: var(--btn-soft-bg, rgba(0, 0, 0, 0.06));
    color: var(--ink, #1f2430);
    cursor: pointer;
}
.compare-mini.is-active,
.compare-mini[aria-pressed="true"] {
    border-color: var(--accent, #bf5a36);
    background: color-mix(in srgb, var(--accent, #bf5a36) 18%, var(--btn-soft-bg, rgba(0, 0, 0, 0.06)));
    color: var(--ink, #1f2430);
}
.compare-mini:disabled {
    opacity: 0.5;
    cursor: default;
}
.compare-tilings {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
    gap: 8px 16px;
    max-height: 200px;
    overflow: auto;
    padding: 10px;
    border: 1px solid var(--line, rgba(0, 0, 0, 0.1));
    border-radius: 10px;
    background: var(--help-bg, rgba(0, 0, 0, 0.03));
}
.compare-tilings-empty {
    grid-column: 1 / -1;
    padding: 18px 8px;
    text-align: center;
    font-size: 12px;
    color: var(--muted, #6d756f);
}
.compare-tilings-group { min-width: 0; }
.compare-tilings-family { display: flex; align-items: center; gap: 6px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted, #6d756f); margin-bottom: 4px; }
.compare-family-count { color: var(--ink, #1f2430); font-family: var(--mono, monospace); letter-spacing: 0; }
.compare-dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.compare-tiling {
    display: grid;
    grid-template-columns: 18px minmax(0, 1fr);
    align-items: start;
    gap: 7px;
    min-height: 28px;
    padding: 4px 6px;
    border-radius: 6px;
    font-size: 12px;
    line-height: 1.25;
    cursor: pointer;
}
.compare-tiling:hover { background: var(--btn-soft-bg, rgba(0, 0, 0, 0.05)); }
.compare-tiling.is-disabled {
    color: var(--muted, #6d756f);
    cursor: not-allowed;
    opacity: 0.58;
}
.compare-tiling.is-disabled:hover { background: transparent; }
.compare-tiling:focus-within {
    outline: 2px solid var(--focus, #7aa7ff);
    outline-offset: 2px;
}
.compare-tiling input[type="checkbox"] {
    box-sizing: border-box;
    appearance: auto;
    -webkit-appearance: checkbox;
    width: 16px;
    height: 16px;
    min-width: 16px;
    margin: 1px 0 0;
    padding: 0;
    accent-color: var(--accent, #bf5a36);
    border-radius: 3px;
    transform: none;
}
.compare-saved {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 10px 16px;
    margin-top: 12px;
}
.compare-saved-section {
    min-width: 0;
    padding: 10px;
    border: 1px solid var(--line, rgba(0, 0, 0, 0.1));
    border-radius: 10px;
    background: var(--help-bg, rgba(0, 0, 0, 0.03));
}
.compare-saved-title {
    margin: 0 0 8px;
    color: var(--muted, #6d756f);
    font-size: 12px;
    font-weight: 600;
}
.compare-saved-row {
    display: grid;
    grid-template-columns: minmax(120px, 1fr) auto minmax(120px, 1fr) auto auto;
    gap: 6px;
    align-items: center;
}
.compare-saved-name,
.compare-saved-select {
    min-width: 0;
}
.compare-saved-empty {
    margin-top: 7px;
    color: var(--muted, #6d756f);
    font-size: 11px;
    line-height: 1.35;
}
.compare-analysis {
    margin-top: 4px;
}
.compare-run {
    flex: 0 0 auto;
    padding: 9px 18px;
    border-radius: 9px;
    border: 1px solid var(--btn-primary-line, rgba(0, 0, 0, 0.2));
    background: var(--btn-primary-bg, #bf5a36);
    color: var(--btn-primary-text, #fff);
    font-size: 14px;
    cursor: pointer;
}
.compare-run:disabled { background: var(--btn-disabled-bg, #ccc); color: var(--btn-disabled-text, #777); cursor: default; border-color: var(--btn-disabled-line, #bbb); }
.compare-run-secondary {
    background: var(--btn-soft-bg, rgba(0, 0, 0, 0.06));
    color: var(--ink, #1f2430);
    border-color: var(--btn-soft-line, rgba(0, 0, 0, 0.12));
}
.compare-run-secondary:hover:not(:disabled) { background: var(--btn-soft-hover, rgba(0, 0, 0, 0.12)); }
.compare-status {
    flex: 1 1 200px;
    min-width: 0;
    font-size: 12px;
    text-align: right;
    color: var(--muted, #6d756f);
}
.compare-status:empty { display: none; }
.compare-filmstrip-area[hidden] { display: none; }
.compare-filmstrip-area { flex: 1 1 auto; min-width: 0; min-height: 0; display: flex; }
.compare-results { margin-top: 16px; padding-bottom: 8px; }
.compare-section-title { font-size: 13px; font-weight: 600; margin: 16px 0 8px; }
.compare-warning {
    margin-top: 12px;
    padding: 10px 12px;
    border-radius: 9px;
    border: 1px solid #d8a657;
    background: rgba(216, 166, 87, 0.16);
    font-size: 12px;
}
.compare-portrait { width: 100%; height: auto; background: var(--field-bg, #fff); border: 1px solid var(--line, rgba(0, 0, 0, 0.1)); border-radius: 10px; }
.compare-portrait__frame { fill: none; stroke: var(--line, rgba(0, 0, 0, 0.1)); }
.compare-portrait__baseline { stroke: var(--muted, #6d756f); stroke-dasharray: 4 4; stroke-width: 1; opacity: 0.6; }
.compare-portrait__line { stroke-width: 1.6; opacity: 0.85; }
.compare-portrait__line.is-dimmed { opacity: 0.12; }
.compare-portrait__point.is-dimmed { opacity: 0.12; }
.compare-grid-scroll {
    max-width: 100%;
    overflow-x: auto;
    border: 1px solid var(--line, rgba(0, 0, 0, 0.08));
    border-radius: 8px;
}
.compare-grid { width: 100%; min-width: 760px; border-collapse: collapse; font-size: 12px; }
.compare-grid th, .compare-grid td { text-align: left; padding: 5px 8px; border-bottom: 1px solid var(--line, rgba(0, 0, 0, 0.08)); }
.compare-grid th { color: var(--muted, #6d756f); font-weight: 600; }
.compare-grid tbody tr:hover { background: var(--btn-soft-bg, rgba(0, 0, 0, 0.05)); }
.compare-grid__name { font-family: var(--mono, monospace); }
.compare-chip { display: inline-block; padding: 1px 8px; border-radius: 999px; color: #fff; background: var(--chip, #6d756f); font-size: 11px; }
.compare-grid__actions { white-space: nowrap; }
.compare-row-actions { display: inline-flex; align-items: center; gap: 4px; }
.compare-link {
    font-size: 11px;
    padding: 2px 7px;
    border-radius: 6px;
    border: 1px solid var(--btn-soft-line, rgba(0, 0, 0, 0.12));
    background: var(--btn-soft-bg, rgba(0, 0, 0, 0.06));
    color: var(--ink, #1f2430);
    cursor: pointer;
}
.compare-link:hover { background: var(--btn-soft-hover, rgba(0, 0, 0, 0.12)); }
.compare-action-menu {
    position: relative;
    display: inline-flex;
}
.compare-action-menu > summary.compare-link {
    display: inline-flex;
    align-items: center;
    list-style: none;
}
.compare-action-menu > summary.compare-link::-webkit-details-marker { display: none; }
.compare-action-menu > summary.compare-link::after {
    content: "▾";
    margin-left: 4px;
    font-size: 9px;
    color: var(--muted, #6d756f);
}
.compare-action-menu[open] > summary.compare-link {
    background: var(--btn-soft-hover, rgba(0, 0, 0, 0.12));
}
.compare-action-menu-panel {
    position: absolute;
    top: calc(100% + 4px);
    right: 0;
    z-index: 3;
    min-width: 92px;
    padding: 4px;
    border: 1px solid var(--line, rgba(0, 0, 0, 0.12));
    border-radius: 8px;
    background: var(--panel-strong, #fff);
    box-shadow: var(--shadow, 0 8px 24px rgba(0, 0, 0, 0.2));
}
.compare-action-menu-item {
    display: block;
    width: 100%;
    padding: 5px 8px;
    border: 0;
    border-radius: 6px;
    background: transparent;
    color: var(--ink, #1f2430);
    font-family: var(--sans, sans-serif);
    font-size: 12px;
    text-align: left;
    cursor: pointer;
}
.compare-action-menu-item:hover,
.compare-action-menu-item:focus-visible {
    background: var(--btn-soft-bg, rgba(0, 0, 0, 0.06));
    outline: none;
}
.compare-row-note {
    font-size: 11px;
    padding: 2px 7px;
    color: var(--muted, #6d756f);
    font-style: italic;
    align-self: center;
    cursor: help;
}
.compare-detail > td { background: var(--help-bg, rgba(0, 0, 0, 0.03)); padding: 10px 8px; }
.compare-detail-status { font-size: 12px; color: var(--muted, #6d756f); }
.compare-detail-grid { display: flex; gap: 18px; flex-wrap: wrap; }
.compare-thumb-block { display: flex; flex-direction: column; gap: 4px; align-items: center; }
.compare-thumb-label { font-size: 11px; color: var(--muted, #6d756f); text-transform: uppercase; letter-spacing: 0.04em; }
.compare-thumb-link {
    display: inline-flex;
    border-radius: 8px;
    color: inherit;
    text-decoration: none;
}
.compare-thumb-link:hover .compare-thumb {
    border-color: var(--accent, #bf5a36);
    box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent, #bf5a36) 28%, transparent);
}
.compare-thumb {
    border: 1px solid var(--line, rgba(0, 0, 0, 0.12));
    border-radius: 8px;
    background: var(--field-bg, #fff);
}
.compare-filmstrip { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; }
.compare-filmstrip[hidden] { display: none; }
.compare-filmstrip-transport {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.compare-filmstrip-btn {
    min-width: 34px;
    padding: 5px 9px;
    border-radius: 7px;
    border: 1px solid var(--btn-soft-line, rgba(0, 0, 0, 0.12));
    background: var(--btn-soft-bg, rgba(0, 0, 0, 0.06));
    color: var(--ink, #1f2430);
    font-size: 13px;
    cursor: pointer;
}
.compare-filmstrip-btn:hover { background: var(--btn-soft-hover, rgba(0, 0, 0, 0.12)); }
.compare-filmstrip-btn:disabled { opacity: 0.5; cursor: default; }
.compare-filmstrip-btn:focus-visible,
.compare-filmstrip-scrubber:focus-visible,
.compare-filmstrip-speed:focus-visible {
    outline: 2px solid var(--focus, #7aa7ff);
    outline-offset: 2px;
}
.compare-filmstrip-scrubber { flex: 1 1 160px; min-width: 120px; accent-color: var(--accent, #bf5a36); }
.compare-filmstrip-counter {
    font-family: var(--mono, monospace);
    font-size: 12px;
    color: var(--muted, #6d756f);
    min-width: 92px;
}
.compare-filmstrip-speed {
    padding: 4px 6px;
    border-radius: 6px;
    border: 1px solid var(--field-border, rgba(0, 0, 0, 0.15));
    background: var(--field-bg, #fff);
    color: var(--field-text, #1f2430);
    font-size: 12px;
}
/* Gallery: boards auto-fit to fill the stage like video-call participants. The
   min keeps ~2 columns at common desktop widths, so four boards read as a 2x2. */
.compare-filmstrip-boards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(46%, 480px), 1fr));
    grid-auto-rows: 1fr;
    gap: 10px 12px;
    align-content: stretch;
    flex: 1 1 auto;
    min-height: 0;
}
.compare-filmstrip-board {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 0;
    min-height: 0;
    padding: 6px;
    border-radius: 10px;
    background: var(--help-bg, rgba(0, 0, 0, 0.03));
    cursor: pointer;
}
.compare-filmstrip-board:focus-visible {
    outline: 2px solid var(--focus, #7aa7ff);
    outline-offset: 2px;
}
/* In the gallery the board slot and its SVG fill the tile (the thumbnail is
   vector, so it scales without loss). */
.compare-filmstrip:not(.compare-filmstrip--speaker) .compare-filmstrip-slot {
    width: 100%;
    height: 100%;
    min-width: 0;
    min-height: 0;
}
.compare-filmstrip:not(.compare-filmstrip--speaker) .compare-thumb {
    width: 100%;
    height: 100%;
    max-width: 100%;
    max-height: 100%;
}
/* Board chrome (name, live count, an expand affordance) overlays the board and
   appears on hover/focus -- and always on the focused hero -- so a resting
   gallery reads as a clean wall of tilings. */
.compare-filmstrip-board-chrome {
    position: absolute;
    left: 6px;
    right: 6px;
    bottom: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 9px;
    border-radius: 7px;
    background: var(--chrome-bg, rgba(16, 20, 24, 0.72));
    color: #f2ede0;
    opacity: 0;
    transition: opacity 0.12s ease;
    pointer-events: none;
}
.compare-filmstrip-board:hover .compare-filmstrip-board-chrome,
.compare-filmstrip-board:focus-visible .compare-filmstrip-board-chrome,
.compare-filmstrip-board.is-hero .compare-filmstrip-board-chrome {
    opacity: 1;
}
.compare-filmstrip-expand { margin-left: auto; font-size: 13px; opacity: 0.85; }
/* The chrome's ✕ drops this board from the run. The chrome itself ignores the
   pointer, so the button opts back in -- but only while the chrome is visible,
   so an invisible ✕ never eats a board click. */
.compare-filmstrip-remove {
    border: none;
    background: none;
    color: inherit;
    font-size: 12px;
    line-height: 1;
    padding: 2px 4px;
    border-radius: 4px;
    cursor: pointer;
    opacity: 0.7;
}
.compare-filmstrip-remove:hover {
    opacity: 1;
    background: rgba(255, 255, 255, 0.16);
}
.compare-filmstrip-board:hover .compare-filmstrip-remove,
.compare-filmstrip-board:focus-visible .compare-filmstrip-remove,
.compare-filmstrip-board.is-hero .compare-filmstrip-remove {
    pointer-events: auto;
}
/* The gallery's trailing ghost tile opens the tiling picker. Speaker view is
   about one board, so the tile only lives in the gallery grid. */
.compare-filmstrip-add {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 0;
    min-height: 0;
    border: 1px dashed var(--line, rgba(0, 0, 0, 0.22));
    border-radius: 10px;
    background: none;
    color: var(--muted, #6d756f);
    font-size: 13px;
    cursor: pointer;
}
.compare-filmstrip-add:hover {
    color: inherit;
    border-color: var(--focus, #7aa7ff);
}
.compare-filmstrip--speaker .compare-filmstrip-add { display: none; }
/* Edit mode: the pointer paints cells, so the cursor says so, hovered cells
   light up, and the chrome becomes interactive so its ⤢ glyph can stay the one
   zoom affordance. */
.compare-filmstrip.is-editing .compare-filmstrip-board { cursor: crosshair; }
.compare-filmstrip.is-editing .compare-thumb polygon:hover {
    stroke: var(--focus, #7aa7ff);
    stroke-width: 0.08;
}
.compare-filmstrip.is-editing .compare-filmstrip-board-chrome {
    pointer-events: auto;
    cursor: default;
}
.compare-filmstrip.is-editing .compare-filmstrip-expand {
    cursor: pointer;
    opacity: 1;
}
/* The hero's toolbelt overlays the top of the focused board: back to the gallery
   on the left, the single fork affordance on the right. */
.compare-hero-toolbelt {
    position: absolute;
    top: 8px;
    left: 8px;
    right: 8px;
    z-index: 3;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    pointer-events: none;
}
.compare-hero-tool {
    pointer-events: auto;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 11px;
    border-radius: 8px;
    border: 1px solid rgba(242, 237, 224, 0.28);
    background: rgba(16, 20, 24, 0.78);
    color: #f2ede0;
    font-family: var(--sans, sans-serif);
    font-size: 12px;
    cursor: pointer;
}
.compare-hero-tool:hover { background: rgba(16, 20, 24, 0.95); }
.compare-hero-tool:disabled { opacity: 0.5; cursor: default; }
.compare-hero-tool:focus-visible {
    outline: 2px solid var(--focus, #7aa7ff);
    outline-offset: 2px;
}
/* Speaker view: the hero fills the stage; the others form a bottom strip. The
   hero spans every column of row 1; the strip boards flow across row 2 as
   uniform tiles, centred, with collapsible empty columns. */
.compare-filmstrip--speaker .compare-filmstrip-boards {
    display: grid;
    grid-template-rows: minmax(0, 1fr) auto;
    grid-template-columns: repeat(auto-fill, 108px);
    justify-content: center;
    align-items: stretch;
    gap: 10px 12px;
    min-height: 0;
}
.compare-filmstrip--speaker .compare-filmstrip-board.is-hero {
    grid-row: 1;
    grid-column: 1 / -1;
    min-height: 0;
}
.compare-filmstrip--speaker .compare-filmstrip-board.is-strip {
    grid-row: 2;
    height: 96px;
}
.compare-filmstrip--speaker .compare-filmstrip-slot {
    width: 100%;
    height: 100%;
    min-width: 0;
    min-height: 0;
}
.compare-filmstrip--speaker .compare-thumb {
    width: 100%;
    height: 100%;
    max-width: 100%;
    max-height: 100%;
}
.compare-filmstrip-label {
    font-size: 11px;
    font-family: var(--mono, monospace);
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.compare-filmstrip-slot {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 96px;
    min-height: 96px;
    font-size: 11px;
    color: var(--muted, #6d756f);
}
.compare-filmstrip-count { font-size: 11px; font-family: var(--mono, monospace); opacity: 0.85; }
/* Live focus pane: a forked, editable board that replaces the hero SVG. Sized
   entirely from its slot (height: 100%, not content), so the canvas it
   contains can never grow the box that in turn bounds the canvas's own fit --
   that circularity was a real bug: a ResizeObserver-driven re-fit (see
   compare-focus-pane.ts) feeding a content-sized container back into itself
   made the pane's size (and hit-testing) jitter indefinitely. */
.compare-focus-pane {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
    height: 100%;
    min-height: 0;
}
.compare-focus-pane-chip {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px 10px;
    padding: 8px 10px;
    border: 1px solid var(--border-warning, #d8a657);
    border-radius: 9px;
    background: var(--bg-warning, rgba(216, 166, 87, 0.16));
}
.compare-focus-pane-info { font-size: 12px; font-weight: 600; color: var(--ink, #1f2430); }
.compare-focus-pane-badge {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 999px;
    background: var(--panel-strong, #fff);
    border: 1px solid var(--line, rgba(0, 0, 0, 0.12));
    color: var(--muted, #6d756f);
}
.compare-focus-pane-palette { display: inline-flex; gap: 4px; flex-wrap: wrap; }
.compare-focus-pane-swatch {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 7px;
    border: 1px solid var(--btn-soft-line, rgba(0, 0, 0, 0.12));
    background: var(--panel-strong, #fff);
    color: var(--ink, #1f2430);
    cursor: pointer;
}
.compare-focus-pane-swatch.is-selected { border-color: var(--accent, #bf5a36); }
.compare-focus-pane-swatch-color {
    width: 11px;
    height: 11px;
    border-radius: 3px;
    border: 1px solid var(--line, rgba(0, 0, 0, 0.2));
}
.compare-focus-pane-actions { display: inline-flex; gap: 6px; margin-left: auto; }
.compare-focus-pane-action {
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 7px;
    border: 1px solid var(--btn-soft-line, rgba(0, 0, 0, 0.12));
    background: var(--panel-strong, #fff);
    color: var(--ink, #1f2430);
    cursor: pointer;
}
.compare-focus-pane-action:hover:not(:disabled) {
    background: var(--btn-soft-bg, rgba(0, 0, 0, 0.06));
}
.compare-focus-pane-action:disabled {
    opacity: 0.45;
    cursor: default;
}
/* The ↶/↷ history buttons carry only a glyph, so they read as square icons. */
.compare-focus-pane-undo,
.compare-focus-pane-redo {
    padding: 4px 8px;
    font-size: 13px;
    line-height: 1;
}
.compare-focus-pane-discard {
    border-color: var(--border-danger, #d08a8a);
    color: var(--text-danger, #a3352d);
}
.compare-focus-pane-viewport {
    display: flex;
    align-items: center;
    justify-content: center;
    /* Fills whatever height remains under the chip -- not content-sized, see
       the .compare-focus-pane comment above. */
    flex: 1 1 auto;
    min-height: 220px;
    padding: 6px;
    border: 1px solid var(--line, rgba(0, 0, 0, 0.1));
    border-radius: 10px;
    background: var(--field-bg, #fff);
}
.compare-focus-pane-canvas { touch-action: none; }
/* Forked boards render their own live canvas in place of the vector thumbnail.
   Once the board isn't the hero (the gallery, or the speaker-view strip) that
   collapses to a compact tile -- just a "live · gen N" badge over the canvas,
   so it still reads like any other tile at a glance. The full chip (palette,
   step/run, discard) only appears once the board is focused as the hero. */
.compare-filmstrip-board:not(.is-hero) .compare-focus-pane {
    position: absolute;
    inset: 0;
    gap: 0;
}
.compare-filmstrip-board:not(.is-hero) .compare-focus-pane-chip {
    position: absolute;
    top: 4px;
    left: 4px;
    z-index: 2;
    padding: 0;
    border: none;
    background: none;
    flex-wrap: nowrap;
}
.compare-filmstrip-board:not(.is-hero) .compare-focus-pane-info,
.compare-filmstrip-board:not(.is-hero) .compare-focus-pane-palette,
.compare-filmstrip-board:not(.is-hero) .compare-focus-pane-actions {
    display: none;
}
.compare-filmstrip-board:not(.is-hero) .compare-focus-pane-badge {
    background: var(--chrome-bg, rgba(16, 20, 24, 0.72));
    color: #f2ede0;
    border: none;
}
.compare-filmstrip-board:not(.is-hero) .compare-focus-pane-viewport {
    position: absolute;
    inset: 0;
    min-height: 0;
    padding: 0;
    border: none;
    border-radius: 0;
    background: transparent;
}
.compare-filmstrip-board:not(.is-hero) .compare-focus-pane-canvas {
    max-width: 100%;
    max-height: 100%;
}
@media (max-width: 640px) {
    .wall-header { align-items: center; }
    /* On a phone the boards want a full column and the stage can scroll. */
    .compare-filmstrip-boards { grid-template-columns: 1fr; grid-auto-rows: minmax(200px, 1fr); }
    .compare-form { grid-template-columns: 1fr; }
    .compare-seed-workspace { grid-template-columns: 1fr; }
    .compare-seedpreview { gap: 10px; }
    .compare-tilings-tools { justify-content: flex-start; flex-basis: 100%; }
    .compare-tilings-search { max-width: none; }
    .compare-tilings-presets { justify-content: flex-start; }
    .compare-tilings { grid-template-columns: 1fr; max-height: 240px; }
    .compare-saved { grid-template-columns: 1fr; }
    .compare-saved-row { grid-template-columns: 1fr; }
    .compare-run { min-width: 136px; }
    .compare-status { flex-basis: 100%; text-align: left; }
    .compare-grid { min-width: 680px; }
}
`;
