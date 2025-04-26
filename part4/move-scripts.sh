# copies the measurement script from host to memcached server
SERVER_NAME=$(kubectl get nodes --selector=cca-project-nodetype=memcached -o jsonpath='{.items[0].metadata.name}')
SERVER_INT_IP=$(kubectl get nodes --selector=cca-project-nodetype=memcached -o jsonpath='{.items[0].status.addresses[0].address}')

gcloud compute scp scheduler_logger.py scheduler.py ubuntu@$SERVER_NAME:~ --zone europe-west1-b
