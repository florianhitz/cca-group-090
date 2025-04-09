export KOPS_STATE_STORE=gs://cca-eth-2025-group-090-flhitz/
PROJECT=`gcloud config get-value project`
kops create -f ../../part2b.yaml
kops update cluster part2b.k8s.local --yes --admin
kops validate cluster --wait 10m
kubectl get nodes -o wide
