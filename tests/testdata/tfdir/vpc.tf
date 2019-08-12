resource "aws_vpc" "test_vpc" {
  cidr_block                     = "10.0.0.0/16"
  enable_classiclink             = false
  enable_classiclink_dns_support = false
  enable_dns_hostnames           = true
  enable_dns_support             = true
  instance_tenancy               = "default"

  tags = {
    ClusterOwner     = "Behzad"
    ClusterStartedBy = "behzad.dastur"
    Name             = "brdtest101"
  }
}

