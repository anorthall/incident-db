import os


def configure_logfire() -> None:
    if not os.getenv("LOGFIRE_TOKEN"):
        return

    import logfire

    logfire.configure(
        token=os.getenv("LOGFIRE_TOKEN", ""),
        environment=os.getenv("LOGFIRE_ENV", "local"),
    )
    logfire.instrument_pydantic_ai()
    logfire.instrument_django()
    logfire.instrument_psycopg()
    logfire.instrument_redis()
    logfire.instrument_pydantic()
    logfire.instrument_system_metrics()
