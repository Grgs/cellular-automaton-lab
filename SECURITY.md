# Security

## Supported Versions

The public release line is a preview series. Security fixes target the current default branch and the latest tagged preview when practical.

## Reporting A Vulnerability

Please report suspected vulnerabilities privately through GitHub security advisories when available, or by opening a minimal issue that does not include exploit details.

Avoid posting secrets, private file paths, tokens, credentials, or private deployment details in public issues or pull requests.

## Local Guardrails

The repository includes pre-commit checks for common secret and privacy leaks:

```powershell
git config core.hooksPath .githooks
python -m pre_commit run --hook-stage pre-push --all-files
```

The hook-path setting is local to each clone, so run the configuration command
once after cloning. See [docs/TESTING.md](docs/TESTING.md#local-git-guards) for
setup and manual-check details and [docs/MAINTENANCE.md](docs/MAINTENANCE.md) for
guardrail ownership.
