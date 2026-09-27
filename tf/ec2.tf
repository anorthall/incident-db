resource "aws_eip" "nss_incidents_eip" {
  instance = module.nss_incidents_ec2.id
}

data "aws_ssm_parameter" "al2023_arm64" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

module "nss_incidents_ec2" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "6.4.1"

  ami  = data.aws_ssm_parameter.al2023_arm64.value
  name = "nss-incidents"

  instance_type               = var.instance_type
  monitoring                  = true
  disable_api_stop            = true
  disable_api_termination     = true
  create_iam_instance_profile = true
  enable_primary_ipv6         = true
  ipv6_address_count          = 1

  iam_role_policies = {
    ssm = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
    app = aws_iam_policy.app.arn
  }

  subnet_id              = module.vpc.public_subnets[0]
  vpc_security_group_ids = [aws_security_group.nss_incidents_sg.id]

  user_data_replace_on_change = true
  user_data = templatefile("${path.module}/../deploy/cloud-init.yaml", {
    compose_version = "v2.40.3"
  })

  root_block_device = {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }
}

resource "aws_ebs_volume" "data" {
  availability_zone = module.nss_incidents_ec2.availability_zone
  size              = 10
  type              = "gp3"
  encrypted         = true

  tags = {
    Name   = "nss-incidents-data"
    Backup = "cidb-data"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_volume_attachment" "data" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.data.id
  instance_id = module.nss_incidents_ec2.id
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
    description      = "Allow HTTP/3"
    from_port        = 443
    to_port          = 443
    protocol         = "udp"
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

data "aws_iam_policy_document" "dlm_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["dlm.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "dlm" {
  name               = "cidb-dlm-lifecycle"
  description        = "Role used by Data Lifecycle Manager to snapshot the data volume"
  assume_role_policy = data.aws_iam_policy_document.dlm_assume.json
}

resource "aws_iam_role_policy_attachment" "dlm" {
  role       = aws_iam_role.dlm.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSDataLifecycleManagerServiceRole"
}

resource "aws_dlm_lifecycle_policy" "data_volume" {
  description        = "Weekly snapshots of the CIDB data volume"
  execution_role_arn = aws_iam_role.dlm.arn
  state              = "ENABLED"

  policy_details {
    resource_types = ["VOLUME"]
    target_tags    = { Backup = "cidb-data" }

    schedule {
      name = "weekly"

      create_rule {
        cron_expression = "cron(0 4 ? * SUN *)"
      }

      retain_rule {
        count = 4
      }

      copy_tags = true
    }
  }
}
