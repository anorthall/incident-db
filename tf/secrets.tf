resource "aws_secretsmanager_secret" "openai_api_key" {
  name        = "nss-incidents-openai-api-key"
  description = "OpenAI API key for NSS Incident Database"
}

resource "aws_secretsmanager_secret" "discord_bot_token" {
  name        = "nss-incidents-discord-bot-token"
  description = "Discord bot token for NSS Incident Database"
}

resource "aws_secretsmanager_secret" "sentry_dsn" {
  name        = "nss-incidents-sentry-dsn"
  description = "Sentry DSN for NSS Incident Database"
}

resource "aws_secretsmanager_secret" "django_secret_key" {
  name        = "nss-incidents-django-secret-key"
  description = "Django secret key for NSS Incident Database"
}
