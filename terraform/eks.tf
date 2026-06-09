resource "aws_eks_cluster" "coldchain" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster_role.arn

  vpc_config {
    subnet_ids              = aws_subnet.public[*].id
    endpoint_public_access  = true
    endpoint_private_access = false
  }

  access_config {
    authentication_mode                         = "API_AND_CONFIG_MAP"
    bootstrap_cluster_creator_admin_permissions = true
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy
  ]

  tags = {
    Name      = var.cluster_name
    Project   = "ColdChainRiskMonitor"
    ManagedBy = "Terraform"
  }
}

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.coldchain.name
  node_group_name = "coldchain-node-group"
  node_role_arn   = aws_iam_role.eks_node_role.arn
  subnet_ids      = aws_subnet.public[*].id

  instance_types = var.node_instance_types
  capacity_type  = "SPOT"
  disk_size      = 20

  scaling_config {
    desired_size = var.node_desired_size
    min_size     = var.node_min_size
    max_size     = var.node_max_size
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.ecr_readonly_policy
  ]

  tags = {
    Name      = "coldchain-node-group"
    Project   = "ColdChainRiskMonitor"
    ManagedBy = "Terraform"
  }
}