NAME_CLIENT_MEASURE=$(kubectl get nodes --selector=cca-project-nodetype="client-measure" -o jsonpath='{.items[0].metadata.name}')
MEMCACHED_INT_IP=$(kubectl get nodes --selector=cca-project-nodetype=memcached -o jsonpath='{.items[0].status.addresses[0].address}')
AGENT_A_INT_IP=$(kubectl get nodes --selector=cca-project-nodetype="client-agent" -o jsonpath='{.items[0].status.addresses[0].address}')

echo "Connect to ${NAME_CLIENT_MEASURE}"
gcloud compute ssh \
--ssh-key-file ~/.ssh/cloud-computing ubuntu@$NAME_CLIENT_MEASURE \
--zone europe-west1-b \
--command "
    cd memcache-perf-dynamic/ && \
    ./mcperf -s ${MEMCACHED_INT_IP} --loadonly && \
    ./mcperf -s ${MEMCACHED_INT_IP} -a ${AGENT_A_INT_IP} \
        --noload -T 8 -C 8 -D 4 -Q 1000 -c 8 -t 5 \
        --scan 5000:220000:5000
"

