NAME=$(kubectl get nodes --selector=cca-project-nodetype="memcached" -o jsonpath='{.items[0].metadata.name}')

echo "Connect to ${NAME} via ssh"

gcloud compute ssh \
    --ssh-key-file ~/.ssh/cloud-computing ubuntu@$NAME \
    --zone europe-west1-b \

