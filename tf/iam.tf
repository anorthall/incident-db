resource "aws_iam_user" "app" {
  name = "cidb-app"
}

resource "aws_iam_user_policy_attachment" "app_cdn_write" {
  user       = aws_iam_user.app.name
  policy_arn = aws_iam_policy.s3_write["cdn"].arn
}

resource "aws_iam_user_policy_attachment" "app_data_read" {
  user       = aws_iam_user.app.name
  policy_arn = aws_iam_policy.s3_read["data"].arn
}

resource "aws_iam_access_key" "app" {
  user = aws_iam_user.app.name
}

output "app_access_key_id" {
  description = "Access key ID for the app user"
  value       = aws_iam_access_key.app.id
}

output "app_secret_access_key" {
  description = "Secret access key for the app user"
  value       = aws_iam_access_key.app.secret
  sensitive   = true
}
