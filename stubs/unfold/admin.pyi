from django.contrib.admin import ModelAdmin as BaseModelAdmin
from django.contrib.admin import StackedInline as BaseStackedInline
from django.contrib.admin import TabularInline as BaseTabularInline
from django.db.models import Model

class ModelAdmin[ModelT: Model](BaseModelAdmin[ModelT]): ...
class TabularInline[ModelT: Model, ParentModelT: Model](
    BaseTabularInline[ModelT, ParentModelT]
): ...
class StackedInline[ModelT: Model, ParentModelT: Model](
    BaseStackedInline[ModelT, ParentModelT]
): ...
