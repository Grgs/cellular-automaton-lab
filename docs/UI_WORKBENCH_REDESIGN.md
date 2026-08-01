# Compare Workbench UI Redesign

## Locked program decisions

The #261 redesign ships as six focused pull requests. Issue #63 is explicitly
out of scope. Every phase starts from the latest `origin/main`; experimental
branches remain available for reference, but their changes are ported
selectively rather than cherry-picked wholesale.

The visual direction is a unified warm-technical system. Compare and Lab share
the root semantic theme tokens, while the warm tile palette remains stable
across themes. Desktop keeps Compare/Lab navigation visible. Narrow layouts use
compact workspace navigation. Theme controls live only in Preferences.

Main must remain releasable after every phase. There is no feature flag or
all-at-once rollout, and there are no backend or HTTP API changes in this
program.

## Phase 1 — Shell, menus, and themes (#262)

- At widths of 720px and above, show Compare/Lab as an always-visible segmented
  switcher with the active route marked.
- Below 720px, place workspace navigation inside the app menu.
- Limit the app menu to navigation where required and global Preferences.
  Contextual commands stay inside their workspace.
- Use a real disclosure button and controlled panel rather than `<details>`.
  Support Escape, outside-click dismissal, focus restoration, inline-end
  positioning, and viewport containment.
- Remove the header theme icon. Preferences offers a Light/Dark/Follow System
  radio group and applies selections immediately.
- Add `ThemePreference = "system" | "light" | "dark"` read/apply helpers.
  Existing stored `light`/`dark` values remain compatible. System stores no
  explicit value and follows live OS changes.
- Make the root background, panel, text, border, accent, focus, form, and button
  tokens authoritative in Compare. Preserve the warm tile palette.
- Reopen #262 and close it only after the shell and full Compare workspace
  visibly follow both themes.

## Phase 2 — Editable run summary and Rule control (#263)

- Move the run summary out of Setup into an always-visible toolbar above the
  wall.
- Keep the canonical Rule select directly visible; do not mirror it.
- Make Seed and Tilings summary buttons open the correct Setup tab and focus the
  relevant editor or search.
- Show current/stale configuration state and a truthful Run/Update action.
- Keep the compact toolbar usable at 390px without horizontal scrolling.

## Phase 3 — Resizable Setup and Inspector (#264)

- Extend the layout controller with pointer- and keyboard-operable vertical
  separators.
- Defaults are Setup 250px and Inspector 270px. Minimums are 220px/240px;
  maximums are 420px/440px; preserve at least 400px for the wall.
- Arrow keys resize by 10px, Shift+Arrow by 40px, and Home/End select the
  minimum/maximum.
- Persist widths and collapsed states under
  `cellular-automaton-lab.compare-layout.v1`, clamping invalid or obsolete
  values on load.
- Below 960px, hide splitters and retain exclusive overlay drawers without
  changing stored desktop widths.
- Add “Reset Compare layout” to Preferences.

## Phase 4 — Tabs and selected-tiling actions (#265)

- Manually port useful behavior from `9eef1d6` and `a9711f8`.
- Render Setup/Tilings/Help/Saved as a connected tab group with roving keyboard
  focus and an unmistakable selected state.
- Remove per-board removal controls. Selection identifies the target; Inspector
  provides Replace selected and Remove selected with the tiling name in
  labels/tooltips.
- Visually group Navigate, Edit, Share, and destructive actions. Keep Remove
  separated and disabled with an explanation when unsafe.
- Keep the selected-tiling toolbelt mounted through gallery/speaker transitions
  and retain visible labels instead of icon-only controls.

## Phase 5 — Wall undo and redo (#266)

- Add a session-only history controller capped at 20 successful add, remove, and
  replace entries.
- Store immutable before/after snapshots containing configuration, ordered
  filmstrip data, result key, selection/focus, frame index, and play state.
- Capture add/replace only after the authoritative async result installs.
  Failed, cancelled, and stale operations add no history.
- Undo/redo cancels queued work, invalidates active operation tickets, restores
  locally, and disposes incompatible live forks.
- Provide a status snackbar with Undo and, after undo, Redo.
- Support Ctrl/Cmd+Z, Ctrl/Cmd+Shift+Z, and Ctrl+Y while yielding to inputs,
  selects, textareas, contenteditable controls, and already-handled events.
- Clear history on reload, saved/deep-linked run replacement, or non-membership
  configuration changes. Preserve it through playback, focus changes, and
  Compare/Lab round trips.
- Add dedicated `CompareWallSnapshot`, `CompareWallHistoryEntry`, and history
  controller interfaces. Saved runs and tiling sets remain separate from
  layout/history storage.

## Phase 6 — Regression gate and umbrella completion (#267/#261)

- Consolidate the accumulated browser journeys as the #261 release gate.
- Close #261 only after every child issue merges and the full matrix passes.

## Acceptance matrix

Every phase adds focused Vitest coverage, then runs frontend typecheck, build,
tests, focused server and standalone Playwright journeys, and the change-aware
PR gate. Accumulated browser coverage includes:

- desktop 1280×800 and narrow 390×800;
- computed light/dark colors across shell, wall, Setup, Inspector, dock,
  overlays, fields, and menus;
- open-menu rectangles within the viewport and
  `document.documentElement.scrollWidth <= innerWidth`;
- keyboard menu/dialog behavior and focus restoration;
- editable summary destinations and Rule updates;
- pointer/keyboard splitter resizing, clamping, persistence, reload, reset, and
  narrow overlays;
- tab semantics and explicitly scoped selected-tiling actions;
- add/remove/replace → undo → redo, including order, selection, playback,
  pending requests, and text-input shortcut yielding;
- Compare-to-Lab round trips and no new console errors.

## Delivery and continuation checkpoints

Use one Codex task, branch, and PR per phase:

1. `fix/ui-shell-theme-foundation`
2. `feat/compare-editable-summary`
3. `feat/compare-resizable-panels`
4. `feat/compare-action-scope`
5. `feat/compare-wall-history`
6. `test/compare-workbench-regression`

Update this document in every PR. After a phase merges, add a concise #261
checkpoint comment containing the merged PR/SHA, tests passed, remaining phase,
and known risks.

After any context compaction, first read the repository instructions, this
document, the latest #261 checkpoint, `git status`, and the current branch
log/diff. Do not rediscover or reimplement completed phases.

| Phase                    | Issue     | Branch                              | PR            | Merge SHA                                  | Verification                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Next phase                                                                         |
| ------------------------ | --------- | ----------------------------------- | ------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| 1 — Shell, menus, themes | #262      | `fix/ui-shell-theme-foundation`     | #269 (merged) | `d2d99d65bac3c0216730c3a27883ff2f653e5438` | Full local PR gate passed (575 frontend tests and 140 Playwright journeys), plus focused desktop/narrow shell, menu, theme, and Compare↔Lab checks                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Phase 2 started fresh from the merged `origin/main`                                |
| 2 — Editable summary     | #263      | `feat/compare-editable-summary`     | #270 (merged) | `3c1e03dc70772ae4d8295385ff92b6eff43feda6` | 575 frontend tests; focused server and freshly built standalone summary journeys at 1280×800 and 390×800; canonical Rule, Seed/Tilings focus, current/stale Run/Update states, themes, overflow, console, and Compare↔Lab checks; the 142-journey browser matrix exposed and verified the picker/dock overlap fix; focused bundle/catalog checks passed                                                                                                                                                                                                                                                   | Phase 3 started fresh from the merged `origin/main`                                |
| 3 — Resizable panels     | #264      | `feat/compare-resizable-panels`     | #271 (merged) | `d717b45876e728e5c820473d4ce7e82936c5c98e` | 584 frontend tests and 144 Playwright journeys; frontend/Python typing, lint, formatting, server/standalone builds, bundle budgets, catalog checks, focused desktop/narrow splitter, persistence, reset, overlay, theme, overflow, Compare↔Lab, and console checks; practical screenshot review                                                                                                                                                                                                                                                                                                           | Phase 4 started fresh from the merged `origin/main`                                |
| 4 — Action scope         | #265      | `feat/compare-action-scope`         | #272 (merged) | `c14d220441c7fa108c05fbb7c372867395e7758e` | Full CI and Supply Chain Audit passed; 586 frontend tests plus focused server/standalone selected-action journeys passed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Phase 5 started fresh from the merged `origin/main`                                |
| 5 — Wall history         | #266      | `feat/compare-wall-history`         | #279 (merged) | `5492ac1c5d3fb59c894374445ad8a32fd2906d8d` | The single change-aware gate passed privacy, Python lint/format/typecheck, frontend lint/typecheck/build, all 600 frontend tests, the standalone build and bundle budgets, and full tiling validation/verification. Focused history/controller/panel coverage includes async capture, failure/cancellation/staleness, exact order/selection/focus/frame/play restoration, 20-entry eviction, clearing, route retention, snackbar actions, shortcut yielding, and superseded preview loads. The focused wall-history journey passes in server and freshly built standalone Chromium at 1280×800 and 390×800, and the server-only pending-request cancellation journey passes with clean console/page-error checks. | Phase 6 started fresh from the merged `origin/main` |
| 6 — Regression gate      | #267/#261 | `agent/compare-browser-regressions` | #280 (merged) | `93e8e53b6a700b14edf70bb3b7d83d3fb50abf16` | The named `compare_workbench` gate passed all 10 server/standalone journeys, covering shell navigation/preferences and themes, editable summary/Rule behavior, resizable desktop and narrow panels, tabs and selected actions, removal with undo/redo, Compare-to-Lab handoffs, overflow, and console/page errors. The full local PR gate also passed privacy/secret checks, Python/frontend lint and typecheck, 605 frontend tests, builds and bundle budgets, tiling validation/reference verification, and all 149 Playwright tests. Documentation links passed separately. | Program complete; close #261                                                       |

### Program completion checkpoint

All six Compare workbench phases have merged and child issues #262–#267 are
closed. The final regression gate merged in PR #280 as
`93e8e53b6a700b14edf70bb3b7d83d3fb50abf16` after the focused 10-journey gate,
the 605-test frontend suite, and the full 149-test Playwright matrix passed.

Issue #261 can be closed as completed. Issue #63 remains out of scope.
