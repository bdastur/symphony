#------------------------------------
# Security Group
variable "sg_name" {
    description = "Security Group Name"
}

variable "sg_description" {
    descripton = "Security Group Description"
}

variable "sg_cidr_blocks" {
    description = "CIDR list: eg: 192.0.0.0/8,100.10.0.0/10,172.122.24.0/24"
    default = "0.0.0.0/0"
}

#------------------------------------

variable "vpc_id" {
    description = "AWS VPC Id"
}


#-------------------------------------
# Tags.
variable "tag_name" {
    description = "Name of the instance in this case"
}

