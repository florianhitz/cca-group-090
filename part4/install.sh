# install memcached, change config and install docker
# for docker see https://docs.docker.com/engine/install/ubuntu/

SERVER_NAME=$(kubectl get nodes --selector=cca-project-nodetype=memcached -o jsonpath='{.items[0].metadata.name}')
SERVER_INT_IP=$(kubectl get nodes --selector=cca-project-nodetype=memcached -o jsonpath='{.items[0].status.addresses[0].address}')

# install memcached
gcloud compute ssh \
    --ssh-key-file ~/.ssh/cloud-computing ubuntu@$SERVER_NAME \
    --zone europe-west1-b \
    --command "
        sudo apt update && sudo apt install -y memcached libmemcached-tools && \
        sudo sed -i 's/^-m .*/-m 1024/' /etc/memcached.conf && \
        sudo sed -i 's/^-l .*/-l $SERVER_INT_IP/' /etc/memcached.conf && \
        cat /etc/memcached.conf && \
        sudo systemctl restart memcached && \
        sudo systemctl status memcached
"

# install docker
gcloud compute ssh \
    --ssh-key-file ~/.ssh/cloud-computing ubuntu@$SERVER_NAME \
    --zone europe-west1-b \
    --command "
        for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove -y \$pkg; done
        sudo apt-get update
        sudo apt-get install -y ca-certificates curl
        sudo install -m 0755 -d /etc/apt/keyrings
        sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
        sudo chmod a+r /etc/apt/keyrings/docker.asc
        echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \$(. /etc/os-release && echo \${UBUNTU_CODENAME:-\$VERSION_CODENAME}) stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

        sudo groupadd docker
        sudo usermod -aG docker $USER
    "

# install py stuff
gcloud compute ssh \
    --ssh-key-file ~/.ssh/cloud-computing ubuntu@$SERVER_NAME \
    --zone europe-west1-b \
    --command "
        sudo apt install python3-pip
        sudo apt install python3.12-venv
        python3 -m venv .venv
    "

# prefetch docker images
#gcloud compute ssh \
#    --ssh-key-file ~/.ssh/cloud-computing ubuntu@$SERVER_NAME \
#    --zone europe-west1-b \
#    --command "
#        docker pull anakli/cca:parsec_blackscholes
#        docker pull anakli/cca:parsec_canneal
#        docker pull anakli/cca:parsec_dedup
#        docker pull anakli/cca:parsec_ferret
#        docker pull anakli/cca:parsec_freqmine
#        docker pull anakli/cca:splash2x_radix
#        docker pull anakli/cca:parsec_vips
#"


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
            make
    "
done


