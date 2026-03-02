resource "awscc_ec2_key_pair" "nss_incidents_key" {
  key_name            = "nss-incidents"
  key_format          = "pem"
  public_key_material = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB1ucb7/nrAvFlQsB9LNgmLFYVivjudL6cfXdUtp2+6M"

  lifecycle {
    ignore_changes = [public_key_material, key_type]
  }
}

resource "aws_eip" "nss_incidents_eip" {
  instance = module.nss_incidents_ec2.id
}

data "aws_ami" "debian_13" {
  most_recent = true
  owners      = ["136693071363"]

  filter {
    name   = "name"
    values = ["debian-13-arm64-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

module "nss_incidents_ec2" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "6.2.0"

  ami = data.aws_ami.debian_13.id

  name                        = "nss-incidents"
  instance_type               = "m8g.large"
  key_name                    = awscc_ec2_key_pair.nss_incidents_key.key_name
  monitoring                  = true
  disable_api_stop            = true
  disable_api_termination     = true
  create_iam_instance_profile = true
  enable_primary_ipv6         = true
  ipv6_address_count          = 1

  subnet_id              = module.vpc.public_subnets[0]
  vpc_security_group_ids = [aws_security_group.nss_incidents_sg.id]

  root_block_device = {
    volume_size           = 200
    volume_type           = "gp3"
    delete_on_termination = false
  }
}

resource "aws_security_group" "nss_incidents_sg" {
  name        = "nss-incidents-sg"
  description = "Security group for NSS Incidents EC2 instance"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description      = "Allow HTTP"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  ingress {
    description      = "Allow HTTPS"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  ingress {
    description      = "Allow SSH"
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    description      = "Allow all outbound traffic"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
    protocol         = "-1"
  }
}
