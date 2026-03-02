from typing import Any, ClassVar

from django.contrib import admin
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponse
from django.urls import URLPattern
from treebeard.al_tree import AL_Node as AL_Node
from treebeard.exceptions import (
    InvalidMoveToDescendant as InvalidMoveToDescendant,
)
from treebeard.exceptions import (
    InvalidPosition as InvalidPosition,
)
from treebeard.exceptions import (
    MissingNodeOrderBy as MissingNodeOrderBy,
)
from treebeard.exceptions import (
    PathOverflow as PathOverflow,
)
from treebeard.forms import MoveNodeForm
from treebeard.models import Node

def check_empty_dict(GET_dict: dict[str, Any]) -> bool: ...

class TreeAdmin[T: Model](admin.ModelAdmin[T]):
    change_list_template: ClassVar[str]
    def get_queryset(self, request: HttpRequest) -> QuerySet[T, T]: ...
    def changelist_view(
        self, request: HttpRequest, extra_context: dict[str, Any] | None = None
    ) -> HttpResponse: ...
    def get_urls(self) -> list[URLPattern]: ...
    def get_node(self, node_id: Any) -> T: ...
    def try_to_move_node(
        self, as_child: bool, node: Node, pos: str, request: HttpRequest, target: Node
    ) -> HttpResponse: ...
    def move_node(self, request: HttpRequest) -> HttpResponse: ...

def admin_factory(form_class: type[MoveNodeForm[Any]]) -> type[TreeAdmin[Any]]: ...
