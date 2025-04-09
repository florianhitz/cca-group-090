CLIENTS=($(kubectl get nodes -o name | grep "client-" | sed "s|node/||"))
echo "Found clients: ${CLIENTS[@]}"

INTERNAL_AGENT_A_IP='' 
INTERNAL_AGENT_B_IP='' 
for vm in "${CLIENTS[@]}"; do
    if [[ $vm == client-agent-a* ]]; then
        NAME_AGENT_A=$vm
        INTERNAL_AGENT_A_IP=$(gcloud compute instances describe $vm --zone europe-west1-b --format="get(networkInterfaces[0].networkIP)")
    elif [[ $vm == client-agent-b* ]]; then
        NAME_AGENT_B=$vm
        INTERNAL_AGENT_B_IP=$(gcloud compute instances describe $vm --zone europe-west1-b --format="get(networkInterfaces[0].networkIP)")
    else
        CLIENT_MEASURE_NAME=$vm
    fi
done

MEMCACHED_IP=$(kubectl get pod some-memcached -o jsonpath='{.status.podIP}{"\n"}')

client=$1
echo "Connect to ${client} via ssh"
    if [[ $1 == "client-a" ]]; then
        echo "Connect to ${NAME_AGENT_A}"
        echo "
            cd memcache-perf-dynamic/ &&
            ./mcperf -T 2 -A
        "
        gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$NAME_AGENT_A --zone europe-west1-b
    elif [[ $1 == "client-b" ]]; then
        echo "Connect to ${NAME_AGENT_B}"
        echo "
            cd memcache-perf-dynamic/ &&
            ./mcperf -T 4 -A
        "
        gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$NAME_AGENT_B --zone europe-west1-b
    else
        echo "Connect to ${CLIENT_MEASURE_NAME}"
        echo "
            cd memcache-perf-dynamic/ &&
            ./mcperf -s ${MEMCACHED_IP} --loadonly &&
            ./mcperf -s ${MEMCACHED_IP} -a ${INTERNAL_AGENT_A_IP} -a ${INTERNAL_AGENT_B_IP} \
                --noload -T 6 -C 4 -D 4 -Q 1000 -c 4 -t 10 --scan 30000:30500:5
        "
        gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$CLIENT_MEASURE_NAME --zone europe-west1-b 
    fi
done

