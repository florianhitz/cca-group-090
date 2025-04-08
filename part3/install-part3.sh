CLIENTS=($(kubectl get nodes -o name | grep "client-" | sed "s|node/||"))     
echo ${CLIENTS[@]}

for vm in "${CLIENTS[@]}"; do
    gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$vm --zone europe-west1-b --command "
        sudo sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/ubuntu.sources &&
        sudo apt-get update &&
        sudo apt-get install libevent-dev libzmq3-dev git make g++ --yes &&
        sudo apt-get build-dep memcached --yes &&
        git clone https://github.com/eth-easl/memcache-perf-dynamic.git &&
        cd memcache-perf-dynamic &&
        make
    "
done
