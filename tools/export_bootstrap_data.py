from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.bootstrap_data import build_bootstrap_payload
from backend.dev_server import APP_NAME


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: py -3 tools/export_bootstrap_data.py <output-path>")

    output_path = Path(sys.argv[1]).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_bootstrap_payload({"app_name": APP_NAME})
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
