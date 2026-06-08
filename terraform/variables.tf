variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
}

variable "ecr_repository_name" {
  description = "Name of the ECR repository for the FastAPI application image"
  type        = string
}