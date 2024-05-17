#!/bin/bash

INTERNAL_MEMCACHED_IP=$1
INTERNAL_AGENT_IP=$2
nameAgent=$3
nameMeasure=$4
serverName=$5
experimentName=$6

# TODO run this 3 times
i=0 

# directory to store results
RESULT_DIR="question2-results-$experimentName-$(date +%d-%H%M%S)"
echo Saving results in folder $RESULT_DIR
mkdir $RESULT_DIR

tmux kill-session -t client
tmux kill-session -t measure

tmux new-session -d -s client "gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-agent-$nameAgent --zone europe-west3-a"
tmux new-session -d -s measure "gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-measure-$nameMeasure --zone europe-west3-a"

echo start $experimentName run $i
tmux send-keys -t client "echo start $experimentName run $i" C-m
tmux send-keys -t measure "echo start $experimentName run $i" C-m

tmux send-keys -t client "cd memcache-perf-dynamic" C-m
tmux send-keys -t measure "cd memcache-perf-dynamic" C-m

tmux send-keys -t client "./mcperf -T 16 -A" C-m

tmux send-keys -t measure "./mcperf -s $INTERNAL_MEMCACHED_IP --loadonly" C-m
tmux send-keys -t measure "./mcperf -s $INTERNAL_MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 1200 --qps_interval 10 --qps_min 5000 --qps_max 100000 --qps_seed 3274" C-m

sleep 20 # make sure memcached started up properly
echo You can now start the scheduler.py on the server. 
sleep 1200

tmux capture-pane -pS - -t client > ./$RESULT_DIR/client-run$i.txt
tmux capture-pane -pS - -t measure > ./$RESULT_DIR/measure-run$i.txt

tmux kill-session -t client
tmux kill-session -t measure


