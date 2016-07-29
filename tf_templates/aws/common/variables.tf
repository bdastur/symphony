# Global.
variable "region" {
    description = "AWS Region"
    default = "us-east-1"
}

variable "aws_credentials_file" {
    description = "AWS Credentials File"
}

variable "aws_profile" {
    description = "AWS Credentails profile"
}

#----------------------------------
# SSH Key.
variable "key_name" {
    description = "SSH Key Name"
}

variable "public_key" {
    description = "SSH Public Key"
}


#------------------------------------
# Security Group
variable "sg_name" {
    description = "Security Group Name"
}

variable "sg_description" {
    descripton = "Security Group Description"
}

variable "sg_cidr_blocks" {
    default = "0.0.0.0/0"
}

#------------------------------------
# VPC:

variable "vpc_id" {
    description = "AWS VPC Id"
}

#------------------------------------
# Identification Tags

variable "tag_name" {
    description = "Name of the instance in this case"
}

