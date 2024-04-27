
> export KOPS_STATE_STORE=<your-gcp-state-store> # e.g. gs://cca-eth-2024-group-1-keuscha/
> PROJECT='gcloud config get-value project'

> ./setup/start-cluster.sh

# connecting to machine
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-agent-xcr4 --zone europe-west3-a
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-measure-m49m --zone europe-west3-a
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@memcache-server-b9xd --zone europe-west3-a
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@<MACHINE_NAME> --zone europe-west3-a

# upload setup scripts
gcloud compute scp --scp-flag=-r setup/ ubuntu@memcache-server-b9xd:/home/ubuntu/ --zone europe-west3-a
gcloud compute scp cpu_utilization.py ubuntu@memcache-server-b9xd:/home/ubuntu/ --zone europe-west3-a
gcloud compute scp --scp-flag=-r setup/ ubuntu@client-agent-xcr4:/home/ubuntu/ --zone europe-west3-a
gcloud compute scp --scp-flag=-r setup/ ubuntu@client-measure-m49m:/home/ubuntu/ --zone europe-west3-a



# execute this on client and measure
> ./setup/memcache-agent-measure-setup.sh

# execute this on memcache-server
> ./setup/memcache-server-setup.sh
> sudo vim /etc/memcached.conf
> sudo systemctl restart memcached
> sudo systemctl status memcached # this gives you the PID
> sudo taskset -a -cp 0 [PID]

# then start the experiment, NUM_THREADS has to be identical to what was defined in /etc/memcached.conf
> ./question1.sh [INTERNAL-MEMCACHE-IP] [INTERNAL_AGENT_IP] [AGENT_NAME] [MEASURE_NAME] [NUM_THREADS] [TASKSET_CPUS] [MEMCACHE_SERVER_NAME]
> ./question1.sh 10.0.16.2 10.0.16.4 xcr4 m49m 2 0 b9xd


NAME                         STATUS   ROLES           AGE     VERSION   INTERNAL-IP   EXTERNAL-IP      OS-IMAGE             KERNEL-VERSION   CONTAINER-RUNTIME
client-agent-xcr4            Ready    node            30s     v1.28.6   10.0.16.4     35.242.245.190   Ubuntu 22.04.3 LTS   6.5.0-1013-gcp   containerd://1.7.13
client-measure-m49m          Ready    node            35s     v1.28.6   10.0.16.3     34.159.180.229   Ubuntu 22.04.3 LTS   6.5.0-1013-gcp   containerd://1.7.13
master-europe-west3-a-pl90   Ready    control-plane   2m59s   v1.28.6   10.0.16.5     34.89.187.187    Ubuntu 22.04.3 LTS   6.5.0-1013-gcp   containerd://1.7.13
memcache-server-b9xd         Ready    node            30s     v1.28.6   10.0.16.2     34.159.75.36     Ubuntu 22.04.3 LTS   6.5.0-1013-gcp   containerd://1.7.13



PID 7154