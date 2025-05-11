NAME=$(kubectl get nodes --selector=cca-project-nodetype="client-agent" -o jsonpath='{.items[0].metadata.name}')

# echo "Connect to ${NAME} via ssh"
echo "cd memcache-perf-dynamic/ && ./mcperf -T 8 -A"

gcloud compute ssh \
    --ssh-key-file ~/.ssh/cloud-computing ubuntu@$NAME \
    --zone europe-west1-b \
#     --command "cd memcache-perf-dynamic/ && ./mcperf -T 8 -A"
