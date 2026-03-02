from django.contrib.admin.templatetags.admin_list import ResultList
from django.contrib.admin.views.main import ChangeList
from django.forms import BoundField
from django.template import Library

register: Library

def result_tree(
    cl: ChangeList,
) -> dict[
    str, list[dict[str, int | str | None]] | list[ResultList] | list[BoundField] | ChangeList | int
]: ...
@register.simple_tag
def tree_context(cl: ChangeList) -> dict[str, str | int]: ...
