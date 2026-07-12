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
| Compare/Lab routing | Pass | Keep | Deep links and workspace navigation pass in the suite. Shared-board links now display a compact **Shared board** marker while Lab is active, making the restored workspace clear without exposing the long URL. |
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
| Keyboard escape/focus and narrow-viewport usability | Pass | Keep | Existing keyboard browser coverage remains green. The shared-board route marker is announced through a live region and is hidden below the narrow-layout breakpoint; browser QA at 800px confirmed the header does not overflow. |
| Visual clarity across themes and topology families | Pass in browser rendering coverage | Keep with periodic review | Rendering and palette checks pass. Continue using the repository render-review tool when visual changes affect canvas output. |

## Follow-up

1. Repeat the keyboard-only and narrow-desktop observation pass when changing
   the shell header, route switcher, or drawer layout. Record only concrete,
   reproducible friction points here.
