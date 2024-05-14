#!/bin/bash

kops create -f part4.yaml
kops create secret --name part4.k8s.local sshpublickey admin -i ~/.ssh/cloud-computing.pub
kops update cluster --name part4.k8s.local --yes --admin
kops validate cluster --wait 10m

kubectl get nodes -o wide