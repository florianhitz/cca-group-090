## 1. Initialization
run setup-part4.sh

## 2. Installation
run install.sh

This will install all the necessary requirements (memcache, docker etc.) on all the vms.

## 3. Login
In a separate terminal run:
ssh-measure-dyn.sh (for dynamic load) or ssh-measure.sh (for constant load)

In a separate terminal run:
ssh-client

Both of the above scripts will automaticall print the correct memcache command.
This command can be copy-pasted into the cli to run client or measure respectively.

In a separate terminal run:
ssh-memc.sh

You are now logged into three different vms (in three different terminal windows)

## 4.1.a Plotting 
Collect memcached results and save it into the results folder as txt
Then run 
plot-results_4-1-a.py
to generate the plot.

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





