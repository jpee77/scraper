from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.operations import sudo
from paramiko import RSAKey

env.roledefs = {
    'test': ['localhost'],
    'aws': ['ubuntu@ec2-107-22-132-139.compute-1.amazonaws.com'],
    'staging': [''],
    'production': ['']
} 

def dev_server():
    env.user = 'ubuntu'
    env.hosts = ['ec2-107-22-132-139.compute-1.amazonaws.com']

def install_req_apt():
    sudo("export DEBIAN_FRONTEND=noninteractive")
    sudo("apt-get update && apt-get install git python-setuptools redis-server -qqy")
    
def install_py_req():
    sudo("easy_install redis")
    sudo("easy_install beautifulsoup")
    
def test():
    with settings(warn_only=True):
        result = local("python ~/projects/scraper/main.py -v -d 1 -u http://www.google.com", capture=True)
    if result.failed and not confirm("Tests failed. Continue anyway?"):
        abort("Aborting at user request.")

def commit():
    local("git add -p && git commit")

def push():
    local("branch newQ")
    local("git push origin")

def git_it():
    commit()
    push()
    
def trac():
    sudo("sudo apt-get install python python-setuptools python-genshi")
    sudo("easy_install Trac==1.0")
    sudo("trac-admin /opt/trac initenv")
    
def deploy_first():

    install_req_apt()
    install_py_req()
    
    code_dir = '/opt/scraper'
    
    with settings(warn_only=True):
        if sudo("test -d %s" % code_dir).failed:
            sudo("git clone https://github.com/jpee77/scraper.git %s" % code_dir)
    with cd(code_dir):
        sudo("git pull")

def deploy():

    code_dir = '/opt/scraper'
    
    with settings(warn_only=True):
        if sudo("test -d %s" % code_dir).failed:
            sudo("git clone https://github.com/jpee77/scraper.git %s" % code_dir)
    with cd(code_dir):
        sudo("git pull origin newQ")
