module "wildcard_cert" {
  source  = "terraform-aws-modules/acm/aws"
  version = "6.3.0"

  domain_name                 = var.frontend_domain_name
  zone_id                     = aws_route53_zone.nss_incidents.zone_id
  subject_alternative_names   = ["*.${var.frontend_domain_name}"]
  validation_method           = "DNS"
  create_route53_records_only = true
  wait_for_validation         = true

  providers = {
    aws = aws.use1
  }
}
