#!/bin/bash

sudo apt update
sudo apt install -y python3 python3-pip memcached libmemcached-tools 

sudo apt-get update
sudo apt-get install apt-transport-https ca-certificates curl software-properties-common
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo docker --version

pip3 install psutil docker

sudo systemctl status memcached
sudo usermod -a -G docker ubuntu

echo Exit and restart such that changes can be applied


#newgrp docker
#docker run hello-world

# docker pull anakli/parsec:dedup-native-reduced 
# docker pull anakli/parsec:splash2x-fft-native-reduced 
# docker pull anakli/parsec:blackscholes-native-reduced 
# docker pull anakli/parsec:canneal-native-reduced 
# docker pull anakli/parsec:freqmine-native-reduced 
# docker pull anakli/parsec:ferret-native-reduced
