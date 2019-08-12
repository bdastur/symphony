variable "HOME" {
  default = "$HOME"
}

variable "profile" {
  type = "string"
  default = "default"
}

variable "region" {
  type    = "string"
  default = "us-west-2"
}

variable "create_vpc" {
  type = "string"
}

variable "enable_network_acl" {
  type = "string"
}
