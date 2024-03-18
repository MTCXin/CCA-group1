
for i in ibench-cpu ibench-l1d ibench-l1i ibench-l2 ibench-llc ibench-membw
    do 
        kubectl create -f interference/$i.yaml
        echo Wait for inference to start...
        kubectl wait --for=condition=Ready pod/$i --timeout=1000s
        kubectl get pods
        echo Wait 2 minutes such that interference can start properly...
        sleep 120
        
        for b in blackscholes canneal ferret freqmine dedup radix vips
        do

            kubectl create -f parsec-benchmarks/part2a/parsec-$b.yaml
            echo Wait for job to complete...
            kubectl wait --for=condition=Complete job/parsec-$b --timeout=1000s

            kubectl get jobs
            echo Job completed! Save output to parsec-$b-$i.txt
            kubectl logs $(kubectl get pods --selector=job-name=parsec-$b --output=jsonpath='{.items[*].metadata.name}') > parsec-$b-$i.txt

            kubectl delete job parsec-$b
            
        done

        echo Delete all jobs and pods...
        kubectl delete jobs --all
        kubectl delete pods --all
        echo Wait 30s to ensure that interference stopped...
        sleep 30
    done



