"""테스트는 실제 DB 파일을 건드리지 않고, 임시 폴더의 DB 를 쓴다."""

import os
import tempfile
from pathlib import Path

_folder = tempfile.mkdtemp(prefix="planner-test-")
os.environ["PLANNER_DB"] = str(Path(_folder) / "test.db")
