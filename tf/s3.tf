module "cdn_bucket" {
  source           = "terraform-aws-modules/s3-bucket/aws"
  bucket           = "nss-incidents-cdn"
  attach_policy    = true
  policy           = data.aws_iam_policy_document.cdn_bucket_cloudfront_access_policy.json
  object_ownership = "BucketOwnerEnforced"
  version          = "5.10.0"

  versioning = {
    enabled = true
  }

  lifecycle_rule = [
    {
      id      = "DeleteOldVersions"
      enabled = true
      filter  = { prefix = "" }
      noncurrent_version_expiration = {
        days = 90
      }
    },
  ]

  cors_rule = [
    {
      allowed_methods = ["GET"]
      allowed_origins = ["*"]
      allowed_headers = ["*"]
      max_age_seconds = 300
    }
  ]
}

module "data_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  bucket  = "nss-incidents-data"
  version = "5.10.0"

  versioning = {
    enabled = true
  }

  lifecycle_rule = [
    {
      id      = "DeleteOldVersions"
      enabled = true
      filter  = { prefix = "" }
      noncurrent_version_expiration = {
        days = 365
      }
    },
  ]
}

module "backup_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  bucket  = "nss-incidents-backups"
  version = "5.10.0"

  versioning = {
    enabled = true
  }

  lifecycle_rule = [
    {
      id      = "DeleteOldVersions"
      enabled = true
      filter  = { prefix = "" }
      noncurrent_version_expiration = {
        days = 365
      }
    },
  ]
}

module "tfstate_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  bucket  = "nss-incidents-tfstate"
  version = "5.10.0"

  versioning = {
    enabled = true
  }

  lifecycle_rule = [
    {
      id      = "DeleteOldVersions"
      enabled = true
      filter  = { prefix = "" }
      noncurrent_version_expiration = {
        days = 90
      }
    },
  ]
}
