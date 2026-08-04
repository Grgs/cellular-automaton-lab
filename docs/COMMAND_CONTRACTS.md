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

`backend/application_commands/contracts.py` is the executable inventory. It owns each semantic id, transport method/path, backend payload name, and frontend request/result expression. `frontend/application-command-contract.ts` is generated from that registry and also exports the transport-path map used by the standalone worker protocol.

After changing the registry, regenerate the frontend surface with:

```powershell
python -m tools repo command-contract --write
```

`python -m tools repo generated-check` compares the complete generated file, including request types, result types, and paths. A matching command-id set alone is not sufficient.

## Boundary rules

- The dispatcher owns request normalization, public validation, domain invocation, and transport-neutral result selection.
- Flask owns session lookup, HTTP status codes, JSON response encoding, server bootstrap/meta, background stepping, and persistence scheduling.
- The standalone host owns initialization/restore, worker envelopes, JS tick timers, and browser-local persistence emission.
- Both transports expose the same structured public error fields through `BackendRequestError`.
- `tests/api/test_command_parity.py` keys its scenario table by semantic command. Every registry entry must have a valid scenario, and every command that accepts a payload must have an invalid scenario. The same test verifies Flask's default and session routes, executes both transports, and normalizes transport envelopes plus the host-local `state_epoch` before comparing domain results.

To add a command, update the Python inventory and dispatcher, add its registry-keyed parity scenarios, regenerate the TypeScript contract, and update payload contracts or runtime decoders when applicable. CI fails when the dispatcher, either Flask route family, generated frontend contract, or parity inventory is incomplete.
