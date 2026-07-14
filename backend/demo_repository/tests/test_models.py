from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models import Item, User


def test_user_creation():
    user = User(email="ada@example.com", name="Ada", hashed_password="hash")

    assert user.email == "ada@example.com"
    assert user.name == "Ada"


def test_user_validation():
    user = User(email="invalid-email", name="", hashed_password="")

    assert user.is_valid() is False


def test_item_schema():
    item = Item(id=1, name="Widget", price=9.99)

    assert item.price == 9.99


def test_item_price_validation():
    with pytest.raises(ValidationError):
        Item(id=1, name="Broken Widget", price=-1)

