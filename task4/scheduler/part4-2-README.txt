
# These are the instructions to run part 4.3

# make sure you are in the folder "scheduler"
> export KOPS_STATE_STORE=<your-gcp-state-store> # e.g. gs://cca-eth-2024-group-1-keuscha/
> export KOPS_STATE_STORE=gs://cca-eth-2024-group-1-keuscha/ 
> PROJECT='gcloud config get-value project'

> ./../setup/start-cluster.sh

# to get names and IPs
> kubectl get nodes -o wide 

# upload setup scripts
gcloud compute scp --scp-flag=-r ../setup/ ubuntu@memcache-server-62bj:/home/ubuntu/ --zone europe-west3-a
gcloud compute scp --scp-flag=-r ../scheduler/ ubuntu@memcache-server-62bj:/home/ubuntu/ --zone europe-west3-a
gcloud compute scp --scp-flag=-r ../setup/ ubuntu@client-agent-zt6m:/home/ubuntu/ --zone europe-west3-a
gcloud compute scp --scp-flag=-r ../setup/ ubuntu@client-measure-0r2f:/home/ubuntu/ --zone europe-west3-a

gcloud compute scp --scp-flag=-r scheduler_2.py ubuntu@memcache-server-62bj:/home/ubuntu/scheduler/scheduler_2.py --zone europe-west3-a
gcloud compute scp --scp-flag=-r ubuntu@memcache-server-62bj:/home/ubuntu/log20240517_064541.txt log.txt --zone europe-west3-a

# connecting to machine template
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@<MACHINE_NAME> --zone europe-west3-a

# connecting to machines
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-agent-zt6m --zone europe-west3-a
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-measure-0r2f --zone europe-west3-a
# execute this on client AND measure
> ./setup/memcache-agent-measure-setup.sh

# connect to and execute this on memcache-server
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@memcache-server-62bj --zone europe-west3-a
> ./setup/memcache-server-setup.sh
> sudo vim /etc/memcached.conf # update the file content as described below
    # update line starting with "-m" to "-m 1024"
    # add a new line "-t 2"
    # update line starting with "-l" to "-l 10.0.16.7" [MEMCAHED_INTERNAL_IP]
    # save file and close it
> sudo systemctl restart memcached
> sudo systemctl status memcached # make sure the changes have been applied

# experimentName can be freely chosen and will be used in logs and in the result folder name
> ./run_experiment.sh 10.0.16.3 10.0.16.5 sm0x 98fd wq3t schedulerme
# when prompted to do so, execute this on memcache-server
> python3 scheduler/scheduler.py
# wait until run_experiment.sh (don't kill it otherwise the logs from measure are lost!!)

# copy the scheduler log file to the results folder created by run_experiment.sh
gcloud compute scp --scp-flag=-r ubuntu@memcache-server-62bj:/home/ubuntu/log20240517_064541.txt log.txt --zone europe-west3-a

NAME                         STATUS   ROLES           AGE     VERSION   INTERNAL-IP   EXTERNAL-IP      OS-IMAGE             KERNEL-VERSION   CONTAINER-RUNTIME
client-agent-zt6m            Ready    node            29s     v1.28.6   10.0.16.3     35.234.125.174   Ubuntu 22.04.3 LTS   6.5.0-1013-gcp   containerd://1.7.13
client-measure-0r2f          Ready    node            31s     v1.28.6   10.0.16.4     34.159.41.97     Ubuntu 22.04.3 LTS   6.5.0-1013-gcp   containerd://1.7.13
master-europe-west3-a-stvk   Ready    control-plane   3m45s   v1.28.6   10.0.16.2     34.159.136.219   Ubuntu 22.04.3 LTS   6.5.0-1013-gcp   containerd://1.7.13
memcache-server-62bj         Ready    node            28s     v1.28.6   10.0.16.5     35.242.201.107   Ubuntu 22.04.3 LTS   6.5.0-1013-gcp   containerd://1.7.13
