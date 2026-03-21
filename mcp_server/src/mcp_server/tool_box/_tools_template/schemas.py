from typing import Literal

from pydantic import BaseModel

# region Example Models

class NestedObjectArgument(BaseModel):
    """Example of a nested object argument — prefer flat objects (see FlatObjectArgument)."""

    Id: int

    class VendorTree(BaseModel):
        Id: int

        class Tree(BaseModel):
            TreeTypeEnum: Literal["type1", "type2", "type3"]
            Active: bool
            TreeNodes: list[dict]

        tree: Tree

    vendor_tree: VendorTree


class FlatObjectArgument(BaseModel):
    """Flat version of NestedObjectArgument — all properties at one level.

    Models perform better when asked to pass or read a simple object
    or list of flat objects. Prefer this pattern over deep nesting.
    """

    Id: int
    TreeId: int
    TreeTypeEnum: Literal["type1", "type2", "type3"]
    Active: bool
    TreeNodes: list[dict]


class ResourceModel(BaseModel):
    """Generic output model for a resource.

    Replace with your domain-specific output model.
    """

    id: int
    name: str
    status: str
    metadata: dict = {}

# endregion
