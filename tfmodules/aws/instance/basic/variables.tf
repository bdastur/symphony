variable "key_name" {
    description = "SSH Key Name"
}

variable "cloud_config_file" {
    description = "Path to cloud config file"
}

#------------------------------------
# VPC:

variable "vpc_id" {
    description = "AWS VPC Id"
}

#----------------------------------
# EC2.

variable "availability_zone" {
    description = "AWS Availability zone to create instance in"
}

variable "instance_monitoring" {
    description = "EC2 Instnace Monitoring"
}

variable "vpc_security_group_ids" {
    description = "List of VPC Security Group IDS to attach to the Instance"
}

variable "ami" {
    description = "AWS AMI ID"
}

variable "subnet_id" {
    description = "VPC Subnet ID to launch in"
}
variable "instance_type" {
    description = "Instance type eg. t1.micro, t2.small"
    default = "t2.small"
}

variable "root_ebs_type" {
    description = "ROot EBS Volume Type"
    default = "standard"
}

variable "root_ebs_size" {
    description = "ROot EBS Volume size"
    default = 40
}

variable "root_ebs_delete_on_termination" {
    description = "Delete Root EBS Volume on Instance termination"
    default = true
}

variable "cloud_config_file" {
    description = "Path to the cloud config script, that is passed as user data"
}


#-------------------------------------
# Tags.
variable "tag_name" {
    description = "Name of the instance in this case"
}

