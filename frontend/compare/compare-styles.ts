export const COMPARE_PANEL_STYLES = `
.compare-close:focus-visible,
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
.compare-backdrop {
    position: fixed;
    inset: 0;
    z-index: 70;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    background: rgba(20, 18, 12, 0.45);
}
.compare-backdrop[hidden] { display: none; }
.compare-backdrop--workspace {
    padding: 0;
    background: var(--panel-strong, #fff);
    align-items: stretch;
    justify-content: stretch;
}
.compare-dialog {
    width: min(880px, 96vw);
    max-height: 92vh;
    overflow: auto;
    background: var(--panel-strong, #fff);
    color: var(--ink, #1f2430);
    border: 1px solid var(--line, rgba(0, 0, 0, 0.12));
    border-radius: var(--radius, 16px);
    box-shadow: var(--shadow, 0 18px 40px rgba(0, 0, 0, 0.25));
    padding: 20px 22px;
    font-family: var(--sans, sans-serif);
    scrollbar-gutter: stable;
}
.compare-dialog--workspace {
    width: 100%;
    max-width: none;
    height: 100vh;
    max-height: 100vh;
    border: none;
    border-radius: 0;
    box-shadow: none;
    /* Fill the viewport but keep the content readable by centring it. */
    padding: 18px max(22px, calc((100vw - 1040px) / 2));
}
.compare-dialog--workspace .compare-actions {
    margin-left: 0;
    margin-right: 0;
    padding-left: 0;
    padding-right: 0;
}
.compare-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.compare-title { font-size: 18px; margin: 0; }
.compare-close {
    border: none;
    background: transparent;
    font-size: 24px;
    line-height: 1;
    cursor: pointer;
    color: var(--muted, #6d756f);
}
.compare-close.compare-back {
    border: 1px solid var(--btn-soft-line, rgba(0, 0, 0, 0.12));
    background: var(--btn-soft-bg, rgba(0, 0, 0, 0.06));
    color: var(--ink, #1f2430);
    font-family: var(--sans, sans-serif);
    font-size: 13px;
    line-height: 1;
    padding: 8px 12px;
    border-radius: 8px;
    cursor: pointer;
}
.compare-close.compare-back:hover { background: var(--btn-soft-hover, rgba(0, 0, 0, 0.12)); }
.compare-content { display: contents; }
.compare-intro { color: var(--muted, #6d756f); font-size: 13px; margin: 6px 0 14px; }
/* Stage-first: the synchronized side-by-side leads the page. */
.compare-stage { min-width: 0; }
.compare-stage-main { min-width: 0; }
/* Speaker view splits the stage into the seed rail and the hero board. */
.compare-stage-main.is-speaker {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    flex-wrap: wrap;
}
.compare-stage-main.is-speaker .compare-filmstrip-area {
    flex: 1 1 480px;
    min-width: 0;
}
.compare-seed-rail {
    flex: 0 1 260px;
    min-width: 0;
    padding: 12px;
    border: 1px solid var(--line, rgba(0, 0, 0, 0.1));
    border-radius: 10px;
    background: var(--help-bg, rgba(0, 0, 0, 0.03));
}
.compare-seed-rail[hidden] { display: none; }
.compare-seed-rail-title { font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.compare-seed-rail .compare-seed-workspace {
    grid-template-columns: 1fr;
    margin-top: 0;
    gap: 12px;
}
.compare-seed-rail .compare-seedbits { max-width: none; }
.compare-seed-rail-rerun { width: 100%; margin-top: 12px; }
.compare-seed-rail-hint {
    margin: 10px 0 0;
    font-size: 11px;
    line-height: 1.4;
    color: var(--muted, #6d756f);
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
/* The transport + primary actions dock beneath the stage and stay reachable
   while the configuration disclosures scroll underneath. */
.compare-dock {
    position: sticky;
    bottom: 0;
    z-index: 5;
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 8px;
    padding: 10px 0 12px;
    background: var(--panel-strong, #fff);
    border-top: 1px solid var(--line, rgba(0, 0, 0, 0.12));
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
.compare-actions {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
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
.compare-status { flex: 1 1 auto; min-width: 140px; font-size: 12px; color: var(--muted, #6d756f); }
.compare-live-state {
    margin-top: 10px;
    padding: 8px 10px;
    border-radius: 8px;
    border: 1px solid var(--line, rgba(0, 0, 0, 0.1));
    background: var(--help-bg, rgba(0, 0, 0, 0.03));
    color: var(--muted, #6d756f);
    font-size: 12px;
}
.compare-filmstrip-area[hidden] { display: none; }
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
.compare-filmstrip { margin-top: 4px; }
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
.compare-filmstrip-boards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 14px 16px;
    align-items: start;
}
.compare-dialog--workspace .compare-filmstrip-boards {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}
.compare-dialog--workspace .compare-filmstrip-slot .compare-thumb {
    width: min(100%, 220px);
    height: auto;
}
.compare-filmstrip-board {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    border-radius: 8px;
    cursor: pointer;
}
.compare-filmstrip-board:focus-visible {
    outline: 2px solid var(--focus, #7aa7ff);
    outline-offset: 4px;
}
.compare-filmstrip-board-head {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    width: 100%;
}
/* Speaker view: the focused board becomes the hero, the rest a wrapping strip. */
.compare-filmstrip--speaker .compare-filmstrip-boards {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: flex-start;
    gap: 12px 16px;
}
.compare-filmstrip--speaker .compare-filmstrip-board.is-hero {
    flex: 1 1 100%;
    order: -1;
}
/* Let the hero's slot span the row so the thumb's percentage width can grow. */
.compare-filmstrip--speaker .compare-filmstrip-board.is-hero .compare-filmstrip-slot {
    width: 100%;
}
.compare-filmstrip--speaker .compare-filmstrip-board.is-hero .compare-thumb {
    width: min(100%, 560px);
    height: auto;
}
.compare-filmstrip--speaker .compare-filmstrip-board.is-strip {
    flex: 0 0 auto;
}
.compare-filmstrip--speaker .compare-filmstrip-board.is-strip .compare-thumb {
    width: 120px;
    height: auto;
}
.compare-filmstrip--speaker .compare-filmstrip-board.is-strip .compare-filmstrip-count,
.compare-filmstrip--speaker .compare-filmstrip-board.is-strip .compare-filmstrip-open {
    display: none;
}
.compare-filmstrip-label {
    font-size: 11px;
    color: var(--muted, #6d756f);
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
.compare-filmstrip-count { font-size: 11px; color: var(--muted, #6d756f); font-family: var(--mono, monospace); }
/* Live focus pane: a forked, editable board that replaces the hero SVG. */
.compare-focus-pane {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
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
.compare-focus-pane-action:hover { background: var(--btn-soft-bg, rgba(0, 0, 0, 0.06)); }
.compare-focus-pane-discard {
    border-color: var(--border-danger, #d08a8a);
    color: var(--text-danger, #a3352d);
}
.compare-focus-pane-viewport {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 260px;
    padding: 6px;
    border: 1px solid var(--line, rgba(0, 0, 0, 0.1));
    border-radius: 10px;
    background: var(--field-bg, #fff);
}
.compare-focus-pane-canvas { touch-action: none; }
.compare-seed-rail-fork { width: 100%; margin-top: 8px; }
@media (max-width: 640px) {
    .compare-backdrop { align-items: stretch; padding: 8px; }
    .compare-dialog {
        width: calc(100vw - 16px);
        max-height: calc(100vh - 16px);
        padding: 16px;
    }
    .compare-header { align-items: flex-start; }
    .compare-form { grid-template-columns: 1fr; }
    .compare-seed-workspace { grid-template-columns: 1fr; }
    .compare-seedpreview { gap: 10px; }
    .compare-tilings-tools { justify-content: flex-start; flex-basis: 100%; }
    .compare-tilings-search { max-width: none; }
    .compare-tilings-presets { justify-content: flex-start; }
    .compare-tilings { grid-template-columns: 1fr; max-height: 240px; }
    .compare-saved { grid-template-columns: 1fr; }
    .compare-saved-row { grid-template-columns: 1fr; }
    .compare-actions {
        align-items: stretch;
        gap: 10px;
    }
    .compare-run { min-width: 136px; }
    .compare-status { min-width: 0; }
    .compare-grid { min-width: 680px; }
}
`;
