"""Deterministic Terraform Infrastructure-as-Code Skeleton Generator for SAE v2."""

from __future__ import annotations

from typing import Any, Dict


def generate_terraform_scaffold(
    system_name: str,
    cloud_lld: Dict[str, Any],
) -> str:
    """Generate complete Terraform main.tf configuration based on Cloud LLD topology."""
    provider = cloud_lld.get("cloud_provider", "AWS").upper()
    sys_slug = system_name.lower().replace(" ", "_")

    tf = f"""# ==============================================================================
# Terraform Infrastructure Provisioning for {system_name}
# Generated deterministically by SAE v2 Pipeline
# Provider: {provider}
# ==============================================================================

terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
  backend "s3" {{
    bucket         = "{sys_slug}-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "{sys_slug}-terraform-locks"
  }}
}}

provider "aws" {{
  region = var.aws_region
  default_tags {{
    tags = {{
      Project     = "{system_name}"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }}
  }}
}}

# ─── VPC & Networking Tier ───────────────────────────────────────────────────

resource "aws_vpc" "main" {{
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {{
    Name = "{sys_slug}-vpc"
  }}
}}

resource "aws_subnet" "public_a" {{
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${{var.aws_region}}a"
  map_public_ip_on_launch = true
  tags = {{ Name = "{sys_slug}-public-a" }}
}}

resource "aws_subnet" "public_b" {{
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${{var.aws_region}}b"
  map_public_ip_on_launch = true
  tags = {{ Name = "{sys_slug}-public-b" }}
}}

resource "aws_subnet" "private_a" {{
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = "${{var.aws_region}}a"
  tags = {{ Name = "{sys_slug}-private-a" }}
}}

resource "aws_subnet" "private_b" {{
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.20.0/24"
  availability_zone = "${{var.aws_region}}b"
  tags = {{ Name = "{sys_slug}-private-b" }}
}}

# ─── Application Load Balancer ───────────────────────────────────────────────

resource "aws_lb" "api_alb" {{
  name               = "{sys_slug}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}}

resource "aws_security_group" "alb_sg" {{
  name        = "{sys_slug}-alb-sg"
  description = "Allow inbound HTTPS/HTTP traffic"
  vpc_id      = aws_vpc.main.id

  ingress {{
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}

  ingress {{
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}

  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}

# ─── ECS Cluster & Fargate Service ───────────────────────────────────────────

resource "aws_ecs_cluster" "app_cluster" {{
  name = "{sys_slug}-ecs-cluster"
  setting {{
    name  = "containerInsights"
    value = "enabled"
  }}
}}

resource "aws_ecs_task_definition" "api_task" {{
  family                   = "{sys_slug}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {{
      name      = "{sys_slug}-api"
      image     = "${{var.ecr_image_uri}}:latest"
      essential = true
      portMappings = [
        {{
          containerPort = 8000
          hostPort      = 8000
        }}
      ]
      healthCheck = {{
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/live || exit 1"]
        interval    = 15
        timeout     = 5
        retries     = 3
        startPeriod = 10
      }}
      logConfiguration = {{
        logDriver = "awslogs"
        options = {{
          awslogs-group         = "/ecs/{sys_slug}-api"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }}
      }}
    }}
  ])
}}

# ─── Amazon RDS PostgreSQL Database ──────────────────────────────────────────

resource "aws_db_subnet_group" "db_subnet_grp" {{
  name       = "{sys_slug}-db-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}}

resource "aws_db_instance" "postgres" {{
  identifier             = "{sys_slug}-postgres-db"
  allocated_storage      = 20
  max_allocated_storage  = 100
  engine                 = "postgres"
  engine_version         = "16.1"
  instance_class         = "db.t4g.micro"
  db_name                = "{sys_slug}_db"
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.db_subnet_grp.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  multi_az               = true
  storage_encrypted      = true
  skip_final_snapshot    = false
  final_snapshot_identifier = "{sys_slug}-final-snapshot"
}}

resource "aws_security_group" "db_sg" {{
  name        = "{sys_slug}-db-sg"
  description = "Restrict access strictly to ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {{
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_sg.id]
  }}
}}

# ─── Variables & Outputs ─────────────────────────────────────────────────────

variable "aws_region" {{
  type    = string
  default = "us-east-1"
}}

variable "environment" {{
  type    = string
  default = "production"
}}

variable "db_username" {{
  type    = string
  default = "postgres_admin"
}}

variable "db_password" {{
  type      = string
  sensitive = true
}}

variable "ecr_image_uri" {{
  type = string
}}

output "alb_dns_name" {{
  value       = aws_lb.api_alb.dns_name
  description = "Public DNS address of Application Load Balancer"
}}

output "database_endpoint" {{
  value       = aws_db_instance.postgres.endpoint
  description = "Primary RDS PostgreSQL database endpoint"
}}
"""
    return tf
