terraform {
  required_version = "1.13.2"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.71.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "5.28.1"
    }
  }

  backend "s3" {
    bucket       = "nss-incidents-tfstate"
    key          = "terraform.tfstate"
    region       = "us-west-2"
    use_lockfile = true
  }
}

provider "cloudflare" {}

provider "aws" {
  region = "us-west-2"
  default_tags {
    tags = {
      Service = "CIDB"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  alias  = "use1"
  default_tags {
    tags = {
      Service = "CIDB"
    }
  }
}
