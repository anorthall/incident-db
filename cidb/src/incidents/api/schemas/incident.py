from ninja import Schema

from cidb.src.incidents.api.schemas.common import ImpreciseDateSchema
from cidb.src.incidents.models import Incident


class TagSchema(Schema):
    id: int
    name: str


class LocationSchema(Schema):
    id: int
    country: str
    state: str
    region: str
    latitude: float | None = None
    longitude: float | None = None


class CaveSchema(Schema):
    id: int
    name: str
    location: LocationSchema | None = None


class PublicationSchema(Schema):
    id: int
    title: str


class IncidentReferenceSchema(Schema):
    author: str
    title: str
    source: str
    raw_citation: str


class IncidentListSchema(Schema):
    id: int
    title: str
    date: ImpreciseDateSchema | None
    cave_name: str
    location_summary: str
    summary: str
    tags: list[TagSchema]
    view_count: int
    relevance_score: float | None = None

    @staticmethod
    def from_incident(
        incident: Incident, relevance_score: float | None = None
    ) -> IncidentListSchema:
        location_parts = []
        if incident.cave and incident.cave.location:
            loc = incident.cave.location
            if loc.region_text:
                location_parts.append(loc.region_text)
            if loc.state_text:
                location_parts.append(loc.state_text)
            if loc.country_text:
                location_parts.append(loc.country_text)

        return IncidentListSchema(
            id=incident.id,
            title=incident.title,
            date=ImpreciseDateSchema.from_imprecise_date(incident.date),
            cave_name=incident.cave.name if incident.cave else "",
            location_summary=", ".join(location_parts),
            summary=incident.summary,
            tags=[TagSchema(id=t.id, name=t.name) for t in incident.tags.all()],
            view_count=incident.view_count,
            relevance_score=relevance_score,
        )


class IncidentDetailSchema(Schema):
    id: int
    title: str
    date: ImpreciseDateSchema | None
    time: str | None = None
    cave: CaveSchema | None = None
    report: str
    analysis: str
    summary: str
    tags: list[TagSchema]
    origin_publication: PublicationSchema | None = None
    references: list[IncidentReferenceSchema]
    created_at: str
    updated_at: str

    @staticmethod
    def from_incident(incident: Incident) -> IncidentDetailSchema:
        cave_schema = None
        if incident.cave:
            location_schema = None
            if incident.cave.location:
                loc = incident.cave.location
                location_schema = LocationSchema(
                    id=loc.id,
                    country=loc.country_text,
                    state=loc.state_text,
                    region=loc.region_text,
                    latitude=float(loc.latitude) if loc.latitude else None,
                    longitude=float(loc.longitude) if loc.longitude else None,
                )
            cave_schema = CaveSchema(
                id=incident.cave.id,
                name=incident.cave.name,
                location=location_schema,
            )

        references = [
            IncidentReferenceSchema(
                author=ref.author,
                title=ref.title,
                source=ref.source,
                raw_citation=ref.raw_citation,
            )
            for ref in incident.references.all()
        ]

        return IncidentDetailSchema(
            id=incident.id,
            title=incident.title,
            date=ImpreciseDateSchema.from_imprecise_date(incident.date),
            time=str(incident.time) if incident.time else None,
            cave=cave_schema,
            report=incident.report,
            analysis=incident.analysis,
            summary=incident.summary,
            tags=[TagSchema(id=t.id, name=t.name) for t in incident.tags.all()],
            origin_publication=PublicationSchema(id=incident.origin.id, title=incident.origin.title)
            if incident.origin
            else None,
            references=references,
            created_at=incident.created_at.isoformat(),
            updated_at=incident.updated_at.isoformat(),
        )
