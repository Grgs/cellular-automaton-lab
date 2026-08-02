# Comparison Wall

The comparison wall is the app's landing view. It projects one shared seed and rule onto several tilings, then plays every result on one clock so differences in local neighborhood are easy to see.

Open the [standalone demo](https://grgs.github.io/cellular-automaton-lab/) or visit the bare URL of a local server. On a first visit, the wall loads a curated four-tiling demo and rests on a lively frame when reduced motion is enabled.

## Configure a run

The setup strip names the seed, rule, selected tilings, and whether the current wall matches that configuration. Use its actions or the dock to change the run:

- **Seed** chooses a named shape or a custom bit pattern.
- **Rule** lists topology-universal rules suitable for a multi-family comparison.
- **Tilings** opens the searchable visual picker. Unsupported or duplicate choices are disabled.
- **Setup** contains traversal, wall generations, analysis steps, grid size, and the bit-level seed pad.

Every selected board starts from the same seed, rule, traversal, frame count, and grid-size policy. The backend rejects incompatible combinations even when a request bypasses the UI.

## Gallery and speaker view

**Gallery** shows every selected board at once. The boards evolve in lockstep and share play, pause, step, scrub, and speed controls. Add, replace, or remove tilings without losing the ordering of the survivors.

Click a board to enter **speaker view**. The selected board becomes the hero while the others move into a thumbnail strip. From the hero you can:

- return to the wall
- open that exact generation in the Lab
- replace or remove the selected tiling
- fork the current generation into a live editable board

Press Escape to peel back from an open sheet or analysis overlay, then from speaker view to the gallery.

## Edit and fork

Use the dock's edit control to make wall cells clickable.

- At generation 0, painting edits the shared seed. The new bits are projected onto every board immediately, followed by a debounced rerun.
- At a later generation, painting automatically forks that board from the visible frame and carries the stroke into the new live session.

A live fork can be painted with brush sizes 1–3, stepped, run, undone, and redone while the rest of the wall keeps looping. **Discard** restores the synchronized filmstrip board. **Run wall from here** turns the fork's current cells into the shared generation-0 seed and reruns all selected tilings.

Multiple forks can remain alive across gallery and speaker view. The standalone demo caps concurrent forks at two because every fork boots its own Python runtime; the server build uses ordinary backend sessions.

## Analyze a comparison

Open **Analysis** from the dock to run the same seed to a fixed horizon. The result includes:

- a normalized population portrait, `live(t) / live(0)`, grouped by tiling family
- cell count and initial/final population for every tiling
- end-state classification
- actions to open or copy the beginning and ending board states as normal share links

Analysis is calculated on demand and does not disturb the synchronized wall playback.

## Save and share

**Copy run link** creates a `#/compare&run=v1.<base64url-json>` URL. Opening it restores the setup without automatically starting work or playback.

Saved runs and saved tiling sets use browser `localStorage`, so they work in both the Flask app and standalone demo but remain local to the current browser and device. Run links are the portable format.

## Routes and limits

- A bare URL opens the comparison wall.
- `#/lab` opens the single-board editor.
- A bare `#share=` board link also opens the Lab.
- The legacy `#/compare` route still opens the wall.
- `&focus=<geometry>` deep-links to a selected board in speaker view.

Filmstrips intentionally cap the number of tilings, frame count, and per-board work to keep interaction responsive. The wall compares one shared seed/rule configuration; use live forks or the Lab when boards need independent state.
