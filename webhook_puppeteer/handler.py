import asyncio
import copy
import functools
from collections import defaultdict
from dataclasses import dataclass, field
from pprint import pprint
from typing import Any, Awaitable, Callable
from uuid import UUID, uuid4

from fastapi import BackgroundTasks
from pydantic import BaseModel

from .models import (BodyPattern, CustomField, Entity, Event, WebHook,
                     WebhookPattern)


@dataclass
class Task:
    pattern: WebhookPattern = WebhookPattern()
    structure: dict | None = None

    callback: Awaitable[None] | None = None
    id: UUID = field(default_factory=uuid4)


class HookSubscriber:

    def __init__(self, pattern: WebhookPattern, callback: Callable[..., Awaitable[None]], filter_patterns: list[dict] | None = None, * args, **kwargs):
        self.pattern = pattern
        self.callback = callback
        self.filter_patterns = filter_patterns or []

    def _match(self, pattern: dict, data):
        if "custom_fields" in pattern:
            pattern = copy.deepcopy(pattern)
            fields = {str(field["id"])
                      for field in pattern["custom_fields"]}
            ignored_fields = [field for field in getattr(
                data, "custom_fields", []) if str(field.id) not in fields]

            pattern["custom_fields"].extend(ignored_fields)

        clone: BaseModel = data.copy(update=pattern)
        return clone == data

    async def __call__(self, hook: BodyPattern, *args: Any, **kwds: Any) -> Any:
        hook_body = hook.data

        if self.filter_patterns and not any((
            self._match(pattern, hook_body)
                for pattern in self.filter_patterns
        )):
            return

        await self.callback(hook_body, *args, **kwds)


class WebhookHandlerPool:

    _subscribers: dict[WebhookPattern,
                       list[Any]] = defaultdict(list)

    def _subscribe(self, subscriber: Any):
        self._subscribers[subscriber.pattern].append(subscriber)

    def add_origin(self, fn: Callable[..., Awaitable[Any]]):

        async def wrapper(hook: WebHook, tasks: BackgroundTasks):
            tasks.add_task(self.resolve, hook)
            return await fn(hook)

        wrapper.__annotations__.update(fn.__annotations__)

        return wrapper

    def subscribe(self, entity: Entity | None = None, event: Event | None = None, filter_patterns=None):
        pattern = WebhookPattern(entity=entity, event=event)

        def decorator(wrapee):
            subscriber = HookSubscriber(pattern, wrapee, filter_patterns)
            self._subscribe(subscriber)

        return decorator

    def unsubscribe(self, task: Task):
        self._subscribers[task.pattern].remove(task)

    # TODO: wildcard matches
    NONE_PATTERN = WebhookPattern()

    async def resolve(self, hook: WebHook):
        subscribers = self._subscribers.get(
            hook.pattern, []) + self._subscribers.get(self.NONE_PATTERN, [])
        tasks = list(subscriber(hook.body) for subscriber in subscribers)
        await asyncio.gather(*tasks)
