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


#--------------------------------------
# AWS Security Group
module "core_sg" {
    source = "{{ sg_core_module_source }}"

    sg_name = "${var.sg_name}-core"
    sg_description = "${var.sg_description}"
    vpc_id = "${var.vpc_id}"

    tag_name = "${var.tag_name}"
}

module "http_sg" {
    source = "{{ sg_http_module_source }}"

    sg_name = "${var.sg_name}-http"
    sg_description = "${var.sg_description}"
    vpc_id = "${var.vpc_id}"

    tag_name = "${var.tag_name}"
}




