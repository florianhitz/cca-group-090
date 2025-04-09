

PARSEC_JOBS=("blackscholes" "canneal" "dedup" "ferret" "freqmine" "radix" "vips")
NUM_THREADS=(1 2 4 8)


# delete all jobs if one is still running
kubectl delete jobs --all

for job in "${PARSEC_JOBS[@]}"; do
    for n in ${NUM_THREADS[@]}; do 
        echo "Running PARSEC job $job with $n threads."

        # adjust number of threads
        sed -i '' "s/-n [1248]/-n ${n}/" ./parsec-benchmarks/part2b/parsec-${job}.yaml

        kubectl create -f ./parsec-benchmarks/part2b/parsec-${job}.yaml
        
        while [ "$(kubectl get job parsec-${job} -o jsonpath='{.status.succeeded}')" != "1" ]; do
            echo "Waiting for $job to finish..."
            sleep 5
        done
        
        pod_name=$(kubectl get pods --selector=job-name=parsec-${job} --output=jsonpath='{.items[*].metadata.name}')
        echo "Collecting logs from pot: $pod_name"
    
        kubectl logs "$pod_name" > results-part2b/${job}_${n}-threads.log
    
        kubectl delete jobs --all
    done
done
    
