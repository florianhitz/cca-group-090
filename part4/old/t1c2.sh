# setup memcached for T=1, C=2
SERVER_NAME=$(kubectl get nodes --selector=cca-project-nodetype=memcached -o jsonpath='{.items[0].metadata.name}')
SERVER_INT_IP=$(kubectl get nodes --selector=cca-project-nodetype=memcached -o jsonpath='{.items[0].status.addresses[0].address}')
gcloud compute ssh \
    --ssh-key-file ~/.ssh/cloud-computing ubuntu@$SERVER_NAME \
    --zone europe-west1-b \
    --command "
        sudo systemctl stop memcached
        sudo systemctl disable memcached
        sudo pkill memcached

        sleep 2

        sudo memcached -m 1024 -p 11211 -l $SERVER_INT_IP -t 1 -u memcache &

        sleep 2

        sudo taskset -a -cp 0,1 \$(pgrep -u memcache memcached) &
"

echo "ok"

