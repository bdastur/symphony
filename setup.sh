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

tf_download_zip="https://releases.hashicorp.com/terraform/0.6.16/terraform_0.6.16_linux_amd64.zip"

# Terraform Ansible Dynamic Inventory Repo.
tf_ansible_repo="https://github.com/bdastur/terraform.py.git"
tf_ansible_branch="master"
tf_ansible_localdir="../tf_ansible"

# Ansible Repo.
ansible_repo="http://github.com/ansible/ansible.git"
ansible_branch="stable-1.9"
ansible_localdir="../ansible_stable19"

curdir=`pwd`
tfdir="${curdir}/tf"


# Set pythonpath.
export PYTHONPATH=${PYTHONPATH}:${curdir}


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
        echo "Pulling $gitrepo $branch" 
        git clone $gitrepo $branch $localgitrepo 
    fi

    if [[ -d $localgitrepo ]]; then
        echo " ---> [DONE]"
    else
        echo " ---> [FAILED]";echo
        echo "Error logs: $setup_logs"
    fi
}

#######################################################
# Setup Terraform.
#######################################################
if [[ ! -d ${tfdir} ]]; then
    echo "$tfdir does not exist"
    mkdir ${tfdir}

    wget ${tf_download_zip} \
        --output-document=${tfdir}/terraform_0.6.16_linux_amd64.zip

    unzip ${tfdir}/terraform_0.6.16_linux_amd64.zip -d ${tfdir} 
fi
export PATH=$PATH:${tfdir}

#######################################################
# Generate a new key pair
#######################################################
if [[ ! -e $curdir/tf_accesskey ]]; then
    ssh-keygen -t rsa -N "" -f $curdir/tf_accesskey
fi

tf_accesskey=$(cat $curdir/tf_accesskey.pub)
export TF_VAR_public_key=${tf_accesskey}


#################################################
# Clone - terraform ansible dynamic inventory
################################################
git_pull ${tf_ansible_repo} ${tf_ansible_localdir} ${tf_ansible_branch}

#################################################
# Clone - Ansible repo.
################################################
git_pull ${ansible_repo} ${ansible_localdir} ${ansible_branch}

# Add the Ansible submodules
cd ${ansible_localdir}
git submodule update --init --recursive
cd ${curdir}

# Env Setup.
export ANSIBLE_HOST_KEY_CHECKING=False





