# -*- mode: ruby -*-
# vi: set ft=ruby :

# This file is for use by Vagrant (http://www.vagrantup.com/).
# It will establish a debian-based (Ubuntu) virtual machine for development.

# The virtual machine environment attempts to match the production environment 
# as closely as possible.

# This file was generated by `vagrant up` and consequently modified.

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

# Copy the vagrant SSH key into the VM so vagrant can SSH to localhost within
# the VM. Continued in the shell script below.
# http://serverfault.com/questions/491343/how-can-i-move-my-deploy-key-into-vagrant#comment549259_491345
git_ssh_key = File.read(ENV['HOME'] + '/.vagrant.d/insecure_private_key');

# build a shell script that installs prereqs, configures the database, sets up
# the user/group associations, pulls in the code from the host machine, sets up
# some external dependency configs, and then runs fabric.
shellscript = <<SCRIPT
cat >>/home/vagrant/.ssh/insecure_private_key <<EOF
#{git_ssh_key}
EOF
chown vagrant:vagrant /home/vagrant/.ssh/insecure_private_key
chmod 600 /home/vagrant/.ssh/insecure_private_key
cat >>/home/vagrant/.ssh/config <<EOF
Host localhost
    User vagrant
    IdentityFile ~/.ssh/insecure_private_key

Host 127.0.0.1
    User vagrant
    IdentityFile ~/.ssh/insecure_private_key
EOF
chmod 644 /home/vagrant/.ssh/config

apt-get update
apt-get upgrade -y
apt-get install -y python-pip postgresql python-virtualenv virtualenvwrapper \
                   git nginx postgresql-server-dev-9.1 libxslt1-dev \
                   libxml2-dev libmemcached-dev python-dev rabbitmq-server \
                   p7zip-full

echo "CREATE USER vagrant WITH CREATEROLE LOGIN; CREATE DATABASE karmaworld OWNER vagrant;" | su postgres -c "psql"

mkdir -m 775 -p /var/www
chown -R :www-data /var/www
usermod -a -G www-data vagrant

su vagrant -c "git clone /vagrant karmaworld"

SECRETPATH="karmaworld/karmaworld/secret"
CFILE="$SECRETPATH/db_settings.py"
cat > $CFILE <<CONFIG
#!/usr/bin/env python
# -*- coding:utf8 -*-
# Copyright (C) 2012  FinalsClub Foundation
"""
DO NOT check this file into source control.
"""
PROD_DB_NAME = 'karmaworld'
PROD_DB_USERNAME = 'vagrant'
PROD_DB_PASSWORD = ''
CONFIG
cp $SECRETPATH/filepicker.py.example $SECRETPATH/filepicker.py
cp $SECRETPATH/static_s3.py.example $SECRETPATH/static_s3.py
chown vagrant:vagrant $SECRETPATH/*.py

cat > /etc/nginx/sites-available/karmaworld <<CONFIG
server {
    listen 80;
    # don't do virtual hosting, handle all requests regardless of header
    server_name "";
    client_max_body_size 20M;

    location / {
        # pass traffic through to gunicorn
        proxy_pass http://127.0.0.1:8000;
    }
}
CONFIG
rm /etc/nginx/sites-enabled/default
ln -s /etc/nginx/sites-available/karmaworld /etc/nginx/sites-enabled/karmaworld
sudo service nginx restart

cp karmaworld/confs/prod/supervisor /etc/init.d
chmod 755 /etc/init.d/supervisor
update-rc.d supervisor defaults

pip install fabric
su vagrant -c "cd karmaworld; fab -H 127.0.0.1 first_deploy"
SCRIPT
# end of script

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # All Vagrant configuration is done here. The most common configuration
  # options are documented and commented below. For a complete reference,
  # please see the online documentation at vagrantup.com.

  # Every Vagrant virtual environment requires a box to build off of.
  config.vm.box = "Official Ubuntu 12.04 daily Cloud Image i386"
  #config.vm.box = "Official Ubuntu 12.04 daily Cloud Image amd64"
  #config.vm.box = "Official Ubuntu 12.10 daily Cloud Image i386"
  #config.vm.box = "Official Ubuntu 12.10 daily Cloud Image amd64"
  #config.vm.box = "Official Ubuntu 13.04 daily Cloud Image i386"
  #config.vm.box = "Official Ubuntu 13.04 daily Cloud Image amd64"
  #config.vm.box = "Official Ubuntu 13.10 daily Cloud Image i386"
  #config.vm.box = "Official Ubuntu 13.10 daily Cloud Image amd64"

  # The url from where the 'config.vm.box' box will be fetched if it
  # doesn't already exist on the user's system.
  config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/precise/current/precise-server-cloudimg-i386-vagrant-disk1.box"
  #config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/precise/current/precise-server-cloudimg-amd64-vagrant-disk1.box"
  #config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/quantal/current/quantal-server-cloudimg-i386-vagrant-disk1.box"
  #config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/quantal/current/quantal-server-cloudimg-amd64-vagrant-disk1.box"
  #config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/raring/current/raring-server-cloudimg-i386-vagrant-disk1.box"
  #config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/raring/current/raring-server-cloudimg-amd64-vagrant-disk1.box"
  #config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/saucy/current/saucy-server-cloudimg-i386-vagrant-disk1.box"
  #config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/saucy/current/saucy-server-cloudimg-amd64-vagrant-disk1.box"

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network :forwarded_port, guest: 80, host: 8080

  # OM (sanskrit) KW (KarmaWorld) on a phone: 66 59
  config.vm.network :forwarded_port, guest: 80, host: 6659, auto_correct: true

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  #config.vm.network :private_network, ip: "192.168.66.59"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # Used to directly access the internet for downloading updates and so forth.
  config.vm.network :public_network

  # If true, then any SSH connections made will enable agent forwarding.
  # Default value: false
  # config.ssh.forward_agent = true

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Setup scripts
  config.vm.provision "shell", inline: shellscript

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  # config.vm.provider :virtualbox do |vb|
  #   # Don't boot with headless mode
  #   vb.gui = true
  #
  #   # Use VBoxManage to customize the VM. For example to change memory:
  #   vb.customize ["modifyvm", :id, "--memory", "1024"]
  # end
  #
  # View the documentation for the provider you're using for more
  # information on available options.

  # Enable provisioning with Puppet stand alone.  Puppet manifests
  # are contained in a directory path relative to this Vagrantfile.
  # You will need to create the manifests directory and a manifest in
  # the file base.pp in the manifests_path directory.
  #
  # An example Puppet manifest to provision the message of the day:
  #
  # # group { "puppet":
  # #   ensure => "present",
  # # }
  # #
  # # File { owner => 0, group => 0, mode => 0644 }
  # #
  # # file { '/etc/motd':
  # #   content => "Welcome to your Vagrant-built virtual machine!
  # #               Managed by Puppet.\n"
  # # }
  #
  # config.vm.provision :puppet do |puppet|
  #   puppet.manifests_path = "manifests"
  #   puppet.manifest_file  = "site.pp"
  # end

  # Enable provisioning with chef solo, specifying a cookbooks path, roles
  # path, and data_bags path (all relative to this Vagrantfile), and adding
  # some recipes and/or roles.
  #
  # config.vm.provision :chef_solo do |chef|
  #   chef.cookbooks_path = "../my-recipes/cookbooks"
  #   chef.roles_path = "../my-recipes/roles"
  #   chef.data_bags_path = "../my-recipes/data_bags"
  #   chef.add_recipe "mysql"
  #   chef.add_role "web"
  #
  #   # You may also specify custom JSON attributes:
  #   chef.json = { :mysql_password => "foo" }
  # end

  # Enable provisioning with chef server, specifying the chef server URL,
  # and the path to the validation key (relative to this Vagrantfile).
  #
  # The Opscode Platform uses HTTPS. Substitute your organization for
  # ORGNAME in the URL and validation key.
  #
  # If you have your own Chef Server, use the appropriate URL, which may be
  # HTTP instead of HTTPS depending on your configuration. Also change the
  # validation key to validation.pem.
  #
  # config.vm.provision :chef_client do |chef|
  #   chef.chef_server_url = "https://api.opscode.com/organizations/ORGNAME"
  #   chef.validation_key_path = "ORGNAME-validator.pem"
  # end
  #
  # If you're using the Opscode platform, your validator client is
  # ORGNAME-validator, replacing ORGNAME with your organization name.
  #
  # If you have your own Chef Server, the default validation client name is
  # chef-validator, unless you changed the configuration.
  #
  #   chef.validation_client_name = "ORGNAME-validator"
end
