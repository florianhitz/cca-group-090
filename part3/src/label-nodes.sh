#!/bin/bash

# Optional: Run this script if your node labels are missing.
# 
# In some cases, the expected node labels (defined in part3.yaml) may not be
# applied correctly after creating or updating the cluster.
# If you've tried rolling updates or reapplying the config without success,
# this script manually attaches the correct `cca-project-nodetype` labels
# based on node hostnames.
#
# Safe to use and re-run — labels will be overwritten as needed.

# Apply labels based on node name pattern
echo "Labelling nodes with cca-project-nodetype..."

# Get all node names
kubectl get nodes -o custom-columns=NAME:.metadata.name --no-headers | while read -r node_name; do
    # Extract logical nodetype from the hostname using regex
    if [[ "$node_name" =~ (node-[a-z]-[0-9]+core|client-agent-[a-z]|client-measure) ]]; then
        label_value="${BASH_REMATCH[1]}"
        echo "Labelling $node_name with cca-project-nodetype=$label_value"
        kubectl label node "$node_name" "cca-project-nodetype=$label_value" --overwrite
    else
        echo "Skipping $node_name (no matching pattern)"
    fi
done

echo "All eligible nodes labelled!"