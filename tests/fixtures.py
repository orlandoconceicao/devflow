from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class TemporaryNames:
    client: str
    project: str
    task: str


def temporary_names() -> TemporaryNames:
    suffix = uuid4().hex[:10]
    return TemporaryNames(
        client=f"TEST_CLIENT_{suffix}",
        project=f"TEST_PROJECT_{suffix}",
        task=f"TEST_TASK_{suffix}",
    )
