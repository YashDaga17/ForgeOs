from __future__ import annotations

from app.models import Item

_ITEMS: dict[int, Item] = {
    1: Item(id=1, name="Signal Beacon", price=42.0),
    2: Item(id=2, name="Patch Cable", price=7.5),
}


def list_items() -> list[Item]:
    return list(_ITEMS.values())


def get_item(item_id: int) -> Item | None:
    return _ITEMS.get(item_id)


def create_item(item: Item) -> Item:
    _ITEMS[item.id] = item
    return item


def update_item(item_id: int, item: Item) -> Item:
    stored = item.model_copy(update={"id": item_id})
    _ITEMS[item_id] = stored
    return stored


def delete_item(item_id: int) -> None:
    _ITEMS.pop(item_id, None)

