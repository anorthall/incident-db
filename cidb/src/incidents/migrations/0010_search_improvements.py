from typing import Any

from django.apps.registry import Apps
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations, models


def repopulate_search_vectors(apps: Apps, schema_editor: Any) -> None:
    from django.contrib.postgres.search import SearchVector

    Incident = apps.get_model("incidents", "Incident")
    Incident.objects.update(
        search_vector=SearchVector("title", weight="A")
        + SearchVector("summary", weight="B")
        + SearchVector("report", weight="C")
        + SearchVector("analysis", weight="D")
    )


class Migration(migrations.Migration):
    dependencies = [
        ("incidents", "0009_add_search_vector"),
    ]

    operations = [
        # 1.2 Enable trigram extension for fuzzy search
        TrigramExtension(),
        # 1.1 Update search vector trigger to include analysis field
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION incidents_search_vector_trigger()
            RETURNS trigger AS $$
            BEGIN
                NEW.search_vector :=
                    setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
                    setweight(to_tsvector('english', COALESCE(NEW.summary, '')), 'B') ||
                    setweight(to_tsvector('english', COALESCE(NEW.report, '')), 'C') ||
                    setweight(to_tsvector('english', COALESCE(NEW.analysis, '')), 'D');
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS incidents_search_vector_update ON incidents_incident;
            CREATE TRIGGER incidents_search_vector_update
            BEFORE INSERT OR UPDATE OF title, summary, report, analysis
            ON incidents_incident
            FOR EACH ROW
            EXECUTE FUNCTION incidents_search_vector_trigger();
            """,
            reverse_sql="""
            CREATE OR REPLACE FUNCTION incidents_search_vector_trigger()
            RETURNS trigger AS $$
            BEGIN
                NEW.search_vector :=
                    setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
                    setweight(to_tsvector('english', COALESCE(NEW.summary, '')), 'B') ||
                    setweight(to_tsvector('english', COALESCE(NEW.report, '')), 'C');
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS incidents_search_vector_update ON incidents_incident;
            CREATE TRIGGER incidents_search_vector_update
            BEFORE INSERT OR UPDATE OF title, summary, report
            ON incidents_incident
            FOR EACH ROW
            EXECUTE FUNCTION incidents_search_vector_trigger();
            """,
        ),
        # Repopulate search vectors with new weights
        migrations.RunPython(repopulate_search_vectors, migrations.RunPython.noop),
        # 1.2 Trigram indexes for fuzzy search on title and cave name
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS incidents_incident_title_trgm
            ON incidents_incident USING gin (title gin_trgm_ops);
            """,
            reverse_sql="DROP INDEX IF EXISTS incidents_incident_title_trgm;",
        ),
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS incidents_cave_name_trgm
            ON incidents_cave USING gin (name gin_trgm_ops);
            """,
            reverse_sql="DROP INDEX IF EXISTS incidents_cave_name_trgm;",
        ),
        # 1.3 Composite indexes for common filter combinations
        migrations.AddIndex(
            model_name="incident",
            index=models.Index(fields=["date", "cave"], name="incidents_incident_date_cave"),
        ),
        migrations.AddIndex(
            model_name="incident",
            index=models.Index(fields=["origin", "date"], name="incidents_incident_origin_date"),
        ),
        # 5.4 Click-through tracking model
        migrations.CreateModel(
            name="SearchClick",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                (
                    "query",
                    models.CharField(
                        max_length=500, help_text="The search query that led to this click"
                    ),
                ),
                (
                    "position",
                    models.PositiveSmallIntegerField(help_text="Position in search results"),
                ),
                ("clicked_at", models.DateTimeField(auto_now_add=True)),
                (
                    "incident",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="search_clicks",
                        to="incidents.incident",
                    ),
                ),
            ],
            options={
                "verbose_name": "search click",
                "verbose_name_plural": "search clicks",
                "indexes": [
                    models.Index(fields=["query"], name="incidents_searchclick_query"),
                    models.Index(fields=["clicked_at"], name="incidents_searchclick_time"),
                ],
            },
        ),
        # Index on SearchQuery for suggestions
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS incidents_searchquery_query_trgm
            ON incidents_searchquery USING gin (query gin_trgm_ops);
            """,
            reverse_sql="DROP INDEX IF EXISTS incidents_searchquery_query_trgm;",
        ),
    ]
