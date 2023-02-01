from pydantic import BaseModel, Field
from .base import CustomField, BodyPattern, BaseData


class LeadData(BaseData, BaseModel):

    id: int
    name: str | None
    status_id: int | None
    old_status_id: int | None
    price: str | None
    responsible_user_id: str | None
    last_modified: int | str | None
    modified_user_id: int | None
    created_user_id: int | None
    date_create: int | str | None
    created_at: int | None
    updated_at: int | None

    pipeline_id: int | None
    tags: dict | None
    account_id: int | None
    custom_fields: list[CustomField] | None


class LeadHookStatus(BaseModel):
    field_0: LeadData = Field(..., alias="0")


class ListOfLeadsPattern(BodyPattern):
    __root__: list[LeadData]

    @property
    def data(self):
        return self.__root__[0]