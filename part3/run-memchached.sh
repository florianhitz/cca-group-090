if [[ $1 == "start" ]]; then
    kubectl create -f memcache-t1-cpuset.yaml
    kubectl expose pod some-memcached --name some-memcached-11211 \
    --type LoadBalancer --port 11211 \
    --protocol TCP
    sleep 60
    kubectl get service some-memcached-11211
    kubectl get pods -o wide
else
    kubectl delete jobs --all
    kubectl delete pods --all
    kubectl delete service some-memcached-11211     
fi
    

