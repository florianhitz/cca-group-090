# install memcache and change config
SERVER_NAME=$(kubectl get nodes --selector=cca-project-nodetype=memcached -o jsonpath='{.items[0].metadata.name}')
SERVER_INT_IP=$(kubectl get nodes --selector=cca-project-nodetype=memcached -o jsonpath='{.items[0].status.addresses[0].address}')
gcloud compute ssh \
    --ssh-key-file ~/.ssh/cloud-computing ubuntu@$SERVER_NAME \
    --zone europe-west1-b \
    --command "sudo apt update && sudo apt install -y memcached libmemcached-tools && \
               sudo sed -i 's/^-m .*/-m 1024/' /etc/memcached.conf && \
               sudo sed -i 's/^-l .*/-l $SERVER_INT_IP/' /etc/memcached.conf && \
               cat /etc/memcached.conf && \
               sudo systemctl restart memcached && \
               sudo systemctl status memcached"



# install the augmented version of mcperf
CLIENT_NAME=$(kubectl get nodes --selector=cca-project-nodetype="client-agent" -o jsonpath='{.items[0].metadata.name}')
MEASURE_NAME=$(kubectl get nodes --selector=cca-project-nodetype="client-measure" -o jsonpath='{.items[0].metadata.name}')

NODES=("$CLIENT_NAME" "$MEASURE_NAME")

for NODE in "${NODES[@]}"; do
    gcloud compute ssh \
        --ssh-key-file ~/.ssh/cloud-computing ubuntu@$NODE \
        --zone europe-west1-b \
        --command "
            sudo sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/ubuntu.sources &&
            sudo apt-get update &&
            sudo apt-get install libevent-dev libzmq3-dev git make g++ --yes &&
            sudo apt-get build-dep memcached --yes &&
            git clone https://github.com/eth-easl/memcache-perf-dynamic.git &&
            cd memcache-perf-dynamic &&
            make"
done


