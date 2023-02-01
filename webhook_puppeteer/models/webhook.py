from functools import cached_property
from collections.abc import Mapping
from enum import Enum
from typing import TypedDict
from typing import Literal, Union
from typing import Optional, Any
from pydantic import BaseModel, Field, validator, ValidationError

from . import Account, BodyPattern


class Entity(Enum):
    LEAD = "leads"  # Сделка
    CONTACT = "contacts"  # Контакт / Компания
    TASK = "task"  # Задача
    CUSTOMER = "customers"  # Покупатель
    CATALOG = "catalogs"  # Каталог (список),  включая счета, юр.лица и товары
    UNSORTED = "unsorted"  # Неразобранное
    TALK = "talk"  # Беседа
    MESSAGE = "message"  # Входящее сообщение


class Event(Enum):

    UPDATE = "update"  # Изменение сущности
    DELETE = "delete"  # Удаление сущности
    NOTE = "note"  # Примечание к сущности
    ADD = "add"  # Добавление сущности
    STATUS = "status"  # Смена статуса сделки
    RESPONSIBLE = "responsible"  # Смена ответственного
    RESTORE = "restore"  # Восстановление сущности


class WebhookPattern(BaseModel):
    entity: Entity | None
    event: Event | None

    def __eq__(self, other):
        return self.entity is other.entity

    def __hash__(self):
        entity = self.entity.value if self.entity is not None else "None"
        event = self.event.value if self.event is not None else "None"
        return hash(f"{entity}:{event}")


class WebhookHandler(BaseModel):
    pattern: WebhookPattern
    model: BaseModel


class HookEvent(BaseModel):
    __root__: dict[Event, Union[BodyPattern.get_subclasses()]]  # type: ignore

    _body = None # type: ignore

    @validator("__root__")
    def single_key(cls, v):
        if len(v.keys()) != 1:
            raise ValueError("there cannot be more than one event for an entity")
        return v

    @property
    def event(self):
        return tuple(self.__root__.keys())[0]

    @property
    def body(self):
        if not self._body:
            self._body = self.__root__[self.event]  # type: ignore

        return self._body

    class Config:
        extra = "allow"


class WebHook(BaseModel):
    __root__: dict[Entity | Literal["account"], HookEvent | Account]

    _pattern: None | WebhookPattern = None
    _event: None | Event = None
    _entity: Entity = None  # type: ignore
    _body: BodyPattern | None = None

    @validator("__root__")
    def entity_stated(cls, v):
        if not any([isinstance(k, Entity) for k in v]):
            raise ValueError("hook must state an entity")
        return v

    @property
    def entity(self) -> Entity:
        if not self._entity:
            for key in self.__root__.keys():
                if isinstance(key, Entity):
                    self._entity = key
                    break

        return self._entity

    @property
    def event(self):
        if not self._event:
            entity = self.entity
            if entity is not None:
                event_obj: HookEvent = self.__root__[entity]  # type: ignore
                self._event = event_obj.event
        return self._event

    @property
    def pattern(self):
        if not self._pattern:
            self._pattern = WebhookPattern(entity=self.entity, event=self.event)
        return self._pattern

    @property
    def body(self) -> BaseModel:
        if not self._body:
            self._body = self.__root__[self.entity].body  # type: ignore

        return self._body  # type: ignore

    class Config:
        extra = "allow"
