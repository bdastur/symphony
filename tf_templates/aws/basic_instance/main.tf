provider "aws" {
    region = "${var.region}"
    shared_credentials_file = "${var.aws_credentials_file}"
    profile = "${var.aws_profile}"
}


#--------------------------------------
# AWS Accesskey.
module "keypair" {
    source = "{{ keypair_module_source }}"

    key_name = "${var.key_name}"
    public_key = "${file(var.public_key)}"
}

