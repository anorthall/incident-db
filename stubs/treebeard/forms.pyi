from typing import Any

from django import forms
from django.db.models import Model
from django.forms.utils import ErrorList
from treebeard.al_tree import AL_Node as AL_Node
from treebeard.models import Node
from treebeard.mp_tree import MP_Node as MP_Node
from treebeard.ns_tree import NS_Node as NS_Node

class MoveNodeForm[T: Model](forms.ModelForm[T]):
    is_sorted: bool
    def __init__(
        self,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        auto_id: str = "id_%s",
        prefix: str | None = None,
        initial: dict[str, Any] | None = None,
        error_class: type[ErrorList] = ...,
        label_suffix: str = ":",
        empty_permitted: bool = False,
        instance: T | None = None,
        **kwargs: Any,
    ) -> None: ...
    instance: T
    def save(self, commit: bool = True) -> T: ...
    @staticmethod
    def is_loop_safe(for_node: Node | None, possible_parent: Node) -> bool: ...
    @staticmethod
    def mk_indent(level: int) -> str: ...
    @classmethod
    def add_subtree(
        cls, for_node: Node | None, node: Node, options: list[tuple[Any, str]]
    ) -> None: ...
    @classmethod
    def mk_dropdown_tree(
        cls, model: type[Node], for_node: Node | None = None
    ) -> list[tuple[Any, str]]: ...

def movenodeform_factory(
    model: type[Model],
    form: type[MoveNodeForm[Any]] = ...,
    fields: list[str] | None = None,
    exclude: list[str] | None = None,
    formfield_callback: Any = None,
    widgets: dict[str, Any] | None = None,
) -> type[MoveNodeForm[Any]]: ...
