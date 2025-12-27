from django.template import Context, Variable

action_form_var: Variable

def needs_checkboxes(context: Context) -> bool: ...
