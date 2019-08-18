provider "aws" {
  region                  = "${var.region}"
  shared_credentials_file = "${var.HOME}/.aws/credentials"
  profile                 = "${var.profile}"
  version                 = "~> 2.24"
}


