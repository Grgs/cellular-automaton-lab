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
    padding: 7px 9px;
    border-radius: 8px;
    border: 1px solid var(--field-border, rgba(0, 0, 0, 0.15));
    background: var(--field-bg, #fff);
    color: var(--field-text, #1f2430);
    font-family: var(--mono, monospace);
    font-size: 13px;
}
.compare-tilings-block { margin-top: 14px; }
.compare-tilings-controls { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
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
.compare-tilings-family { display: flex; align-items: center; gap: 6px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted, #6d756f); margin-bottom: 4px; }
.compare-dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.compare-tiling { display: flex; align-items: center; gap: 7px; font-size: 12px; padding: 2px 0; cursor: pointer; }
.compare-actions { display: flex; align-items: center; gap: 14px; margin: 16px 0 4px; }
.compare-run {
    padding: 9px 18px;
    border-radius: 9px;
    border: 1px solid var(--btn-primary-line, rgba(0, 0, 0, 0.2));
    background: var(--btn-primary-bg, #bf5a36);
    color: var(--btn-primary-text, #fff);
    font-size: 14px;
    cursor: pointer;
}
.compare-run:disabled { background: var(--btn-disabled-bg, #ccc); color: var(--btn-disabled-text, #777); cursor: default; border-color: var(--btn-disabled-line, #bbb); }
.compare-status { font-size: 12px; color: var(--muted, #6d756f); }
.compare-results { margin-top: 8px; }
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
.compare-grid { width: 100%; border-collapse: collapse; font-size: 12px; }
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
`;
