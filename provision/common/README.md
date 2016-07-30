How to Run:

export TERRAFORM_STATE_ROOT=/home/user1/symphonydir/
ansible-playbook \
    -i ../../../tf_ansible/terraform.py provision.yaml \
    -e "hosts=all username=ec2-user" \
    --private-key=../../tf_accesskey


