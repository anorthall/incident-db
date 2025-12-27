from _typeshed import Incomplete
from django.contrib.admin.views.main import ChangeList
from django.http import HttpRequest
from django.template import Context
from django.utils.safestring import SafeString
from treebeard.templatetags import needs_checkboxes as needs_checkboxes

register: Incomplete
CHECKBOX_TMPL: str

def result_tree(context: Context, cl: ChangeList, request: HttpRequest) -> SafeString: ...
