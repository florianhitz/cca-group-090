CLIENTS=($(kubectl get nodes -o name | grep "client-" | sed "s|node/||"))
echo "${CLIENTS[@]}"

INTERNAL_AGENT_A_IP='' 
INTERNAL_AGENT_B_IP='' 
MEMCACHED_IP='' 

for vm in "${CLIENTS[@]}"; do
    if [[ $vm == client-agent-a* ]]; then
        INTERNAL_AGENT_A_IP=$(gcloud compute instances describe $vm --zone europe-west1-b --format="get(networkInterfaces[0].networkIP)")
    elif [[ $vm == client-agent-b* ]]; then
        INTERNAL_AGENT_B_IP=$(gcloud compute instances describe $vm --zone europe-west1-b --format="get(networkInterfaces[0].networkIP)")
    else
        MEMCACHED_IP=$(gcloud compute instances describe $vm --zone europe-west1-b --format="get(networkInterfaces[0].networkIP)")
    fi
done

for vm in "${CLIENTS[@]}"; do
    echo "Setting up mcperf for ${vm}"
    if [[ $vm == client-agent-a* ]]; then
        gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$vm --zone europe-west1-b --command "
            cd memcache-perf-dynamic/ &&
            ./mcperf -T 2 -A
        "
    elif [[ $vm == client-agent-b* ]]; then
        gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$vm --zone europe-west1-b --command "
            cd memcache-perf-dynamic/ &&
            ./mcperf -T 4 -A
        "
    else
        gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$vm --zone europe-west1-b --command "
            cd memcache-perf-dynamic/ &&
            ./mcperf -s ${MEMCACHED_IP} --loadonly &&
            ./mcperf -s ${MEMCACHED_IP} -a ${INTERNAL_AGENT_A_IP} -a ${INTERNAL_AGENT_B_IP} \
                --noload -T 6 -C 4 -D 4 -Q 1000 -c 4 -t 10 --scan 30000:30500:5
        "
    fi
done

