read -p "Enter your ETH ID: " ETHID
export KOPS_STATE_STORE=gs://cca-eth-2025-group-090-$ETHID/
kops delete cluster part3.k8s.local --yes
