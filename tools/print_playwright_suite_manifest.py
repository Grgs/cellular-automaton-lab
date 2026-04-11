from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.e2e.playwright_suite_support import playwright_suite_manifest_json


def main() -> int:
    print(playwright_suite_manifest_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
