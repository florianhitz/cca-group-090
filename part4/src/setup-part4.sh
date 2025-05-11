# Promote the user for ETHz ID
read -p "Enter your ETH ID: " ETHID
export KOPS_STATE_STORE=gs://cca-eth-2025-group-090-$ETHID/
# Replace line 16 in the YAML file
yaml_file="../part4.yaml"
new_line="  configBase: gs://cca-eth-2025-group-090-$ETHID/part4.k8s.local"
# Replace line 16 (line numbers start at 1)
sed -i '' "16s|.*|$new_line|" "$yaml_file"
PROJECT=`gcloud config get-value project`
kops create -f ../part4.yaml
kops update cluster part4.k8s.local --yes --admin
kops validate cluster --wait 10m
kubectl get nodes -o wide
