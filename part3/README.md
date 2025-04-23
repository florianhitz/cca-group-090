# User Instruction for Part 3

## Part 3 Folder Structure

## Usage Specification
Please make sure that you are under the current working directory: ```/part3/src/```
### Step 1: Set Up Kubernetes Cluster
This step sets up a Kubernetes cluster with 1 master and 7 worker nodes.
To run the script as-is, you must have a valid ETH ID associated with Group 090.
If you're using a different configuration, please update lines 2-3 of the setup script to mathc your project setting.
```
$ ./setup-part3.sh
```
#### Optional: Fix Missing Node Labels
In case that your nodes are not labelled, you can manually attach the labels using the helper script:
```
$ ./label-nodes.sh
```
### Step 2: Install Augmented mcperf on Client Node
SSH into the mcperf client nodes and install the augmented version of the mcperf on each client.
```
$ ./install-part3.sh 
```
### Step 3: Launch the Memcached Service
#### 3.1 - Specify the Target Node
In ```instruction-yaml/memcache-t1-cpuset.yaml``` (line 16), set the target node where memcached should run. Make sure to choose one of the four heterogeneous VMs.
#### 3.2 - Start Memcached
Use the start flag to launch the memcached service. Omitting the flag will delete all previously deployed jobs, pods and services.
```
$ ./run-memchached.sh start
```
### Step 4: SSH into the Client and Measure Nodes
#### 4.1 - Connect to client-agent-a
Open a new terminal and run:
```
$ ./ssh-into.sh client-a
```
#### 4.2 - Connect to client-agent-b
Open another terminal and run:
```
$ ./ssh-into.sh client-b
```
#### 4.3 - Connect to client-measure
Open one more terminal and run:
```
$ ./ssh-into.sh
```
After Step 4, there should be four terminal windows open: one for the main console and three for the mcperf-related nodes.
### Step 5: Run a Scheduling Policy and Collect Results
Choose one of the 8 available scheduling policies to run:
```
$ python run-policy.py <1-8>
```
In a separate terminal, monitor the pod statues and job completion (there should be 5 terminals now):
```
$ kubectl get pods -o wide
```
Once all jobs are finished, save the full pod status output to a results file:
```
$ kubectl get pods -o json > results.json
```