locals {
  vpc_cidr    = "10.1.0.0/16"
  vpc_zones   = 2
  vpc_num_azs = 3
}

data "aws_availability_zones" "available" {}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "6.6.0"

  name = "nss-incidents-vpc"
  cidr = local.vpc_cidr

  azs = slice(data.aws_availability_zones.available.names, 0, local.vpc_num_azs)

  public_subnets              = [for i in range(local.vpc_zones) : cidrsubnet(local.vpc_cidr, 5, 0 * local.vpc_zones + i)]
  enable_ipv6                 = true
  public_subnet_ipv6_prefixes = [for i in range(local.vpc_zones) : i]

  enable_dns_hostnames = true
  enable_dns_support   = true
}
