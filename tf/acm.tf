module "wildcard_cert" {
  source  = "terraform-aws-modules/acm/aws"
  version = "6.3.1"

  domain_name               = var.frontend_domain_name
  subject_alternative_names = ["*.${var.frontend_domain_name}"]
  validation_method         = "DNS"
  create_route53_records    = false
  validation_record_fqdns   = [for record in cloudflare_dns_record.acm_validation : record.name]
  wait_for_validation       = true

  providers = {
    aws = aws.use1
  }
}
