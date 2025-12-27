from collections.abc import Mapping
from typing import Any, Literal, Self, TypedDict

from django.db import models
from django.db.models import Manager
from treebeard.exceptions import InvalidMoveToDescendant as InvalidMoveToDescendant
from treebeard.exceptions import NodeAlreadySaved as NodeAlreadySaved
from treebeard.models import Node

SiblingPos = Literal["first-sibling", "left", "right", "last-sibling", "sorted-sibling"]
MovePos = Literal[
    "first-sibling",
    "left",
    "right",
    "last-sibling",
    "sorted-sibling",
    "first-child",
    "last-child",
    "sorted-child",
]

class BulkDict(TypedDict, total=False):
    data: Mapping[str, Any]
    children: list[BulkDict]

class InfoDict(TypedDict):
    open: bool
    close: list[int]
    level: int

def get_result_class[T: Node](cls: type[T]) -> type[T]: ...
def merge_deleted_counters(
    c1: tuple[int, dict[str, int]], c2: tuple[int, dict[str, int]]
) -> tuple[int, dict[str, int]]: ...

class NS_NodeQuerySet[T: models.Model](models.query.QuerySet[T, T]):
    def delete(
        self,
        *args: Any,
        removed_ranges: list[tuple[int, int, int]] | None = None,
        deleted_counter: tuple[int, dict[str, int]] | None = None,
        **kwargs: Any,
    ) -> tuple[int, dict[str, int]]: ...

class NS_NodeManager[T: models.Model](Manager[T]):
    def get_queryset(self) -> NS_NodeQuerySet[T]: ...

class NS_Node(Node):
    lft: int
    rgt: int
    tree_id: int
    depth: int
    @classmethod
    def add_root(cls, **kwargs: Any) -> Self: ...
    def add_child(self, **kwargs: Any) -> Self: ...
    def add_sibling(self, pos: SiblingPos | None = None, **kwargs: Any) -> Self: ...
    def move(self, target: Self, pos: MovePos | None = None) -> None: ...
    @classmethod
    def load_bulk(
        cls, bulk_data: list[BulkDict], parent: Self | None = None, keep_ids: bool = False
    ) -> list[Any]: ...
    def get_children(self) -> NS_NodeQuerySet[Self]: ...
    def get_depth(self) -> int: ...
    def is_leaf(self) -> bool: ...
    def get_root(self) -> Self: ...
    def is_root(self) -> bool: ...
    def get_siblings(self) -> NS_NodeQuerySet[Self]: ...
    @classmethod
    def dump_bulk(cls, parent: Self | None = None, keep_ids: bool = True) -> list[BulkDict]: ...
    @classmethod
    def get_tree(cls, parent: Self | None = None) -> NS_NodeQuerySet[Self]: ...
    def get_descendants(self, include_self: bool = False) -> NS_NodeQuerySet[Self]: ...
    def get_descendant_count(self) -> int: ...
    def get_ancestors(self) -> NS_NodeQuerySet[Self]: ...
    def is_descendant_of(self, node: Self) -> bool: ...
    def get_parent(self, update: bool = False) -> Self | None: ...
    @classmethod
    def get_root_nodes(cls) -> NS_NodeQuerySet[Self]: ...
