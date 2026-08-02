# Application Command Contracts

Flask and the standalone Pyodide runtime share one transport-neutral command layer in `backend/application_commands/`. HTTP and worker paths select commands, but paths are not their internal identity.

## Shared inventory

| Command | Transport path | Result | Mutates state |
|---|---|---|---|
| `state.get` | `/api/state` | snapshot | no |
| `rules.list` | `/api/rules` | rules | no |
| `compare.run` | `/api/compare` | comparison | no |
| `filmstrip.run` | `/api/compare/filmstrip` | filmstrip | no |
| `topology.preview` | `/api/topology/preview` | topology preview | no |
| `simulation.start` | `/api/control/start` | snapshot | yes |
| `simulation.pause` | `/api/control/pause` | snapshot | yes |
| `simulation.resume` | `/api/control/resume` | snapshot | yes |
| `simulation.step` | `/api/control/step` | snapshot | yes |
| `simulation.reset` | `/api/control/reset` | snapshot | yes |
| `simulation.configure` | `/api/config` | snapshot | yes |
| `cell.toggle` | `/api/cells/toggle` | cell delta | yes |
| `cell.set` | `/api/cells/set` | cell delta | yes |
| `cells.set_many` | `/api/cells/set-many` | cell delta | yes |

`backend/application_commands/contracts.py` is the executable inventory. `frontend/application-command-contract.ts` is its TypeScript request/result map, and `tests/unit/test_payload_contracts.py` requires the two command-id sets to match.

## Boundary rules

- The dispatcher owns request normalization, public validation, domain invocation, and transport-neutral result selection.
- Flask owns session lookup, HTTP status codes, JSON response encoding, server bootstrap/meta, background stepping, and persistence scheduling.
- The standalone host owns initialization/restore, worker envelopes, JS tick timers, and browser-local persistence emission.
- Both transports expose the same structured public error fields through `BackendRequestError`.
- `tests/api/test_command_parity.py` runs representative valid and invalid requests through both targets. It normalizes transport envelopes and the host-local `state_epoch` before comparing domain results.

Do not add a command to only one dispatcher. Add it to the Python inventory, TypeScript map, payload contracts, runtime decoders when applicable, and parity coverage together.
