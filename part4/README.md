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
After each measurement, please copy the result output from client-measure VM terminal and save it under the corresponding directories specified in the following steps based on your needs.

### Step 4.1.a Plot the p95 Latency for --scan 5000:220000:5000
After Step 3, you should have collected p95 lantecy results under different numbers of threads/CPU cores. Since the test under each condition is required to be simulated at least three times, there should be at least 12 files saved in the ```part4/result/log/4-1-a``` folder.
To visualize the relationship between p95 tail latency and QPS under various configurations, run:
```
python3 plot-results_4-1-a.py
```
The file is called `plot-results_4-1-a.py` because it corresponds to part 4.1.a in the report. The visualization script will output some warnings in the terminal as a function is deprecated but it won't affect the successful generation of a plot.

### Step 4.1.d Plot the p95 Latency and CPU Utilization for --scan 5000:220000:5000 with 1 vs 2 Core Comparison
Collect the memcached results and save as .txt files in the ```part4/result/log/4-1-d``` directory, using the naming scheme ```t2c<1/2>-run<1/2/3>.txt```
Collect the CPU usage results and save them in the same ```log/4-1-d``` directory with the naming scheme ```cpu<1/2>-run<1/2/3>.txt```
To visualize the relationship between the achieved QPS, p95 tail latency and CPU utilization under 1-core vs. 2-core settings, run:
```
python3 plot-results_4-1-d.py <1/2>
```
The file is named `plot-results_4-1-d.py` to correspond with part 4.1.d in the report. Again, the visualization script will output some warnings in the terminal as a function is deprecated but it won't affect the successful generation of a plot.

To adjust the number of threads follow the project description.
To adjust the number of CPU cores, run the following in the memcached server terminal:
```
sudo taskset -a -cp [<cores as list>] <PID-MEMCACHED>
```

(-a flag is important!)


## 4.2 Run Batch Jobs 
Make sure you runned the install.sh script.
It takes care of the installation of everything you need for this part.

Make sure memcache is running on 1 or two cores.

You can copy the necessary python scripts into the memcache VM via:
./move-scripts.sh
You can execute it whenever you adjusted sth in the script on you host machine.

Create a venv on the memcache machine and you are good to go.





