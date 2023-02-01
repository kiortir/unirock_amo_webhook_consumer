from functools import cached_property
from pydantic import BaseModel
from typing import Any, Optional, Union

from abc import ABC, abstractmethod


class CustomFieldValue(BaseModel):
    value: Any
    enum: Any


class CustomField(BaseModel):
    id: int
    name: str
    values: list[CustomFieldValue]


class BaseData(BaseModel):
    def normalize_value(self, value):
        if isinstance(value, str):
            value = value.replace("+", " ")
        return value

    def __getitem__(self, key: str | int) -> Any:
        key = str(key)
        field = self.custom_fields_by_id.get(key) or self.custom_field_by_name(key)
        values = [self.normalize_value(value.value) for value in field.values]

        return values[0] if len(values) == 1 else values

    @property
    def custom_fields_by_id(self) -> dict[str, CustomField]:

        if not getattr(self, "_fields_by_id", None):
            custom_fields: list[CustomField] = getattr(self, "custom_fields", [])
            _fields_by_id = {str(field.id): field for field in custom_fields}
            self.__dict__["_fields_by_id"] = _fields_by_id
        return self.__dict__["_fields_by_id"]  # type: ignore

    @property
    def custom_fields_by_names(self) -> dict[str, CustomField]:
        if not getattr(self, "_fields_by_names", None):
            custom_fields: list[CustomField] = getattr(self, "custom_fields", [])
            _fields_by_names = {field.name.lower(): field for field in custom_fields}
            self.__dict__["_fields_by_names"] = _fields_by_names
        return self.__dict__["_fields_by_names"]  # type: ignore

    def custom_field_by_name(self, name: str):
        name = name.replace(" ", "+").lower()

        return self.custom_fields_by_names.get(name)

    def get_custom_field(self, field_id: int, field_name: str | None = None):

        custom_fields: list[CustomField] = getattr(self, "custom_fields", [])

        return next(
            (x for x in custom_fields if x.id == field_id or x.name == field_name), None
        )

    def dict(self, *args, **kwargs):
        exclude_values = kwargs.pop("exclude", None)
        exclude = exclude_values or set()
        exclude |= {"_fields_by_id", "_fields_by_names"}
        kwargs["exclude"] = exclude
        return super().dict(**kwargs)


class BodyPattern(BaseModel, ABC):
    @classmethod
    def get_subclasses(cls):
        r = tuple(cls.__subclasses__())
        return r

    @property
    @abstractmethod
    def data(self) -> BaseData:
        raise NotImplementedError()
