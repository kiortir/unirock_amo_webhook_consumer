from .models import WebHook, Entity, Event, BaseData
from .main import pool
from typing import TypedDict


class Pattern(TypedDict):
    entity: Entity | None
    event: Event | None
    filter_patterns: list[dict] | None


pattern: Pattern = {
    "entity": Entity.LEAD,
    "event": Event.STATUS,
    "filter_patterns": [
        {"status_id": 22577428, "pipeline_id": 1453099},
        {"status_id": 142, "pipeline_id": 1453099},
    ],
}

from pprint import pprint


@pool.subscribe(**pattern)  # type: ignore
async def send_to_1c(hook: BaseData) -> None:
    print("task")
    print(hook["менеджер по продажам"])