locals {
  s3_buckets = {
    cdn    = module.cdn_bucket.s3_bucket_arn
    data   = module.data_bucket.s3_bucket_arn
    backup = module.backup_bucket.s3_bucket_arn
  }
}

data "aws_iam_policy_document" "s3_read" {
  for_each = local.s3_buckets

  statement {
    sid = "CIDBS3BucketRead"
    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation",
    ]
    resources = [each.value]
  }

  statement {
    sid = "CIDBS3BucketReadObjects"
    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
    ]
    resources = ["${each.value}/*"]
  }
}

data "aws_iam_policy_document" "s3_write" {
  for_each = local.s3_buckets

  statement {
    sid = "CIDBS3ListBucket"
    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation",
    ]
    resources = [each.value]
  }

  statement {
    sid = "CIDBS3BucketWriteObjects"
    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:DeleteObjectVersion",
    ]
    resources = ["${each.value}/*"]
  }
}

resource "aws_iam_policy" "s3_read" {
  for_each = local.s3_buckets

  name        = "cidb-${each.key}-s3-read"
  description = "Read access to the ${each.key} S3 bucket"
  policy      = data.aws_iam_policy_document.s3_read[each.key].json
}

resource "aws_iam_policy" "s3_write" {
  for_each = local.s3_buckets

  name        = "cidb-${each.key}-s3-write"
  description = "Write access to the ${each.key} S3 bucket"
  policy      = data.aws_iam_policy_document.s3_write[each.key].json
}

data "aws_iam_policy_document" "cdn_bucket_cloudfront_access_policy" {
  statement {
    sid       = "AllowCloudFrontCDNGetObject"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = [module.cdn_bucket.s3_bucket_arn, "${module.cdn_bucket.s3_bucket_arn}/*"]

    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.cdn.iam_arn]
    }
  }
}
