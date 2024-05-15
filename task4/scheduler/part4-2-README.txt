
# These are the instructions to run part 4.3

# make sure you are in the folder "scheduler"
> export KOPS_STATE_STORE=<your-gcp-state-store> # e.g. gs://cca-eth-2024-group-1-keuscha/
> export KOPS_STATE_STORE=gs://cca-eth-2024-group-1-keuscha/ 
> PROJECT='gcloud config get-value project'

> ./../setup/start-cluster.sh

> kubectl get nodes -o wide # to get names and IPs

# upload setup scripts
gcloud compute scp --scp-flag=-r ../setup/ ubuntu@memcache-server-wf21:/home/ubuntu/ --zone europe-west3-a
gcloud compute scp --scp-flag=-r ../scheduler/ ubuntu@memcache-server-wf21:/home/ubuntu/ --zone europe-west3-a
gcloud compute scp --scp-flag=-r ../setup/ ubuntu@client-agent-b9zq:/home/ubuntu/ --zone europe-west3-a
gcloud compute scp --scp-flag=-r ../setup/ ubuntu@client-measure-ws12:/home/ubuntu/ --zone europe-west3-a

# connecting to machine template
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@<MACHINE_NAME> --zone europe-west3-a

# connecting to machines
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-agent-b9zq --zone europe-west3-a
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-measure-ws12 --zone europe-west3-a
# execute this on client AND measure
> ./setup/memcache-agent-measure-setup.sh

# connect to and execute this on memcache-server
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@memcache-server-wf21 --zone europe-west3-a
> ./setup/memcache-server-setup.sh
> sudo vim /etc/memcached.conf # update the file content as described below
    # update line starting with "-m" to "-m 1024"
    # add a new line "-t 2"
    # update line starting with "-l" to "-l 10.0.16.4" [MEMCAHED_INTERNAL_IP]
    # save file and close it
> sudo systemctl restart memcached
> sudo systemctl status memcached # make sure the changes have been applied

# experimentName can be freely chosen and will be used in logs and in the result folder name
> ./run_experiment.sh 10.0.16.4 10.0.16.3 b9zq ws12 vksf experimentName
# when prompted to do so, execute this on memcache-server
> python3 scheduler/scheduler.py
# once it finished, make sure that run_experiment.sh finishes as well (this saves the log files)

# TODO: copy the scheduler_logger file from memcache-server to the local results folder created by run_experiment.sh

NAME                         STATUS   ROLES           AGE   VERSION   INTERNAL-IP   EXTERNAL-IP      OS-IMAGE
  KERNEL-VERSION   CONTAINER-RUNTIME
client-agent-b9zq            Ready    node            73s   v1.28.6   10.0.16.3     35.246.237.32    Ubuntu 22.04.3 LTS   6.5.0-1013-gcp   containerd://1.7.13
client-measure-ws12          Ready    node            71s   v1.28.6   10.0.16.5     34.159.196.1     Ubuntu 22.04.3 LTS   6.5.0-1013-gcp   containerd://1.7.13
master-europe-west3-a-f90n   Ready    control-plane   4m    v1.28.6   10.0.16.2     35.234.80.77     Ubuntu 22.04.3 LTS   6.5.0-1013-gcp   containerd://1.7.13
memcache-server-wf21         Ready    node            69s   v1.28.6   10.0.16.4     35.246.158.154   Ubuntu 22.04.3 LTS   6.5.0-1013-gcp   containerd://1.7.13