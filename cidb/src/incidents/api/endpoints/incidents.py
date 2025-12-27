from enum import StrEnum
from typing import Annotated

from django.contrib.postgres.search import SearchQuery as PgSearchQuery
from django.contrib.postgres.search import SearchRank, TrigramSimilarity
from django.db.models import F, Q
from django.db.models.functions import Ln
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Query, Router, Schema

from cidb.src.incidents.api.schemas.common import PaginatedResponse
from cidb.src.incidents.api.schemas.incident import (
    IncidentDetailSchema,
    IncidentListSchema,
)
from cidb.src.incidents.models import (
    Incident,
    SearchClick,
    SearchQuery,
)

router = Router()


class SortBy(StrEnum):
    DATE = "date"
    RELEVANCE = "relevance"
    POPULARITY = "popularity"
    TITLE = "title"
    CAVE_NAME = "cave_name"


class SuggestionSchema(Schema):
    suggestions: list[str]


class DidYouMeanSchema(Schema):
    suggestion: str | None
    similarity: float | None


class ClickTrackRequest(Schema):
    query: str
    incident_id: int
    position: int


class ClickTrackSchema(Schema):
    success: bool


@router.get(
    "/search",
    response=PaginatedResponse[IncidentListSchema],
)
def search_incidents(
    request: HttpRequest,
    q: Annotated[str | None, Query(description="Search query")] = None,
    sort_by: Annotated[SortBy | None, Query(description="Sort field")] = None,
    sort_order: Annotated[str, Query(description="Sort order", pattern="^(asc|desc)$")] = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[IncidentListSchema]:
    queryset = (
        Incident.objects.only(
            "id",
            "title",
            "date",
            "summary",
            "view_count",
            "cave__id",
            "cave__name",
            "cave__location__id",
            "cave__location__country_text",
            "cave__location__state_text",
            "cave__location__region_text",
            "search_vector",
        )
        .select_related(
            "cave",
            "cave__location",
        )
        .prefetch_related("tags")
    )

    search_query = None
    if q:
        SearchQuery.record_search(q)
        search_query = PgSearchQuery(q, search_type="websearch")
        queryset = queryset.filter(
            Q(search_vector=search_query) | Q(cave__name__icontains=q) | Q(tags__name__icontains=q)
        ).distinct()

    total = queryset.count()
    offset = (page - 1) * page_size
    order_prefix = "" if sort_order == "asc" else "-"

    items: list[IncidentListSchema]
    if sort_by == SortBy.RELEVANCE and search_query:
        ranked_qs = queryset.annotate(
            rank=SearchRank(F("search_vector"), search_query),
            popularity_boost=Ln(F("view_count") + 2),
            relevance=F("rank") + F("popularity_boost") * 0.1,
        ).order_by(f"{order_prefix}relevance", "-date")[offset : offset + page_size]
        items = [
            IncidentListSchema.from_incident(i, relevance_score=round(i.relevance, 2))
            for i in ranked_qs
        ]
    elif sort_by == SortBy.POPULARITY:
        items = [
            IncidentListSchema.from_incident(i)
            for i in queryset.order_by(f"{order_prefix}view_count", "-date")[
                offset : offset + page_size
            ]
        ]
    elif sort_by == SortBy.TITLE:
        items = [
            IncidentListSchema.from_incident(i)
            for i in queryset.order_by(f"{order_prefix}title", "-date")[offset : offset + page_size]
        ]
    elif sort_by == SortBy.CAVE_NAME:
        items = [
            IncidentListSchema.from_incident(i)
            for i in queryset.order_by(f"{order_prefix}cave__name", "-date")[
                offset : offset + page_size
            ]
        ]
    else:
        items = [
            IncidentListSchema.from_incident(i)
            for i in queryset.order_by(f"{order_prefix}date")[offset : offset + page_size]
        ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )


@router.get("/suggestions", response=SuggestionSchema)
def get_suggestions(
    request: HttpRequest,
    q: Annotated[str, Query(description="Partial search query", min_length=2)],
    limit: Annotated[int, Query(ge=1, le=20)] = 8,
) -> SuggestionSchema:
    normalized = q.lower().strip()

    suggestions = list(
        SearchQuery.objects.filter(query__istartswith=normalized)
        .order_by("-query_count")
        .values_list("query", flat=True)[:limit]
    )

    if len(suggestions) < limit:
        containing = list(
            SearchQuery.objects.filter(query__icontains=normalized)
            .exclude(query__istartswith=normalized)
            .order_by("-query_count")
            .values_list("query", flat=True)[: limit - len(suggestions)]
        )
        suggestions.extend(containing)

    return SuggestionSchema(suggestions=suggestions)


@router.get("/did-you-mean", response=DidYouMeanSchema)
def get_did_you_mean(
    request: HttpRequest,
    q: Annotated[str, Query(description="Search query to check", min_length=2)],
) -> DidYouMeanSchema:
    normalized = q.lower().strip()

    similar = (
        SearchQuery.objects.annotate(similarity=TrigramSimilarity("query", normalized))
        .filter(similarity__gt=0.3)
        .exclude(query=normalized)
        .order_by("-similarity", "-query_count")
        .values("query", "similarity")
        .first()
    )

    if similar:
        return DidYouMeanSchema(
            suggestion=similar["query"],
            similarity=round(similar["similarity"], 2),
        )

    return DidYouMeanSchema(suggestion=None, similarity=None)


@router.post("/click", response=ClickTrackSchema)
def track_click(request: HttpRequest, payload: ClickTrackRequest) -> ClickTrackSchema:
    if not Incident.objects.filter(pk=payload.incident_id).exists():
        return ClickTrackSchema(success=False)

    SearchClick.record_click(
        query=payload.query, incident_id=payload.incident_id, position=payload.position
    )
    return ClickTrackSchema(success=True)


@router.get("/{incident_id}", response=IncidentDetailSchema)
def get_incident(request: HttpRequest, incident_id: int) -> IncidentDetailSchema:
    Incident.increment_view_count(incident_id)
    incident = get_object_or_404(
        Incident.objects.select_related(
            "cave",
            "cave__location",
            "cave__location__canonical_area",
            "origin",
        ).prefetch_related(
            "tags",
            "references",
        ),
        pk=incident_id,
    )

    return IncidentDetailSchema.from_incident(incident)
