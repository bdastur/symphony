#!/bin/bash

###########################################################
# Symphony - Setup Script.
# -----------------------
# Platform: Linux. 
#
# The script setups up environment for symphony generator.
#
#
###########################################################

curdir=`pwd`
tfdir="${curdir}/tf"
logsdir=".logs"
setup_logs="${logsdir}/setup.logs"

# Terraform Ansible Dynamic Inventory Repo.
tf_ansible_repo="https://github.com/bdastur/terraform.py.git"
tf_ansible_branch="master"
tf_ansible_localdir="../tf_ansible"

# Ansible Repo.
ansible_repo="http://github.com/ansible/ansible.git"
ansible_branch="stable-1.9"
ansible_localdir="../ansible_stable19"

# Function to display logs to console and
# file.
function echox ()
{
    local messages=$@
    echo $messages | tee -a ${setup_logs} 
}

# Function to generate ssh keypair.
# The keypairs by default are generated as symphony_accesskey
function generate_ssh_keypair ()
{
    echox "------------------------------------"
    echox "Generate ssh KeyPair: Start"
    
    echo -n "Generate new ssh keypair ('y' to generate)?: "
    read userinput

    if [[ ${userinput} != "y" ]]; then
        echox "Do not generate any ssh keypairs"
        return
    fi

    ssh_key_dir="${curdir}/.ssh"
    if [[ ! -d $ssh_key_dir ]]; then
        mkdir $ssh_key_dir
    fi

    echo -n "Default (${ssh_key_dir}/symphony_accesskey): "; read privkey_name

    if [[ -z $privkey_name ]]; then
        echo "choose default"
        privkey_name="${ssh_key_dir}/symphony_accesskey"
    fi

    #######################################################
    # Generate a new key pair
    #######################################################
    if [[ ! -e ${privkey_name} ]]; then
        keygen_log=$(ssh-keygen -t rsa -N "" -f ${privkey_name})
        echo $keygen_log  >> $setup_logs 2>&1
    else
        echox "Keys with $privkey_name already exists. We will not overwrite"
    fi

    tf_accesskey=$(cat ${privkey_name}.pub)
    export TF_VAR_public_key=${tf_accesskey}
    echox "Generate ssh KeyPair: Done"
    echox ""
}


# Function to setup terraform
function setup_terraform ()
{
    tf_zip="terraform_0.7.4_linux_amd64.zip"
    tf_download_zip="https://releases.hashicorp.com/terraform/0.7.4/${tf_zip}"

    echox "------------------------------------"
    echox "Setup Terraform. Version: $tf_zip: Start"

    #######################################################
    # Setup Terraform.
    #######################################################
    if [[ ! -d ${tfdir} ]]; then
        echox "$tfdir does not exist. Creating it"
        mkdir ${tfdir}

        wget ${tf_download_zip} \
            --output-document=${tfdir}/${tf_zip}  >> $setup_logs 2>&1

        unzip ${tfdir}/${tf_zip} -d ${tfdir}  >> $setup_logs 2>&1
    fi
    export PATH=$PATH:${tfdir}
    echox "Setup Terraform. Version: $tf_zip: Done"
    echox ""
}


# The function pulls a git repository
# :params
#   $1: reponame
#   $2: localdir
#   $3: branch
# It skips pulling the repo if the local dir
# already exists.
function git_pull () 
{
    gitrepo=$1
    localgitrepo=$2
    branch=$3

    if [[ ! -z $branch ]]; then
        branch="-b $branch"
    fi

    echo -n "pulling repo: [$gitrepo]  "
    if [[ ! -d $localgitrepo ]]; then 
        echo "Pulling $gitrepo $branch"  >> $setup_logs 2>&1
        git clone $gitrepo $branch $localgitrepo  >> $setup_logs 2>&1
    fi

    if [[ -d $localgitrepo ]]; then
        echox " ---> [DONE]"
    else
        echox " ---> [FAILED]";echo
        echox "Error logs: $setup_logs"
    fi
}

function show_banner()
{
    echo "=================================="
    echo " Symphony:"
    echo " ---------"
    echo " Framework to deploy and manage services in a simple and "
    echo " cloud agnostic way, allowing more modular approach and ability"
    echo " to duplicate environments quickly"
    echo ""
    echo " Setup:"
    echo "=================================="
    echo " This setup script will deploy and setup the various dependencies"
    echo " needed to run symphony."
    echo ""
}

#######################################################
# Symphony setup script.
# -----------------------------------------------------
# Symphony has a few simple goals:
# 
# - Abstract the details of the cloud from the consumer who is trying 
#   to consume the resources.
#
# - Allow for reusable templates to seamlessly spin up new clusters
#   for services.
#
#
#
#######################################################
if [[ ! -d $logsdir ]]; then
        mkdir $logsdir
fi

start_time=$(date +"%b-%d-%y %H%M%S")
echo "----------------------------------------------" >> $setup_logs 2>&1
echo "Start Setup Run: $start_time" >> $setup_logs 2>&1
echo "" >> $setup_logs 2>&1


show_banner
sleep 1


#######################################################
# Setup Terraform.
#######################################################
setup_terraform

#######################################################
# Generate a new key pair
#######################################################
generate_ssh_keypair


#################################################
# Clone other repositories:
# - terraform ansible dynamic inventory
# - Ansible repo.
################################################
git_pull ${tf_ansible_repo} ${tf_ansible_localdir} ${tf_ansible_branch}
git_pull ${ansible_repo} ${ansible_localdir} ${ansible_branch}

# Add the Ansible submodules
cd ${ansible_localdir}
git submodule update --init --recursive  > /dev/null
cd ${curdir}

echo -n "Do you want to specify any additional git repo for your environments? ('y'): "
read userinput
if [[ ${userinput} == "y" ]]; then
    echo -n "git repo: "; read user_repo 
    echo -n "branch: "; read branch

    localpath="../usergitrepo_${branch}"
    git_pull ${user_repo} ${localpath} ${branch}
fi


# Env Setup.
export ANSIBLE_HOST_KEY_CHECKING=False
# Set pythonpath.
export PYTHONPATH=${PYTHONPATH}:${curdir}



