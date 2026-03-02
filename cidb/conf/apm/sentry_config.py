import os


def configure_sentry() -> None:
    if sentry_dsn := os.getenv("SENTRY_DSN", None):
        import sentry_sdk
        from sentry_sdk.integrations.anthropic import AnthropicIntegration
        from sentry_sdk.integrations.asyncio import AsyncioIntegration
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.openai import OpenAIIntegration
        from sentry_sdk.integrations.pydantic_ai import PydanticAIIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                DjangoIntegration(),
                AsyncioIntegration(),
                PydanticAIIntegration(),
                OpenAIIntegration(),
                AnthropicIntegration(),
            ],
            traces_sample_rate=0.1,
            send_default_pii=True,
        )
