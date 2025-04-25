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
#### (Optional) Fix Missing Node Labels
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
In ```instruction-yaml/memcache-t1-cpuset.yaml``` (line 14 and 17), set the target node and CPU core where memcached should run. Make sure to choose from one of the four heterogeneous VMs. In our setting, we put it on client-agent-b core 0.
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
#### 5.1 Choose and Run a Scheduling Policy
Choose one of the 8 available scheduling policies to run:
```
$ python3 run-policy.py <1-8>
```
This will submit a batch of jobs based on the selected policy.
#### 5.2 Monitor Job Progress
In a separate terminal (you should have 5 terminals open now), watch the pod statuses and job completions:
```
$ kubectl get pods -o wide
```
Wait until all batch jobs have finished, i.e., all pods running a batch job show STATUS=Completed.
#### 5.3 Collect the Results
Once all jobs are finished, save the full pod status output to a results file:
```
$ kubectl get pods -o json > ../result/batch_result_<exp_idx>.json
```
#### 5.4 Record Latency results
Don't forget to keep an eye on the 95th results from the client-measure. Log it and name it ```memcache_<1-3>.csv```
### Step 6: Delete Everything
To delete all nodes and resources managed by Kops, use:
```
$ ./teardown.sh
```
#### (Optional) Clean Up Jobs, Services, and Pods
If you’d like to manually remove all running jobs, services, and pods before tearing down the cluster, run the command before teardown first and then run teardown shown above:
```
$ ./run-memchached.sh
```
### Step 7: Visualize Results
I’ve integrated the instructions from ```python3 get_time.py results.json``` directly into a new script. Install the required dependencies using:
```
$ pip install -r requirements.txt
```
Then, you can simply run: 
```
$ python3 analyze_result.py
```
This script processes the results and automatically generates the required figure, following the formatting specified in the report guidelines.
