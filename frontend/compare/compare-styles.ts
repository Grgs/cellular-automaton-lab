export const COMPARE_PANEL_STYLES = `
.compare-toggle {
    position: fixed;
    right: 16px;
    bottom: 16px;
    z-index: 60;
    padding: 10px 14px;
    border-radius: 999px;
    border: 1px solid var(--btn-primary-line, rgba(0, 0, 0, 0.2));
    background: var(--btn-primary-bg, #bf5a36);
    color: var(--btn-primary-text, #fff);
    font-family: var(--sans, sans-serif);
    font-size: 13px;
    cursor: pointer;
    box-shadow: var(--shadow, 0 8px 24px rgba(0, 0, 0, 0.2));
}
.compare-toggle:hover { background: var(--btn-primary-hover, #a44928); }
.compare-toggle:focus-visible,
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
.compare-intro { color: var(--muted, #6d756f); font-size: 13px; margin: 6px 0 14px; }
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
.compare-tilings-controls { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.compare-tilings-summary { font-size: 12px; color: var(--muted, #6d756f); margin-right: auto; }
.compare-mini {
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 7px;
    border: 1px solid var(--btn-soft-line, rgba(0, 0, 0, 0.12));
    background: var(--btn-soft-bg, rgba(0, 0, 0, 0.06));
    color: var(--ink, #1f2430);
    cursor: pointer;
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
.compare-tilings-group { min-width: 0; }
.compare-tilings-family { display: flex; align-items: center; gap: 6px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted, #6d756f); margin-bottom: 4px; }
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
.compare-actions {
    position: sticky;
    bottom: -20px;
    z-index: 2;
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 16px -22px -20px;
    padding: 12px 22px 16px;
    border-top: 1px solid var(--line, rgba(0, 0, 0, 0.1));
    background: var(--panel-strong, #fff);
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
.compare-status { flex: 1 1 auto; min-width: 140px; font-size: 12px; color: var(--muted, #6d756f); }
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
.compare-row-actions { display: inline-flex; gap: 4px; }
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
    .compare-tilings { grid-template-columns: 1fr; max-height: 240px; }
    .compare-actions {
        bottom: -16px;
        align-items: stretch;
        gap: 10px;
        margin: 16px -16px -16px;
        padding: 10px 16px 14px;
    }
    .compare-run { min-width: 136px; }
    .compare-status { min-width: 0; }
    .compare-grid { min-width: 680px; }
}
`;
