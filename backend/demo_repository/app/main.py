from __future__ import annotations

from fastapi import FastAPI

from app.models import Item
from app.repository import create_item, delete_item, get_item, list_items, update_item

app = FastAPI(title="ForgeOS Demo Shop")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/items")
async def read_items() -> list[Item]:
    return list_items()


@app.post("/items", status_code=201)
async def add_item(item: Item) -> Item:
    return create_item(item)


@app.get("/items/{item_id}")
async def read_item(item_id: int) -> Item | None:
    item = get_item(item_id)
    return item


@app.put("/items/{item_id}")
async def replace_item(item_id: int, item: Item) -> Item:
    return update_item(item_id, item)


@app.delete("/items/{item_id}")
async def remove_item(item_id: int) -> dict[str, bool]:
    delete_item(item_id)
    return {"deleted": True}

