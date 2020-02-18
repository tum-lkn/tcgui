# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "debian/contrib-jessie64"

  config.vm.define "sender" do |cfg|
    config.vm.provision "shell", inline: <<-SHELL
            apt update
            apt install -y iproute python3 python3-flask iperf3
    SHELL
    cfg.vm.network "private_network", ip: "192.168.210.2"
  end

  config.vm.define "receiver" do |cfg|
    config.vm.provision "shell", inline: <<-SHELL
            apt update
            apt install -y iperf3
    SHELL
    cfg.vm.network "private_network", ip: "192.168.210.3"
  end
end
