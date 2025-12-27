from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from cidb.src.incidents.models import (
    Author,
    Cave,
    ContentReport,
    DataOperationLog,
    Document,
    DuplicateGroup,
    DuplicateGroupMember,
    GeographicArea,
    Incident,
    IncidentEmbedding,
    IncidentPerson,
    IncidentReference,
    Injury,
    Location,
    Person,
    Publication,
    PublicationPage,
    SearchClick,
    SearchQuery,
    SourceExtract,
    SourceFile,
    Tag,
)


class IncidentReferenceInline(TabularInline[IncidentReference, Incident]):
    model = IncidentReference
    extra = 0
    fields = ("index", "author", "title", "source", "reference_date", "raw_citation")


class IncidentPersonInline(TabularInline[IncidentPerson, Incident]):
    model = IncidentPerson
    extra = 0
    autocomplete_fields = ("person",)
    filter_horizontal = ("injuries",)


class DuplicateGroupMemberInline(TabularInline[DuplicateGroupMember, DuplicateGroup]):
    model = DuplicateGroupMember
    extra = 0
    autocomplete_fields = ("incident",)
    readonly_fields = ("similarity_score", "llm_confidence", "llm_reasoning")


class PublicationPageInline(TabularInline[PublicationPage, Publication]):
    model = PublicationPage
    extra = 0
    autocomplete_fields = ("document",)


class SourceExtractInline(TabularInline[SourceExtract, SourceFile]):
    model = SourceExtract
    extra = 0
    readonly_fields = ("sequence",)


@admin.register(Tag)
class TagAdmin(ModelAdmin[Tag]):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Injury)
class InjuryAdmin(ModelAdmin[Injury]):
    list_display = ("id", "description", "created_at")
    search_fields = ("description",)
    ordering = ("description",)


@admin.register(Author)
class AuthorAdmin(ModelAdmin[Author]):
    list_display = ("id", "name", "kind", "created_at")
    list_filter = ("kind",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(GeographicArea)
class GeographicAreaAdmin(ModelAdmin[GeographicArea]):
    list_display = ("id", "name", "kind", "code", "depth")
    list_filter = ("kind",)
    search_fields = ("name", "code")
    ordering = ("path",)


@admin.register(Location)
class LocationAdmin(ModelAdmin[Location]):
    list_display = ("id", "__str__", "country_text", "state_text", "region_text", "canonical_area")
    search_fields = ("country_text", "state_text", "region_text")
    list_filter = ("country_text",)
    autocomplete_fields = ("canonical_area",)

    fieldsets = (
        ("Text Location", {"fields": ("country_text", "state_text", "region_text")}),
        ("Canonical Reference", {"fields": ("canonical_area",)}),
        ("Coordinates", {"fields": ("latitude", "longitude")}),
    )


@admin.register(Cave)
class CaveAdmin(ModelAdmin[Cave]):
    list_display = ("id", "name", "location", "created_at")
    search_fields = ("name",)
    autocomplete_fields = ("location",)
    ordering = ("name",)


@admin.register(Person)
class PersonAdmin(ModelAdmin[Person]):
    list_display = ("id", "name", "gender", "date_of_birth", "location")
    search_fields = ("name",)
    list_filter = ("gender",)
    autocomplete_fields = ("location",)
    ordering = ("name",)


@admin.register(Document)
class DocumentAdmin(ModelAdmin[Document]):
    list_display = ("id", "has_text", "has_image", "has_pdf", "created_at")
    search_fields = ("id",)
    readonly_fields = ("id",)

    @admin.display(boolean=True, description="Text")
    def has_text(self, obj: Document) -> bool:
        return bool(obj.text)

    @admin.display(boolean=True, description="Image")
    def has_image(self, obj: Document) -> bool:
        return bool(obj.image)

    @admin.display(boolean=True, description="PDF")
    def has_pdf(self, obj: Document) -> bool:
        return bool(obj.pdf)


@admin.register(Publication)
class PublicationAdmin(ModelAdmin[Publication]):
    list_display = ("id", "title", "published_at", "website", "created_at")
    search_fields = ("title",)
    autocomplete_fields = ("content",)
    filter_horizontal = ("authors",)
    inlines = (PublicationPageInline,)

    fieldsets = (
        ("Publication Info", {"fields": ("title", "website", "published_at")}),
        ("Authors", {"fields": ("authors",)}),
        ("Content", {"fields": ("content",)}),
    )


@admin.register(PublicationPage)
class PublicationPageAdmin(ModelAdmin[PublicationPage]):
    list_display = ("id", "publication", "number", "document")
    autocomplete_fields = ("publication", "document")
    ordering = ("publication", "number")


@admin.register(SourceFile)
class SourceFileAdmin(ModelAdmin[SourceFile]):
    list_display = ("id", "filename", "publication", "created_at")
    search_fields = ("filename",)
    autocomplete_fields = ("document", "publication")
    readonly_fields = ("id",)
    inlines = (SourceExtractInline,)


@admin.register(SourceExtract)
class SourceExtractAdmin(ModelAdmin[SourceExtract]):
    list_display = ("id", "source_file", "sequence", "created_at")
    search_fields = ("content",)
    autocomplete_fields = ("source_file",)
    readonly_fields = ("metadata",)


@admin.register(Incident)
class IncidentAdmin(ModelAdmin[Incident]):
    list_display = ("id", "title", "cave", "date", "origin", "view_count", "created_at")
    search_fields = ("title", "report", "analysis", "summary")
    list_filter = ("tags", "origin")
    autocomplete_fields = ("cave", "origin", "source_extract")
    filter_horizontal = ("tags",)
    readonly_fields = ("view_count", "search_vector", "created_at", "updated_at")
    inlines = (IncidentReferenceInline, IncidentPersonInline)

    fieldsets = (
        ("Identification", {"fields": ("title", "cave", "date", "time")}),
        ("Content", {"fields": ("report", "analysis", "summary")}),
        ("Classification", {"fields": ("tags",)}),
        ("Source", {"fields": ("origin", "source_extract")}),
        ("Metadata", {"fields": ("view_count", "search_vector", "created_at", "updated_at")}),
    )


@admin.register(IncidentReference)
class IncidentReferenceAdmin(ModelAdmin[IncidentReference]):
    list_display = ("id", "incident", "index", "author", "title")
    autocomplete_fields = ("incident",)
    ordering = ("incident", "index")


@admin.register(IncidentPerson)
class IncidentPersonAdmin(ModelAdmin[IncidentPerson]):
    list_display = ("id", "incident", "person", "age_at_incident")
    autocomplete_fields = ("incident", "person")
    filter_horizontal = ("injuries",)


@admin.register(DuplicateGroup)
class DuplicateGroupAdmin(ModelAdmin[DuplicateGroup]):
    list_display = ("id", "status", "primary_incident", "member_count", "created_at")
    list_filter = ("status",)
    search_fields = ("id", "notes")
    autocomplete_fields = ("primary_incident",)
    readonly_fields = ("created_at", "updated_at")
    inlines = (DuplicateGroupMemberInline,)

    @admin.display(description="Members")
    def member_count(self, obj: DuplicateGroup) -> int:
        return obj.members.count()


@admin.register(DuplicateGroupMember)
class DuplicateGroupMemberAdmin(ModelAdmin[DuplicateGroupMember]):
    list_display = ("id", "group", "incident", "similarity_score", "llm_confidence")
    autocomplete_fields = ("group", "incident")
    readonly_fields = ("similarity_score", "llm_confidence", "llm_reasoning")


@admin.register(IncidentEmbedding)
class IncidentEmbeddingAdmin(ModelAdmin[IncidentEmbedding]):
    list_display = ("id", "incident", "model_version", "embedding_preview", "created_at")
    autocomplete_fields = ("incident",)
    readonly_fields = ("embedding", "created_at", "updated_at")

    @admin.display(description="Embedding")
    def embedding_preview(self, obj: IncidentEmbedding) -> str:
        if obj.embedding:
            return (
                f"[{obj.embedding[0]:.4f}, {obj.embedding[1]:.4f}, ... ({len(obj.embedding)} dims)]"
            )
        return "-"


@admin.register(ContentReport)
class ContentReportAdmin(ModelAdmin[ContentReport]):
    list_display = ("id", "incident", "reason", "status", "reporter", "created_at")
    list_filter = ("status", "reason")
    search_fields = ("description", "reviewer_notes")
    autocomplete_fields = ("incident", "reporter")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Report Details", {"fields": ("incident", "url", "reason", "description")}),
        ("Reporter", {"fields": ("reporter",)}),
        ("Review", {"fields": ("status", "reviewer_notes")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(SearchQuery)
class SearchQueryAdmin(ModelAdmin[SearchQuery]):
    list_display = ("id", "query", "query_count", "last_queried_at")
    search_fields = ("query",)
    ordering = ("-query_count",)
    readonly_fields = ("query", "query_count", "last_queried_at")

    def has_add_permission(self, request: object) -> bool:
        return False

    def has_change_permission(self, request: object, obj: SearchQuery | None = None) -> bool:
        return False


@admin.register(SearchClick)
class SearchClickAdmin(ModelAdmin[SearchClick]):
    list_display = ("id", "query", "incident", "position", "clicked_at")
    search_fields = ("query",)
    list_filter = ("position",)
    autocomplete_fields = ("incident",)
    readonly_fields = ("query", "incident", "position", "clicked_at")

    def has_add_permission(self, request: object) -> bool:
        return False

    def has_change_permission(self, request: object, obj: SearchClick | None = None) -> bool:
        return False


@admin.register(DataOperationLog)
class DataOperationLogAdmin(ModelAdmin[DataOperationLog]):
    list_display = ("id", "incident", "operation_name", "operation_version", "status", "created_at")
    list_filter = ("status", "operation_name")
    search_fields = ("operation_name", "error_message")
    autocomplete_fields = ("incident",)
    readonly_fields = (
        "incident",
        "operation_name",
        "operation_version",
        "status",
        "changes_made",
        "error_message",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request: object) -> bool:
        return False

    def has_change_permission(self, request: object, obj: DataOperationLog | None = None) -> bool:
        return False
