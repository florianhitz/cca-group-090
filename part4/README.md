# User Instruction for Part 4

## Part 4 Folder Structure

## Usage Specification
Please make sure that you are under the current working directory ```/part4/src```

### Step 1. Set Up Kubernetes Nodes
This step sets up a Kubernetes cluster with 1 master and 3 worker nodes:
 - a 2-core VM cluster master
 - a 4-core high memory VM for memcached server, 7 batch jobs and scheduling controller
 - a 8-core VM for the mcperf agent
 - a 2-core VM for the mcperf measurement machine
```
$ ./setup-part4.sh
```
#### (Optional) Fix Missing Node Labels
In case that your nodes are not labelled, you can manually attach the labels using the helper script:
```
$ ./label-nodes.sh
```

### Step 2. Install Required Software on Each VM
Run the following command to install all necessary software components:
 - memcached on the memcache-server VM.
 - augmented mcperf on the client-agent and client-measure VMs (for mcperf agent and measurement machine)
 - docker on the memcache-server VM (for running the 7 batch jobs)
```
$ ./install.sh
```

###  3. SSH into the client-agent, client-measure and memcache-server VMs
#### 3.1 - Connect to client-measure
Open a new terminal and run the following for ```--scan 5000:220000:5000``` testing:
```
$ ./ssh-measure.sh
```
or for dynamic load ```--qps_interval 10 --qps_min 5000 --qps_max 180000``` testing:
```
$ ./ssh-measure-dyn.sh
```
#### 3.2 - Connect to client-agent
Open a new terminal and run:
```
$ ./ssh-client
```
Both scripts in Step 3.1 and 3.2 will automaticall print the correct memcache command. You can then copy-paste the printed command into the respective SSH session to run the load generation or measurement.
#### 3.3 - Connect to memcache-server
Open another new terminal and run:
```
$ ./ssh-memc.sh
```
At this point, there should be four terminals open:
 - the main console
 - the client-measure VM
 - the client-agent VM
 - the memcache-server VM
After each measurement, please copy the result output from client-measure VM terminal and save it under the ```results``` folder using the following naming scheme:
```
t<num_of_threads>_c<num_of_cores>-run<run_index>.txt
```

### Step 4.1.a Plot the p95 Latency for --scan 5000:220000:5000
After Step 3, you should have collected p95 lantecy results under different numbers of threads/CPU cores. Since the test under each condition is required to be simulated at least three times, there should be at least 12 files saved in the ```result``` folder.
To visualize the relationship between p95 tail latency and QPS, run:
```
python3 plot-results_4-1-a.py
```

## 4.1.d Plotting 
Collect memcached results and save it into the results-cpu folder as txt
Collect cpu results and save it into the results-cpu folder as txt

To adjust the threads follow the project description.
To adjust cores run (in the memcache terminal):
sudo taskset -a -cp [<cores as list>] <PID-MEMCACHED>

(-a flag is important!)


## 4.2 Run Batch Jobs 
Make sure you runned the install.sh script.
It takes care of the installation of everything you need for this part.

Make sure memcache is running on 1 or two cores.

You can copy the necessary python scripts into the memcache VM via:
./move-scripts.sh
You can execute it whenever you adjusted sth in the script on you host machine.

Create a venv on the memcache machine and you are good to go.





