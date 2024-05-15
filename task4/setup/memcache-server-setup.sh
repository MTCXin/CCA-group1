#!/bin/bash

sudo apt update
sudo apt install -y python3 python3-pip memcached libmemcached-tools 
# sudo snap install docker
pip3 install psutil docker

sudo systemctl status memcached
sudo vim /etc/memcached.conf
sudo systemctl restart memcached
sudo systemctl status memcached
#sudo usermod -aG docker $USER
#newgrp docker
#docker run hello-world

# docker pull anakli/parsec:dedup-native-reduced 
# docker pull anakli/parsec:splash2x-fft-native-reduced 
# docker pull anakli/parsec:blackscholes-native-reduced 
# docker pull anakli/parsec:canneal-native-reduced 
# docker pull anakli/parsec:freqmine-native-reduced 
# docker pull anakli/parsec:ferret-native-reduced
