# UI User-Flow Test Plan and Findings

## Purpose

Evaluate the application as a first-time and returning user would: discover
each feature, complete its main task, recover from a mistake where relevant,
and decide whether the UI should be kept or changed. This complements the
automated browser suites; it is an exploratory usability record, not a test
pass/fail report.

## How to run a session

1. Start with a clean browser profile or clear only this app's site data.
2. Use a normal desktop viewport first. Repeat the highest-risk flows at a
   narrow desktop width and with keyboard-only navigation where practical.
3. Follow the scenarios below without reading implementation details while
   operating the app. Capture a screenshot or reproducible route for every
   issue.
4. Fill in the session log immediately after each scenario. Mark a UI element
   **Keep** only when users can find, understand, and successfully use it
   without unexpected side effects.
5. Retest any proposed UI change using the affected scenario plus its listed
   automated suite.

Use the local server for the complete feature pass, then repeat the
standalone-specific scenarios against the static build. Before a fresh local
pass, run `python -m tools repo cleanup`, `npm run build:frontend`, and start
`py -3 .\app.py`.

## Decision rubric

| Recommendation | Use when |
| --- | --- |
| Keep | The control is discoverable, clear, responsive, and produces the expected durable result. |
| Keep with copy/polish | The workflow works, but wording, feedback, placement, or affordance causes hesitation. |
| Change | A typical user cannot predict the result, complete the task, or recover confidently. |
| Investigate | The observation needs another user, viewport, topology, or host before deciding. |

Severity: **P0** blocks the primary task or loses work; **P1** causes major
confusion or a misleading result; **P2** is a noticeable friction point;
**P3** is cosmetic or minor clarity work.

## Scenario matrix

| ID | User goal and walkthrough | Expected user-visible result | Evidence / regression suite |
| --- | --- | --- | --- |
| U01 | Arrive at a bare URL as a new user. Identify what is running and how to begin. | The comparison wall appears, the curated demo is understandable, and the next meaningful action is evident. | Screenshot; `overlays_and_editor` |
| U02 | Use **Compare** and **Lab** (including `#/lab` deep link and return to wall). | Navigation labels, active state, and back/forward behavior make the two workspaces distinct. | Route and screenshot; `overlays_and_editor` |
| U03 | Open the configuration sheet; visit Setup, tiling selection, Analysis, Help, and saved-content tabs. | The sheet opens predictably, tabs explain their purpose, and close/reopen preserves a comprehensible state. | Screenshot; `overlays_and_editor` |
| U04 | Choose a rule, search/filter tilings, add/remove tilings, and try an incompatible pairing. | Picker feedback explains availability and selection; additions/removals are visible and reversible. | `rules_and_picker` |
| U05 | Configure a seed, grid/frame settings, then run a comparison. | The user can tell what settings apply, when work is underway, and when the wall represents the requested run. | Screenshot; relevant server suite |
| U06 | Use play, pause, step, scrub, and speed controls. | Generation and playback state are legible; controls do exactly one intuitive thing and retain context. | `overlays_and_editor` |
| U07 | In gallery, identify a board, zoom it to speaker view, return with Escape, and remove a board. | Board identity is discoverable, focus is obvious, Escape is safe, and destructive removal has adequate feedback. | `overlays_and_editor` |
| U08 | Turn on edit mode at generation 0; paint and undo/redo. Then paint at a later generation. | The user understands whether they edit the shared seed or a fork, sees the change immediately, and can recover a stroke. | `overlays_and_editor` |
| U09 | Fork a speaker board, edit it, switch layouts, discard it, and run the wall from the fork. | Fork state is clearly separate from the wall; persistence, discard, and rejoin actions have unsurprising outcomes. | `overlays_and_editor` |
| U10 | In Lab, paint with brush, line, rectangle, and fill; undo/redo and reset. | Tools communicate selection and scope; canvas actions hit the intended cells; recovery is dependable. | `overlays_and_editor` |
| U11 | Switch among square, periodic mixed, and aperiodic tilings; alter patch depth or construction options where shown. | Controls appear only when relevant, changes render promptly, and the board remains understandable at each topology. | `topology_and_persistence` |
| U12 | Select rules across supported families and use a multistate/showcase preset. | Rule labels, disabled choices, palettes, and state behavior are understandable without domain knowledge. | `rules_and_picker`, `pattern_and_showcase` |
| U13 | Export/copy a painted pattern, clear/reset, then import/paste it. Try malformed input. | The round trip preserves expected cells; success/error feedback is actionable and does not silently replace work. | `pattern_and_showcase` |
| U14 | Copy a board/share link and a comparison run link; open each in a clean tab. | The link restores the advertised context and clearly distinguishes board sharing from comparison-run sharing. | `topology_and_persistence` |
| U15 | Save, rename if offered, restore, and remove a tiling set/run. Reload the page. | Saved data is clearly local, survives reload as promised, and removal cannot be mistaken for navigation. | `topology_and_persistence` |
| U16 | Reload after changing a board and restart the local server if applicable. | Persisted state returns accurately with no stale or ambiguous loading state. | `topology_and_persistence` |
| U17 | Repeat U01, U14, and U15 in the standalone build, including a deliberate worker startup failure if practical. | The standalone experience communicates loading/errors and preserves browser-local data as documented. | `standalone_runtime` |
| U18 | Keyboard-only pass over header, dock, sheet, picker, dialogs, and visible controls; test Escape and focus return. | Tab order, focus indication, names, and keyboard escape/recovery are usable. | Manual notes and screenshots |
| U19 | Visual clarity pass: light/dark themes if available; square, mixed, and aperiodic boards; narrow desktop width. | Text, selected states, canvas contrast, overlays, and controls remain legible without clipping or overlap. | Screenshots; `python -m tools browser review` for representative topology renders |

## Session log

Create one block per scenario execution. Keep unresolved findings in this file
until a product decision is made; move accepted implementation work into the
normal issue/task tracker if one is selected later.

### Session metadata

- Date/time:
- Tester:
- Host: server / standalone
- Browser and viewport:
- Starting state: clean / returning / shared link / other
- Build or commit:

### Findings

| Scenario | Outcome | What the user expected vs. what happened | Evidence | Severity | Recommendation | Follow-up / owner | Retest result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| U01 | Not run |  |  |  |  |  |  |
| U02 | Not run |  |  |  |  |  |  |
| U03 | Not run |  |  |  |  |  |  |
| U04 | Not run |  |  |  |  |  |  |
| U05 | Not run |  |  |  |  |  |  |
| U06 | Not run |  |  |  |  |  |  |
| U07 | Not run |  |  |  |  |  |  |
| U08 | Not run |  |  |  |  |  |  |
| U09 | Not run |  |  |  |  |  |  |
| U10 | Not run |  |  |  |  |  |  |
| U11 | Not run |  |  |  |  |  |  |
| U12 | Not run |  |  |  |  |  |  |
| U13 | Not run |  |  |  |  |  |  |
| U14 | Not run |  |  |  |  |  |  |
| U15 | Not run |  |  |  |  |  |  |
| U16 | Not run |  |  |  |  |  |  |
| U17 | Not run |  |  |  |  |  |  |
| U18 | Not run |  |  |  |  |  |  |
| U19 | Not run |  |  |  |  |  |  |

## Completion criteria

- Every scenario has at least one server-host result; U17 has a standalone result.
- Each finding has evidence, severity, and a keep/change/investigate recommendation.
- P0/P1 items have a reproduction and a proposed next action before UI decisions are finalized.
- The relevant automated browser suite passes after any UI change.
