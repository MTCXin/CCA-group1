
> export KOPS_STATE_STORE=<your-gcp-state-store> # e.g. gs://cca-eth-2024-group-1-keuscha/
> PROJECT='gcloud config get-value project'

> ./setup/start-cluster.sh

# connecting to machine
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@<MACHINE_NAME> --zone europe-west3-a

# upload setup scripts
gcloud compute scp --scp-flag=-r setup/ ubuntu@memcache-server-8tzg:/home/ubuntu/ --zone europe-west3-a
gcloud compute scp cpu_utilization.py ubuntu@memcache-server-8tzg:/home/ubuntu/ --zone europe-west3-a
gcloud compute scp --scp-flag=-r setup/ ubuntu@client-agent-1ggt:/home/ubuntu/ --zone europe-west3-a
gcloud compute scp --scp-flag=-r setup/ ubuntu@client-measure-b3h0:/home/ubuntu/ --zone europe-west3-a

# execute this on memcache-server
> ./setup/memcache-server-  setup.sh

# execute this on client and measure
> ./setup/memcache-agent-measure-setup.sh

# then start the experiment, NUM_THREADS has to be identical to what was defined in /etc/memcached.conf
> ./question1.sh [INTERNAL-MEMCACHE-IP] [INTERNAL_AGENT_IP] [AGENT_NAME] [MEASURE_NAME] [NUM_THREADS] [TASKSET_CPUS] [MEMCACHE_SERVER_NAME]
