"""선수과목(권장 이수 순서) 확인.

자료: app/data/prerequisites.json (frontend/app/lib/prerequisites.ts 의 사슬을 옮긴 것, 원본은 prerequisites.pdf).
사슬마다 단계가 있고, 'A / B' 처럼 한 단계에 대체 과목이 여럿일 수 있다.

해석: 선수과목 안내는 '권장 이수 순서'라서 학칙상 수강 제한은 아니다. 여기서는
- 과목이 들어 있는 사슬 중 하나라도 바로 앞 단계(대체 과목 중 하나)를 이수했으면 충족,
- 어느 사슬에서든 첫 단계이거나 사슬에 없는 과목은 확인하지 않는다,
- 앞 단계를 같은 학기 시간표에 함께 넣었으면 '동시 수강'(concurrent)으로 따로 알린다.
'공통' 사슬은 모든 학생에게, 'AI'·'플랫폼SW' 사슬은 그 트랙(ai, platform) 학생에게만 적용한다.
"""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Iterable

DATA = Path(__file__).resolve().parent.parent / "data" / "prerequisites.json"
SOURCE = "prerequisites.pdf"
NOTE = "선수과목 안내의 권장 이수 순서 기준입니다. 앞 단계 과목을 하나라도 이수했으면 충족으로 봅니다."

_ROMAN = str.maketrans({"Ⅰ": "1", "Ⅱ": "2", "Ⅲ": "3", "Ⅳ": "4"})


def normalize(name: str | None) -> str:
    """과목명 비교용: 공백 제거, 끝의 괄호 꼬리 제거, '데이타'→'데이터', 로마 숫자→아라비아 숫자."""
    text = re.sub(r"\s+", "", name or "")
    text = re.sub(r"\([^()]*\)$", "", text)  # 예: 문제해결기반공학연수실습(심화컴퓨터학), 운영체제(샘플)
    return text.replace("데이타", "데이터").translate(_ROMAN).upper()


@lru_cache(maxsize=1)
def load_chains() -> tuple[dict, ...]:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    chains = []
    for chain in data["chains"]:
        chains.append(
            {
                "category": chain["category"],
                "page": int(chain.get("page") or 1),
                "tracks": tuple(chain["tracks"]) if chain.get("tracks") else None,
                "stages": tuple(tuple(stage) for stage in chain["stages"]),
                "keys": tuple(frozenset(normalize(name) for name in stage) for stage in chain["stages"]),
            }
        )
    return tuple(chains)


@lru_cache(maxsize=1)
def _positions() -> dict[str, tuple[tuple[int, int], ...]]:
    """정규화한 과목명 → (사슬 번호, 단계 번호) 목록."""
    found: dict[str, list[tuple[int, int]]] = {}
    for i, chain in enumerate(load_chains()):
        for j, keys in enumerate(chain["keys"]):
            for key in keys:
                found.setdefault(key, []).append((i, j))
    return {key: tuple(value) for key, value in found.items()}


def _applies(chain: dict, track: str | None) -> bool:
    return chain["tracks"] is None or (track is not None and track in chain["tracks"])


def _name_of(item: str, catalog: Iterable) -> str:
    """과목코드나 강좌번호면 카탈로그의 과목명, 아니면 그대로."""
    item = item.strip()
    for course in catalog:
        if course.course_code == item or course.course_id == item:
            return course.name
    return item


class Checker:
    """이수 과목을 한 번만 정리해 두고 여러 과목을 빠르게 확인한다."""

    def __init__(self, completed: Iterable[str], catalog: Iterable, track: str | None = None) -> None:
        catalog = list(catalog)
        by_code = {}
        for course in catalog:
            by_code.setdefault(course.course_code, course.name)
            by_code.setdefault(course.course_id, course.name)
        self.track = track
        self.done: set[str] = set()
        for item in completed:
            item = item.strip()
            self.done.add(normalize(item))
            if item in by_code:
                self.done.add(normalize(by_code[item]))
        self._cache: dict[str, tuple[list[dict], bool]] = {}

    def requirements(self, name: str) -> tuple[list[dict], bool]:
        """(사슬별 바로 앞 단계 확인 결과, 어느 사슬에서든 첫 단계인지)."""
        key = normalize(name)
        if key not in self._cache:
            chains = load_chains()
            items, first = [], False
            for i, j in _positions().get(key, ()):
                chain = chains[i]
                if not _applies(chain, self.track):
                    continue
                if j == 0:
                    first = True
                    continue
                previous = chain["keys"][j - 1]
                items.append(
                    {
                        "chain": chain["category"],
                        "required": " / ".join(chain["stages"][j - 1]),
                        "satisfied": bool(previous & self.done),
                        "page": chain["page"],
                        "_keys": previous,
                    }
                )
            self._cache[key] = (items, first)
        return self._cache[key]

    def issue(self, name: str, planned: set[str] | frozenset = frozenset()) -> dict | None:
        """문제가 있으면 {missing, chain, page, kind}. planned 는 같은 학기에 듣는 과목의 정규화 이름."""
        items, first = self.requirements(name)
        if not items or first or any(item["satisfied"] for item in items):
            return None
        together = [item for item in items if item["_keys"] & planned]
        chosen = together or items
        missing = list(dict.fromkeys(item["required"] for item in chosen))
        return {
            "missing": missing,
            "chain": chosen[0]["chain"],
            "page": chosen[0]["page"],
            "kind": "concurrent" if together else "missing",
        }


def check(course: str, completed: list[str], catalog, track: str | None = None) -> list[dict]:
    """course(과목명 또는 코드)의 사슬별 바로 앞 단계를 completed(코드 또는 이름)로 이수했는지.

    반환: [{"chain", "required", "satisfied", "page"}]. 사슬 첫 단계나 사슬에 없는 과목이면 빈 목록.
    """
    catalog = list(catalog)
    checker = Checker(completed, catalog, track)
    items, first = checker.requirements(_name_of(course, catalog))
    if first:
        return []
    return [{k: v for k, v in item.items() if not k.startswith("_")} for item in items]


def issues_for(
    sections,
    completed: list[str],
    catalog,
    planned_names: Iterable[str] | None = None,
    track: str | None = None,
    checker: Checker | None = None,
) -> list[dict]:
    """sections(Course 목록) 중 선수과목이 걸리는 과목.

    planned_names: 같은 학기에 함께 듣는 과목명(없으면 sections 의 과목명). 앞 단계가 여기 있으면 kind="concurrent".
    반환: [{"course_id", "name", "missing", "chain", "page", "kind"}]
    """
    checker = checker or Checker(completed, catalog, track)
    names = planned_names if planned_names is not None else [section.name for section in sections]
    planned = {normalize(name) for name in names}
    result, seen = [], set()
    for section in sections:
        if section.course_code in seen:
            continue
        seen.add(section.course_code)
        found = checker.issue(section.name, planned)
        if found:
            result.append({"course_id": section.course_id, "name": section.name, **found})
    return result


def describe(issue: dict) -> str:
    """경고 한 줄. 예: 선수과목 확인: 운영체제 ← 시스템프로그래밍 미이수 (선수과목 안내 1쪽)"""
    before = ", ".join(issue["missing"])
    if issue["kind"] == "concurrent":
        return f"선수과목 확인: {issue['name']} ← {before}와 같은 학기에 함께 듣습니다 (권장 순서는 먼저 이수, 선수과목 안내 {issue['page']}쪽)"
    return f"선수과목 확인: {issue['name']} ← {before} 미이수 (선수과목 안내 {issue['page']}쪽)"
