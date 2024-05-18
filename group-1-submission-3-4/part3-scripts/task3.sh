#!/bin/bash

# Input variables
name1=$1
name2=$2
name3=$3
namea=$4
nameb=$5
namec=$6
MEMCACHED_IP=$7
INTERNAL_AGENT_A_IP=$8
INTERNAL_AGENT_B_IP=$9

# directory to store results
RESULT_DIR="results-$(date +%d-%H%M%S)"
mkdir $RESULT_DIR

tmux list-sessions -F "#{session_name}" | xargs -I {} tmux kill-session -t {}
kubectl get pods --field-selector spec.nodeName=node-a-2core-$namea -o name | grep -v some-memcached | xargs kubectl delete
kubectl delete pods --field-selector=spec.nodeName=node-b-4core-$nameb
kubectl delete pods --field-selector=spec.nodeName=node-c-8core-$namec
kubectl delete jobs --all
sleep 4
kubectl get pods --field-selector spec.nodeName=node-a-2core-$namea -o name | grep -v some-memcached | xargs kubectl delete
kubectl delete pods --field-selector=spec.nodeName=node-b-4core-$nameb
kubectl delete pods --field-selector=spec.nodeName=node-c-8core-$namec
kubectl delete jobs --all
sleep 8

# tmux sessions
tmux new-session -d -s client-a "gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-agent-a-$name1 --zone europe-west3-a"
tmux new-session -d -s client-b "gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-agent-b-$name2 --zone europe-west3-a"
tmux new-session -d -s measure "gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-measure-$name3 --zone europe-west3-a"
tmux new-session -d -s workflow1
tmux new-session -d -s workflow2
tmux new-session -d -s workflow3

# kubectl label nodes ubuntu@node-b-4core-$nameb cca-project-nodetype=node-b
# kubectl label nodes ubuntu@node-c-8core-$namec cca-project-nodetype=node-c

# Loop 
for i in 1 2 3
do
    # cd memcache-perf
    tmux send-keys -t client-a "cd memcache-perf-dynamic" C-m
    tmux send-keys -t client-b "cd memcache-perf-dynamic" C-m
    tmux send-keys -t measure "cd memcache-perf-dynamic" C-m
    tmux send-keys -t client-a "./mcperf -T 2 -A" C-m
    tmux send-keys -t client-b "./mcperf -T 4 -A" C-m
    tmux send-keys -t measure "./mcperf -s $MEMCACHED_IP --loadonly" C-m

    # 
    tmux send-keys -t measure "./mcperf -s $MEMCACHED_IP -a $INTERNAL_AGENT_A_IP -a $INTERNAL_AGENT_B_IP --noload -T 6 -C 4 -D 4 -Q 1000 -c 4 -t 10 --scan 30000:30500:5" C-m
    
    tmux send-keys -t workflow1 "kubectl create -f parsec-benchmarks/part3/parsec-blackscholes.yaml" C-m
    tmux send-keys -t workflow2 "kubectl create -f parsec-benchmarks/part3/parsec-canneal.yaml" C-m
    tmux send-keys -t workflow3 "kubectl create -f parsec-benchmarks/part3/parsec-dedup.yaml; kubectl create -f parsec-benchmarks/part3/parsec-vips.yaml" C-m
    tmux send-keys -t workflow2 "kubectl create -f parsec-benchmarks/part3/parsec-radix.yaml" C-m
# Monitoring
    declare -A job_status=(["parsec-dedup"]="pending" ["parsec-radix"]="pending" ["parsec-ferret"]="pending" ["parsec-vips"]="pending" ["parsec-blackscholes"]="pending" ["parsec-freqmine"]="pending" ["parsec-canneal"]="pending")
    while true; do

       #  get job status
        if ! jobs_output=$(kubectl get jobs -o wide 2>/dev/null); then
            echo "failed fetching jobs"
            jobs_output=""  # clear
        fi

        # renew job status
        for job in "${!job_status[@]}"; do
            if echo "$jobs_output" | grep -q "^$job"; then

                job_complete=$(echo "$jobs_output" | awk -v job="$job" '$1 == job && $2 == "1/1" {print "complete"}')
                if [[ "$job_complete" == "complete" ]]; then
                    job_status[$job]="complete"
                    echo "$job completed"
                elif [ "${job_status[$job]}" != "complete" ]; then
                    echo "$job running"
                fi
            else

                if [ "${job_status[$job]}" = "pending" ]; then
                    echo "$job pending。"
                elif [ "${job_status[$job]}" != "complete" ]; then
                    echo "$job status uncertain"
                fi
            fi
        done


        # Conditions for job creation
        if [ "${job_status["parsec-canneal"]}" = "complete" ] && [ "${job_status["parsec-ferret"]}" = "pending" ]; then
            tmux send-keys -t workflow2 "kubectl create -f parsec-benchmarks/part3/parsec-ferret.yaml" C-m
            job_status["parsec-ferret"]="started"
            echo "parsec-ferret has been triggered to start."
        fi

        # if [ "${job_status["parsec-radix"]}" = "complete" ] && [ "${job_status["parsec-dedup"]}" = "pending" ]; then
        #     tmux send-keys -t workflow1 "kubectl create -f parsec-benchmarks/part3/parsec-dedup.yaml" C-m
        #     job_status["parsec-dedup"]="started"
        #     echo "parsec-dedup has been triggered to start."
        # fi

        if { [ "${job_status["parsec-vips"]}" = "complete" ] || [ "${job_status["parsec-dedup"]}" = "complete" ]; }  && [ "${job_status["parsec-freqmine"]}" = "pending" ]; then
            tmux send-keys -t workflow3 "kubectl create -f parsec-benchmarks/part3/parsec-freqmine.yaml" C-m
            job_status["parsec-freqmine"]="started"
            echo "parsec-freqmine has been triggered to start."
        fi


        all_done=true
        for status in "${job_status[@]}"; do
            if [ "$status" != "complete" ]; then
                all_done=false
                break
            fi
        done

        if [ "$all_done" = true ]; then
            echo "All jobs have completed."
            break
        fi

        sleep 2
    done

    kubectl get pods -o json > ./$RESULT_DIR/results-$i.json
    sleep 5
    tmux capture-pane -pS - -t client-a > ./$RESULT_DIR/client-a-$i.txt
    tmux capture-pane -pS - -t client-b > ./$RESULT_DIR/client-b-$i.txt
    tmux capture-pane -pS - -t measure > ./$RESULT_DIR/measure-$i.txt
    tmux send-keys -t client-a C-c
    tmux send-keys -t client-b C-c
    tmux send-keys -t measure C-c
    tmux send-keys -t client-a 'clear' C-m
    tmux send-keys -t client-b 'clear' C-m
    tmux send-keys -t measure 'clear' C-m
    
    kubectl delete pods --field-selector=spec.nodeName=node-b-4core-$nameb
    kubectl delete pods --field-selector=spec.nodeName=node-c-8core-$namec
    kubectl get pods --field-selector spec.nodeName=node-a-2core-$namea -o name | grep -v some-memcached | xargs kubectl delete
    kubectl delete jobs --all
    sleep 4
    kubectl get pods --field-selector spec.nodeName=node-a-2core-$namea -o name | grep -v some-memcached | xargs kubectl delete
    kubectl delete pods --field-selector=spec.nodeName=node-b-4core-$nameb
    kubectl delete pods --field-selector=spec.nodeName=node-c-8core-$namec
    kubectl delete jobs --all
    
    sleep 40
done

cp -r ./parsec-benchmarks/part3/* ./$RESULT_DIR/
# kubectl delete pods,jobs --all --field-selector=spec.nodeName!=ubuntu@node-a-2core-$namea