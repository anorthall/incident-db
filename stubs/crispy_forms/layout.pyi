from dataclasses import dataclass
from typing import Any

from crispy_forms.utils import TEMPLATE_PACK
from crispy_forms.utils import flatatt as flatatt
from crispy_forms.utils import render_field as render_field
from django.forms import forms

@dataclass
class Pointer:
    positions: list[int]
    name: str

    def __init__(self, positions, name) -> None: ...

class TemplateNameMixin:
    def get_template_name(self, template_pack: str): ...

class LayoutObject(TemplateNameMixin):
    choices: list[tuple[str, str]]

    def __getitem__(self, slice: int): ...
    def __setitem__(self, slice: int, value: Any) -> None: ...
    def __delitem__(self, slice: int) -> None: ...
    def __len__(self) -> int: ...
    def __getattr__(self, name: str): ...
    def get_field_names(self, index: int | None = None): ...
    def get_layout_objects(
        self,
        *LayoutClasses,  # noqa: N803
        index: int | None = None,
        max_level: int = 0,
        greedy: bool = False,
    ): ...
    def get_rendered_fields(
        self,
        form: forms.Form,
        context: dict[str, Any],
        template_pack: str = TEMPLATE_PACK,
        **kwargs: dict[str, Any],
    ): ...

class Layout(LayoutObject):
    fields: Any

    def __init__(self, *fields: Any) -> None: ...
    def render(
        self,
        form: forms.Form,
        context: dict[str, Any],
        template_pack: str = TEMPLATE_PACK,
        **kwargs: dict[str, Any],
    ): ...

class ButtonHolder(LayoutObject):
    template: str
    fields: Any
    css_id: str
    css_class: str

    def __init__(
        self,
        *fields,
        css_id: str | None = None,
        css_class: str | None = None,
        template: str | None = None,
    ) -> None: ...
    def render(
        self,
        form: forms.Form,
        context: dict[str, Any],
        template_pack: str = TEMPLATE_PACK,
        **kwargs: dict[str, Any],
    ): ...

class BaseInput(TemplateNameMixin):
    template: str
    field_classes: str
    name: str
    value: str
    id: str
    attrs: Any
    flat_attrs: Any

    def __init__(
        self,
        name: str,
        value: str,
        *,
        css_id: str | None = None,
        css_class: str | None = None,
        template: str | None = None,
        **kwargs,
    ) -> None: ...
    def render(
        self,
        form: forms.Form,
        context: dict[str, Any],
        template_pack: str = TEMPLATE_PACK,
        **kwargs: dict[str, Any],
    ): ...

class Submit(BaseInput):
    input_type: str
    field_classes: str

class Button(BaseInput):
    input_type: str
    field_classes: str

class Hidden(BaseInput):
    input_type: str
    field_classes: str

class Reset(BaseInput):
    input_type: str
    field_classes: str

class Fieldset(LayoutObject):
    template: str | None
    fields: Any
    legend: str
    css_class: str
    css_id: str
    flat_attrs: Any

    def __init__(
        self,
        legend,
        *fields,
        css_class: str | None = None,
        css_id: str | None = None,
        template: str | None = None,
        **kwargs,
    ) -> None: ...
    def render(
        self,
        form: forms.Form,
        context: dict[str, Any],
        template_pack: str = TEMPLATE_PACK,
        **kwargs: dict[str, Any],
    ): ...

class MultiField(LayoutObject):
    template: str | None
    field_template: str
    fields: Any
    label_html: str
    label_class: str
    css_class: str
    css_id: str
    help_text: str
    flat_attrs: Any

    def __init__(
        self,
        label: str,
        *fields: Any,
        label_class: Any | None = None,
        help_text: str | None = None,
        css_class: str | None = None,
        css_id: str | None = None,
        template: str | None = None,
        field_template: Any | None = None,
        **kwargs,
    ) -> None: ...
    def render(
        self,
        form: forms.Form,
        context: dict[str, Any],
        template_pack: str = TEMPLATE_PACK,
        **kwargs: dict[str, Any],
    ): ...

class Div(LayoutObject):
    template: str | None
    css_class: str
    fields: Any
    css_id: str
    flat_attrs: Any

    def __init__(
        self,
        *fields,
        css_id: str | None = None,
        css_class: str | None = None,
        template: str | None = None,
        **kwargs,
    ) -> None: ...
    def render(
        self,
        form: forms.Form,
        context: dict[str, Any],
        template_pack: str = TEMPLATE_PACK,
        **kwargs: dict[str, Any],
    ): ...

class Row(Div):
    template: str | None

class Column(Div):
    template: str | None

class HTML:
    html: str

    def __init__(self, html) -> None: ...
    def render(
        self,
        form: forms.Form,
        context: dict[str, Any],
        template_pack: str = TEMPLATE_PACK,
        **kwargs: dict[str, Any],
    ): ...

class Field(LayoutObject):
    template: str | None
    attrs: Any
    fields: Any
    wrapper_class: Any

    def __init__(
        self,
        *fields,
        css_class: str | None = None,
        wrapper_class: Any | None = None,
        template: str | None = None,
        **kwargs,
    ) -> None: ...
    def render(
        self,
        form: forms.Form,
        context: dict[str, Any],
        template_pack: str = TEMPLATE_PACK,
        extra_context: dict[str, Any] | None = None,
        **kwargs: dict[str, Any],
    ): ...

class MultiWidgetField(Field):
    fields: Any
    attrs: Any
    template: str | None
    wrapper_class: Any

    def __init__(
        self,
        *fields: Any,
        attrs: Any | None = None,
        template: str | None = None,
        wrapper_class: Any | None = None,
    ) -> None: ...
