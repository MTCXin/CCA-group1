
> export KOPS_STATE_STORE=<your-gcp-state-store> # e.g. gs://cca-eth-2024-group-1-keuscha/
> export KOPS_STATE_STORE=gs://cca-eth-2024-group-1-keuscha/ 
> PROJECT='gcloud config get-value project'

> ./../setup/start-cluster.sh

# connecting to machine
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-agent-xcr4 --zone europe-west3-a
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-measure-m49m --zone europe-west3-a
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@memcache-server-b9xd --zone europe-west3-a
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@<MACHINE_NAME> --zone europe-west3-a

# upload setup scripts
gcloud compute scp --scp-flag=-r ../setup/ ubuntu@memcache-server-XXXX:/home/ubuntu/ --zone europe-west3-a
gcloud compute scp scheduler/scheduler.py ubuntu@memcache-server-XXXX:/home/ubuntu/ --zone europe-west3-a
gcloud compute scp --scp-flag=-r ../setup/ ubuntu@client-agent-XXXX:/home/ubuntu/ --zone europe-west3-a
gcloud compute scp --scp-flag=-r ../setup/ ubuntu@client-measure-XXXX:/home/ubuntu/ --zone europe-west3-a


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
