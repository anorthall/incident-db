locals {
  default_ttl = 300
  server_ip_addresses = {
    "A"    = aws_eip.nss_incidents_eip.public_ip
    "AAAA" = module.nss_incidents_ec2.ipv6_addresses[0]
  }
}

resource "aws_route53_delegation_set" "nss_incidents" {
  reference_name = "nss-incidents"
}

output "nameservers" {
  value       = aws_route53_delegation_set.nss_incidents.name_servers
  description = "Nameservers for the root domain"
}

resource "aws_route53_zone" "nss_incidents" {
  name              = var.root_domain_name
  delegation_set_id = aws_route53_delegation_set.nss_incidents.id
}

resource "aws_route53_record" "frontend_dns_records" {
  for_each = toset(["A", "AAAA"])

  zone_id = aws_route53_zone.nss_incidents.zone_id
  name    = var.frontend_domain_name
  type    = each.key

  alias {
    name                   = aws_cloudfront_distribution.cdn.domain_name
    zone_id                = aws_cloudfront_distribution.cdn.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "api_dns_records" {
  for_each = local.server_ip_addresses

  zone_id = aws_route53_zone.nss_incidents.zone_id
  name    = var.api_domain_name
  type    = each.key
  ttl     = local.default_ttl
  records = [each.value]
}

resource "aws_route53_record" "origin_dns_records" {
  for_each = local.server_ip_addresses

  zone_id = aws_route53_zone.nss_incidents.zone_id
  name    = var.origin_domain_name
  type    = each.key
  ttl     = local.default_ttl
  records = [each.value]
}
