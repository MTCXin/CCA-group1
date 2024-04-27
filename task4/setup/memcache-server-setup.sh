#!/bin/bash

sudo apt update
sudo apt install -y python3 python3-pip memcached libmemcached-tools
pip3 install psutil

sudo systemctl status memcached
sudo vim /etc/memcached.conf
sudo systemctl restart memcached
sudo systemctl status memcached
