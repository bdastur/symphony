#---------------------------------------------
# EC2 Instance.

resource "aws_instance" "basic-instance" {
    ami = "${var.ami}"
    instance_type = "${var.instance_type}"
    key_name = "${var.key_name}"
    availability_zone = "${var.availability_zone}"
    monitoring = "${var.instance_monitoring}"
    vpc_security_group_ids = ["${split(",", "${var.vpc_security_group_ids}")}"]
    subnet_id = "${var.subnet_id}"
    user_data = "${file("${var.cloud_config_file}")}"

    root_block_device = {
        volume_type = "${var.root_ebs_type}"
        volume_size = "${var.root_ebs_size}"
        delete_on_termination = "${var.root_ebs_delete_on_termination}"
    }

    tags = {
        Name = "${var.tag_name}"
        sshPrivateIp = "true"
    } 
}

