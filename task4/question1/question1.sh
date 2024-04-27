#!/bin/bash

INTERNAL_MEMCACHED_IP=$1
INTERNAL_AGENT_IP=$2
nameAgent=$3
nameMeasure=$4
t=$5
c=$6
serverName=$7

# directory to store results
RESULT_DIR="question1-results-$(date +%d-%H%M%S)"
mkdir $RESULT_DIR


for i in 1 2 3; do
    tmux new-session -d -s client "gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-agent-$nameAgent --zone europe-west3-a"
    tmux new-session -d -s measure "gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-measure-$nameMeasure --zone europe-west3-a"
    tmux new-session -d -s server "gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@memcache-server-$serverName --zone europe-west3-a"

    echo start T=$t C=$c i=$i
    tmux send-keys -t client "echo start T=$t C=$c i=$i" C-m
    tmux send-keys -t measure "echo start T=$t C=$c i=$i" C-m
    tmux send-keys -t server "echo start T=$t C=$c i=$i" C-m

    tmux send-keys -t client "cd memcache-perf-dynamic" C-m
    tmux send-keys -t measure "cd memcache-perf-dynamic" C-m

    tmux send-keys -t client "./mcperf -T 16 -A" C-m

    tmux send-keys -t measure "./mcperf -s $INTERNAL_MEMCACHED_IP --loadonly" C-m
    tmux send-keys -t server "python3 cpu_utilization.py" C-m
    tmux send-keys -t measure "./mcperf -s $INTERNAL_MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 --scan 5000:125000:5000" C-m

    sleep 200

    tmux send-keys -t server C-c

    tmux capture-pane -pS - -t client > ./$RESULT_DIR/client-T$t-C$c-run$i.txt
    tmux capture-pane -pS - -t measure > ./$RESULT_DIR/measure-T$t-C$c-run$i.txt
    tmux capture-pane -pS - -t server > ./$RESULT_DIR/server-T$t-C$c-run$i.txt
    tmux send-keys -t client 'clear' C-m
    tmux send-keys -t measure 'clear' C-m

    tmux kill-session -t client
    tmux kill-session -t measure
    tmux kill-session -t server
done


