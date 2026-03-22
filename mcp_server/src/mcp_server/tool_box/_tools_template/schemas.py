from typing import Literal

from pydantic import BaseModel

# region Example Models

class NestedObjectArgument(BaseModel):
    """Example of a nested object argument — prefer flat objects (see FlatObjectArgument)."""

    item_id: int

    class NestedParent(BaseModel):
        parent_id: int

        class NestedChild(BaseModel):
            item_type: Literal["type1", "type2", "type3"]
            active: bool
            child_items: list[dict]

        nested_child: NestedChild

    nested_parent: NestedParent


class FlatObjectArgument(BaseModel):
    """Flat version of NestedObjectArgument — all properties at one level.

    Models perform better when asked to pass or read a simple object
    or list of flat objects. Prefer this pattern over deep nesting.
    """

    item_id: int
    nested_id: int
    item_type: Literal["type1", "type2", "type3"]
    active: bool
    child_items: list[dict]


class ExampleOutputModel(BaseModel):
    """Generic output model example.

    Replace with your domain-specific output model.
    """

    id: int
    name: str
    status: str
    metadata: dict = {}

# endregion
