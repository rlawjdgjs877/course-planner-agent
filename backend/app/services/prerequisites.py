"""컴퓨터학부 전공 소개 페이지의 선후수 흐름으로 '먼저 들으면 좋은 과목'을 확인한다.

자료(data/prerequisites.json)는 학과가 안내하는 권장 순서다. 학칙상 수강 제한은 아니므로
막지 않고, 시간표 점수를 깎고 경고로 알린다. 프론트엔드(frontend/app/lib/data/prerequisites.json)와 같은 파일이다.

흐름의 한 단계에 '자료구조 / 자료구조응용'처럼 여러 과목이 있으면 그중 하나만 들었으면 된다.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).parent.parent / "data" / "prerequisites.json"


def normalize(name: str) -> str:
    """띄어쓰기, 로마 숫자 표기 차이를 없앤다."""
    return re.sub(r"\s+", "", name).replace("Ⅰ", "I").replace("Ⅱ", "II")


@lru_cache(maxsize=1)
def _chains() -> list[dict]:
    return json.loads(DATA.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _requirements() -> dict[str, list[tuple[str, ...]]]:
    """과목명 → 먼저 들어야 하는 단계 목록. 단계마다 '이 중 하나' 과목들."""
    result: dict[str, list[tuple[str, ...]]] = {}
    for chain in _chains():
        stages = [tuple(normalize(name) for name in stage.split(" / ")) for stage in chain["stages"]]
        for previous, stage in zip(stages, stages[1:]):
            for name in stage:
                if previous not in result.setdefault(name, []):
                    result[name].append(previous)
    return result


def display(stage: tuple[str, ...]) -> str:
    return " 또는 ".join(stage)


def missing(course_name: str, completed_names: set[str]) -> list[tuple[str, ...]]:
    """이 과목 전에 들으면 좋은데 이수 기록이 없는 단계들. completed_names 는 normalize 한 이름."""
    return [
        stage
        for stage in _requirements().get(normalize(course_name), [])
        if not any(name in completed_names for name in stage)
    ]


def requirements_of(course_name: str) -> list[tuple[str, ...]]:
    return list(_requirements().get(normalize(course_name), []))
