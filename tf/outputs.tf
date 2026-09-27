output "instance_id" {
  description = "EC2 instance ID for SSM commands and sessions"
  value       = module.nss_incidents_ec2.id
}

output "deploy_role_arn" {
  description = "IAM role ARN that GitHub Actions assumes via OIDC"
  value       = aws_iam_role.github_deploy.arn
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for invalidations"
  value       = aws_cloudfront_distribution.cdn.id
}

output "frontend_bucket" {
  description = "S3 bucket the SPA is synced to"
  value       = module.frontend_bucket.s3_bucket_id
}
