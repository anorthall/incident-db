data "aws_caller_identity" "current" {}

locals {
  parameter_prefix = "arn:aws:ssm:us-west-2:${data.aws_caller_identity.current.account_id}:parameter/cidb/prod"
}

data "aws_iam_policy_document" "app" {
  source_policy_documents = [
    data.aws_iam_policy_document.s3_write["cdn"].json,
    data.aws_iam_policy_document.s3_read["data"].json,
    data.aws_iam_policy_document.s3_write["backup"].json,
  ]

  statement {
    sid = "CIDBReadParameters"
    actions = [
      "ssm:GetParametersByPath",
      "ssm:GetParameters",
    ]
    resources = [local.parameter_prefix, "${local.parameter_prefix}/*"]
  }

  statement {
    sid       = "CIDBDecryptParameters"
    actions   = ["kms:Decrypt"]
    resources = ["arn:aws:kms:us-west-2:${data.aws_caller_identity.current.account_id}:key/*"]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ssm.us-west-2.amazonaws.com"]
    }
  }
}

resource "aws_iam_policy" "app" {
  name        = "cidb-app"
  description = "Instance permissions for the CIDB application server"
  policy      = data.aws_iam_policy_document.app.json
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"] # pragma: allowlist secret
}

data "aws_iam_policy_document" "github_deploy_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:anorthall/incident-db:environment:production"]
    }
  }
}

data "aws_iam_policy_document" "github_deploy" {
  statement {
    sid       = "SyncFrontendBucket"
    actions   = ["s3:ListBucket"]
    resources = [module.frontend_bucket.s3_bucket_arn]
  }

  statement {
    sid = "WriteFrontendObjects"
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = ["${module.frontend_bucket.s3_bucket_arn}/*"]
  }

  statement {
    sid       = "InvalidateDistribution"
    actions   = ["cloudfront:CreateInvalidation"]
    resources = [aws_cloudfront_distribution.cdn.arn]
  }

  statement {
    sid     = "SendDeployCommand"
    actions = ["ssm:SendCommand"]
    resources = [
      module.nss_incidents_ec2.arn,
      "arn:aws:ssm:us-west-2::document/AWS-RunShellScript",
    ]
  }

  statement {
    sid = "ReadCommandStatus"
    actions = [
      "ssm:GetCommandInvocation",
      "ssm:ListCommands",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role" "github_deploy" {
  name               = "cidb-github-deploy"
  description        = "Role assumed by GitHub Actions to deploy CIDB"
  assume_role_policy = data.aws_iam_policy_document.github_deploy_assume.json
}

resource "aws_iam_role_policy" "github_deploy" {
  name   = "cidb-github-deploy"
  role   = aws_iam_role.github_deploy.id
  policy = data.aws_iam_policy_document.github_deploy.json
}
