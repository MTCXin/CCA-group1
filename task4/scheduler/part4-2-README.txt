
# These are the instructions to run part 4.3 and 4.4
# Note that scheduler_logger.py was provided by the course organizers and we did not modify it


> export KOPS_STATE_STORE=<your-gcp-state-store>
> PROJECT='gcloud config get-value project'

> ./setup/start-cluster.sh

# to get names and IPs
> kubectl get nodes -o wide 

# upload setup scripts
> gcloud compute scp --scp-flag=-r setup/ ubuntu@memcache-server-[SERVER_NAME]:/home/ubuntu/ --zone europe-west3-a
> gcloud compute scp --scp-flag=-r setup/ ubuntu@client-agent-[AGENT_NAME]:/home/ubuntu/ --zone europe-west3-a
> gcloud compute scp --scp-flag=-r setup/ ubuntu@client-measure-[CLIENT_NAME]:/home/ubuntu/ --zone europe-west3-a
> gcloud compute scp --scp-flag=-r scheduler.py ubuntu@memcache-server-[SERVER_NAME]:/home/ubuntu/scheduler/scheduler.py --zone europe-west3-a

# connecting to machine template
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@<MACHINE_NAME> --zone europe-west3-a

# connecting to machines
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-agent-[AGENT_NAME] --zone europe-west3-a
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-measure-[CLIENT_NAME] --zone europe-west3-a
# execute this on client AND measure
> ./setup/memcache-agent-measure-setup.sh

# connect to and execute this on memcache-server
> gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@memcache-server-[SERVER_NAME] --zone europe-west3-a
> ./setup/memcache-server-setup.sh
# update the file content as described below
> sudo vim /etc/memcached.conf 
    # update line starting with "-m" to "-m 1024"
    # add a new line "-t 2"
<<<<<<< HEAD
    # update line starting with "-l" to "-l 10.0.16.7" [MEMCAHED_INTERNAL_IP]
=======
    # update line starting with "-l" to "-l [MEMCACHE_INTERNAL_IP]" 
>>>>>>> dbb3454d8f5b701fb4dd16f20c14bc2e0bb7c251
    # save file and close it
> sudo systemctl restart memcached
> sudo systemctl status memcached

<<<<<<< HEAD
# experimentName can be freely chosen and will be used in logs and in the result folder name
> ./run_experiment.sh 10.0.16.3 10.0.16.5 sm0x 98fd wq3t schedulerme
=======
# [NAME] can be freely chosen and will be used in logs and in the result folder name
> ./run_experiment.sh [MEMCACHE_INTERNAL_IP] [AGENT_INTERNAL_IP] [AGENT_NAME] [CLIENT_NAME] [SERVER_NAME] [NAME]
>>>>>>> dbb3454d8f5b701fb4dd16f20c14bc2e0bb7c251
# when prompted to do so, execute this on memcache-server
> python3 scheduler/scheduler.py
# wait until run_experiment.sh (don't kill it otherwise the logs from measure are lost!!)

# copy the scheduler log file to the results folder created by run_experiment.sh
gcloud compute scp --scp-flag=-r ubuntu@memcache-server-[SERVER_NAME]:/home/ubuntu/log[TIMESTAMP].txt jobs.txt --zone europe-west3-a