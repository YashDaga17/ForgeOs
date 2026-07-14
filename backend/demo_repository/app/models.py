from __future__ import annotations

from pydantic import BaseModel, Field


class Item(BaseModel):
    id: int
    name: str
    price: float = Field(ge=0)


class User(BaseModel):
    email: str
    name: str
    hashed_password: str = ""

