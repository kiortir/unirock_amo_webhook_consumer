from pydantic import BaseModel


class _Links(BaseModel):
    self: str


class Account(BaseModel):
    subdomain: str
    id: str | None
    _links: _Links | None
