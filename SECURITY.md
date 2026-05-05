# Security

## Supported Versions

The public `v0.1.x` line is a preview release. Security fixes target the current default branch and the latest tagged preview when practical.

## Reporting A Vulnerability

Please report suspected vulnerabilities privately through GitHub security advisories when available, or by opening a minimal issue that does not include exploit details.

Avoid posting secrets, private file paths, tokens, credentials, or private deployment details in public issues or pull requests.

## Local Guardrails

The repository includes pre-commit checks for common secret and privacy leaks:

```powershell
py -3 -m pre_commit install --hook-type pre-commit --hook-type pre-push
py -3 -m pre_commit run --all-files
```

See [docs/MAINTENANCE.md](docs/MAINTENANCE.md) for guardrail ownership and release-process details.
