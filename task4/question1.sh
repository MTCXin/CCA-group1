#!/bin/bash

INTERNAL_MEMCACHED_IP=$1
INTERNAL_AGENT_IP=$2
nameAgent=$3
nameMeasure=$4

# directory to store results
RESULT_DIR="question1-results-$(date +%d-%H%M%S)"
mkdir $RESULT_DIR

tmux new-session -d -s client "gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-agent-$nameAgent --zone europe-west3-a"
tmux new-session -d -s measure "gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-measure-$nameMeasure --zone europe-west3-a"


for t in 1 2; do
    for c in 1 2; do # TODO where do I set this?
        for i in 1 2 3; do
            tmux send-keys -t client "echo start T=$t C=$c i=$i" C-m

            tmux send-keys -t client "cd memcache-perf-dynamic" C-m
            tmux send-keys -t measure "cd memcache-perf-dynamic" C-m

            tmux send-keys -t client "./mcperf -T 16 -A" C-m

            tmux send-keys -t measure "./mcperf -s $INTERNAL_MEMCACHED_IP --loadonly" C-m
            tmux send-keys -t measure "./mcperf -s $INTERNAL_MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T $t -C $c -D 4 -Q 1000 -c 4 -t 5 --scan 5000:125000:5000" C-m
    
            # TODO wait for measurement
            sleep 10

            tmux capture-pane -pS - -t client > ./$RESULT_DIR/client-T$t-C$c-run$i.txt
            tmux capture-pane -pS - -t measure > ./$RESULT_DIR/measure-T$t-C$c-run$i.txt
            tmux send-keys -t client 'clear' C-m
            tmux send-keys -t measure 'clear' C-m

            # TODO how to start new measurement?
        done
    done
done
