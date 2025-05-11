#!/bin/bash

# Optional: Run this script if your node labels are missing.
# In fact, it is a bit strange for me because the nodes are not always correctly
# labeled while they are indeed described in the part4.yaml

#!/bin/sh

# Loop through all nodes
for node in $(kubectl get nodes --no-headers -o custom-columns=":metadata.name"); do
  case "$node" in
    client-agent-*)
      echo "Labeling $node as client-agent"
      kubectl label node "$node" cca-project-nodetype=client-agent --overwrite
      ;;
    client-measure-*)
      echo "Labeling $node as client-measure"
      kubectl label node "$node" cca-project-nodetype=client-measure --overwrite
      ;;
    memcache-server-*)
      echo "Labeling $node as memcached"
      kubectl label node "$node" cca-project-nodetype=memcached --overwrite
      ;;
    *)
      echo "Skipping $node (no matching prefix)"
      ;;
  esac
done