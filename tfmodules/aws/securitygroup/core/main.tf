#--------------------------------------
# AWS Security Group

resource "aws_security_group" "sg_core" {
    name = "${var.sg_name}"
    description = "${var.sg_description}"
    vpc_id = "${var.vpc_id}"

    tags = { 
        Name = "${var.tag_name}"
    }   
}

resource "aws_security_group_rule" "inbound_allow_22" {
    type = "ingress"
    from_port = 22 
    to_port = 22 
    protocol = "tcp"
    cidr_blocks = [
        "${split(",", "${var.sg_cidr_blocks}")}"]
    security_group_id = "${aws_security_group.sg_core.id}"
}

resource "aws_security_group_rule" "output_allow_all" {
    type  = "egress"
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    security_group_id = "${aws_security_group.sg_core.id}"
}

