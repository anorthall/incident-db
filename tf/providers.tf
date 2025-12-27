terraform {
  required_version = "1.14.3"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.28.0"
    }
  }

  backend "s3" {
    bucket       = "nss-incidents-tfstate"
    key          = "terraform.tfstate"
    region       = "us-west-2"
    use_lockfile = true
  }
}

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
