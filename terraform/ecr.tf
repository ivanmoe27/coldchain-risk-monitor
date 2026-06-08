resource "aws_ecr_repository" "coldchain_app" {
  name         = var.ecr_repository_name
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project   = "ColdChainRiskMonitor"
    ManagedBy = "Terraform"
  }
}