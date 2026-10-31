locals {
  default_ttl = 300
  server_ip_addresses = {
    "A"    = aws_eip.nss_incidents_eip.public_ip
    "AAAA" = module.nss_incidents_ec2.ipv6_addresses[0]
  }
}

resource "cloudflare_dns_record" "frontend" {
  zone_id = var.cloudflare_zone_id
  name    = var.frontend_domain_name
  type    = "CNAME"
  content = aws_cloudfront_distribution.cdn.domain_name
  ttl     = local.default_ttl
  proxied = false
}

resource "cloudflare_dns_record" "api" {
  for_each = local.server_ip_addresses

  zone_id = var.cloudflare_zone_id
  name    = var.api_domain_name
  type    = each.key
  content = each.value
  ttl     = local.default_ttl
  proxied = false
}

resource "cloudflare_dns_record" "acm_validation" {
  for_each = {
    for option in module.wildcard_cert.acm_certificate_domain_validation_options :
    trimsuffix(option.resource_record_name, ".") => trimsuffix(option.resource_record_value, ".")...
  }

  zone_id = var.cloudflare_zone_id
  name    = each.key
  type    = "CNAME"
  content = each.value[0]
  ttl     = local.default_ttl
  proxied = false
}
