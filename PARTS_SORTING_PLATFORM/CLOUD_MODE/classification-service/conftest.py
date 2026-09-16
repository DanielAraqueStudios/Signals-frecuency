"""Makes the repo-root-level `shared` package (../../shared) importable
when running this service's tests or app standalone, matching how the
Dockerfile's build context and COPY layout expose it in the built image."""

import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
