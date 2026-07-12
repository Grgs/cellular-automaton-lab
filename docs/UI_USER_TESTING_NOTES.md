# UI User-Flow Test Notes

## Session

- Date: 2026-07-12
- Host coverage: local Flask server and standalone browser runtime
- Automated user-flow coverage: `npm run test:e2e:playwright`
- Result: **96 tests passed** in 359.723 seconds
- Manual exploration: comparison wall readiness and workspace navigation in the
  local app

## Results

| Area | Result | Recommendation | Evidence / notes |
| --- | --- | --- | --- |
| First-run comparison wall and autoplay | Pass | Keep | Bare wall bootstrap and comparison readiness are covered by browser tests. Manual review reached the filmstrip-ready state with no alert. |
| Compare/Lab routing | Pass with follow-up | Investigate | Deep links and workspace navigation pass in the suite. During manual exploration, an existing `#share=` state produced a very long URL after selecting Lab; repeat this flow from a truly fresh browser profile to judge whether that state transition is understandable to new users. |
| Configuration sheet, tabs, and tiling selection | Pass | Keep | Covered by overlays/editor and rules/picker flows. |
| Rule compatibility and picker behavior | Pass | Keep | Covered by rules/picker suite, including supported-family constraints. |
| Comparison run and playback controls | Pass | Keep | Covered by wall, playback, and editor browser flows. |
| Gallery, speaker view, edit mode, and live forks | Pass | Keep | Covered by gallery selection, mid-timeline editing, fork persistence, discard/rejoin, and undo/redo flows. |
| Lab editor tools and simulation controls | Pass | Keep | Covered by canvas editing, run/step, overlays, and editor tests. |
| Regular, periodic, and aperiodic topology controls | Pass | Keep | Covered by topology/persistence suite and representative aperiodic rendering cases. |
| Rules, multistate presets, and showcase flows | Pass | Keep | Covered by rules/picker and pattern/showcase suites. |
| Pattern import, export, copy, paste, and validation | Pass | Keep | Covered by pattern round-trip/import/export browser cases. |
| Share links, saved runs, saved tiling sets, reload, and server restart | Pass | Keep | Covered by topology/persistence suite. |
| Standalone loading, saved state, run-link restore, and startup error | Pass | Keep | Covered by standalone runtime suite. |
| Keyboard escape/focus and narrow-viewport usability | Not fully observed manually | Investigate | No failure was reported by the automated suite, but a dedicated keyboard-only and narrow-desktop observation pass remains useful for qualitative clarity and focus-order decisions. |
| Visual clarity across themes and topology families | Pass in browser rendering coverage | Keep with periodic review | Rendering and palette checks pass. Continue using the repository render-review tool when visual changes affect canvas output. |

## Follow-up

1. Open the app in a brand-new browser profile and assess the transition from a
   shared board URL to Lab. Confirm that the visible route and workspace state
   communicate what was restored before changing UI copy or behavior.
2. Schedule a short keyboard-only/narrow-desktop observation pass before any
   accessibility or layout redesign. Record only concrete, reproducible
   friction points here.
