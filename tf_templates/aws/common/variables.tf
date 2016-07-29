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

