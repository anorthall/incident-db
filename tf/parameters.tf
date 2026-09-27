// Secret values are created as a literal "placeholder" and set once out of band
// with put-parameter, so they never enter Terraform state or this repository.
// deploy.sh refuses to start while any required value is still "placeholder", so
// a first boot fails loudly rather than serving traffic with a publicly known
// SECRET_KEY. ACME_EMAIL is not secret but only the operator knows it.
//
// Non-secret values Terraform already knows are seeded with their real values, so
// they need no manual step and cannot be left as a placeholder that reaches the
// application. ignore_changes means a value edited by hand is never reverted.
data "aws_region" "current" {}

locals {
  secure_parameters = {
    SECRET_KEY        = "placeholder" # pragma: allowlist secret
    POSTGRES_PASSWORD = "placeholder" # pragma: allowlist secret
    SENTRY_DSN        = "placeholder" # pragma: allowlist secret
    LOGFIRE_TOKEN     = "placeholder" # pragma: allowlist secret
    OPENAI_API_KEY    = "placeholder" # pragma: allowlist secret
    SENTRY_CRON_URL   = "placeholder" # pragma: allowlist secret
  }

  string_parameters = {
    ACME_EMAIL              = "placeholder"
    API_DOMAIN              = var.api_domain_name
    DJANGO_ALLOWED_HOSTS    = "${var.api_domain_name},${var.frontend_domain_name}"
    CSRF_TRUSTED_ORIGINS    = "https://${var.frontend_domain_name},https://${var.api_domain_name}"
    CORS_ALLOWED_ORIGINS    = "https://${var.frontend_domain_name}"
    AWS_STORAGE_BUCKET_NAME = module.cdn_bucket.s3_bucket_id
    AWS_S3_REGION_NAME      = data.aws_region.current.region
    AWS_S3_CUSTOM_DOMAIN    = "${var.frontend_domain_name}/cdn"
    BACKUP_BUCKET           = module.backup_bucket.s3_bucket_id
    WEB_CONCURRENCY         = "3"
  }
}

resource "aws_ssm_parameter" "secure" {
  for_each = local.secure_parameters

  name  = "/cidb/prod/${each.key}"
  type  = "SecureString"
  value = each.value

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "string" {
  for_each = local.string_parameters

  name  = "/cidb/prod/${each.key}"
  type  = "String"
  value = each.value

  lifecycle {
    ignore_changes = [value]
  }
}
