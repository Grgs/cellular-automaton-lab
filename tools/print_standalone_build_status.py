from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.e2e.support_runtime_host import standalone_build_status


def main() -> int:
    print(json.dumps(standalone_build_status(ROOT), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
