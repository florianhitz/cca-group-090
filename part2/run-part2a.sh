#!/bin/bash

INTERFERENCES=("none" "cpu" "l1d" "l1i" "l2" "llc" "membw")
PARSEC_JOBS=("blackscholes" "canneal" "dedup" "ferret" "freqmine" "radix" "vips")

for interference in "${INTERFERENCES[@]}"; do
    if [ "$interference" != "none" ]; then
        echo "Launching iBench interference: $interference"

        kubectl create -f ./interference/ibench-${interference}.yaml

        while [ "$(kubectl get pod ibench-${interference} -o jsonpath='{.status.containerStatuses[0].ready}')" != 'true' ]; do
            echo "Waiting for $interference to start..."
            sleep 5
        done
        echo "$interference started."
    fi

    for job in "${PARSEC_JOBS[@]}"; do
        echo "Running PARSEC job: $job under interference: $interference"
        kubectl create -f ./parsec-benchmarks/part2a/parsec-${job}.yaml
        
        while [ "$(kubectl get job parsec-${job} -o jsonpath='{.status.succeeded}')" != "1" ]; do
            echo "Waiting for $job under $interference to finish..."
            sleep 5
        done
        
        pod_name=$(kubectl get pods --selector=job-name=parsec-${job} --output=jsonpath='{.items[*].metadata.name}')
        echo "Collecting logs from pot: $pod_name"

        kubectl logs "$pod_name" > results-part2a/${job}_${interference}.log

        kubectl delete jobs --all
    done
    kubectl delete pods --all
done
        


