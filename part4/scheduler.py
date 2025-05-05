#!/usr/bin/env python3

import threading
import subprocess
import time

import docker

from scheduler_logger import SchedulerLogger, Job


USAGE_THRESHOLD = 65

client = docker.from_env()
sl = SchedulerLogger()

images_to_pull = {
    'blackscholes': 'anakli/cca:parsec_blackscholes',
    'canneal': 'anakli/cca:parsec_canneal',
    'dedup': 'anakli/cca:parsec_dedup',
    'ferret': 'anakli/cca:parsec_ferret',
    'freqmine': 'anakli/cca:parsec_freqmine',
    'radix': 'anakli/cca:splash2x_radix',
    'vips': 'anakli/cca:parsec_vips',
}

image_commands = {
    'blackscholes': './run -a run -S parsec -p blackscholes -i native -n 4',
    'canneal': './run -a run -S parsec -p canneal -i native -n 4',
    'dedup': './run -a run -S parsec -p dedup -i native -n 4',
    'ferret': './run -a run -S parsec -p ferret -i native -n 4',
    'freqmine': './run -a run -S parsec -p freqmine -i native -n 4',
    'radix': './run -a run -S splash2x -p radix -i native -n 4',
    'vips': './run -a run -S parsec -p vips -i native -n 4',
}

for image in images_to_pull.values():
    print(f'Pulling image {image}')
    client.images.pull(image)


def get_memached_cup_usage(pid):
    out = subprocess.check_output(['pidstat', '-p', str(pid), '1', '1']).decode().strip()
    out = out.split('\n')[-1].split()[-3]
    return float(out)

def adjust_memcached_cores(pid, cores=1):
    current_cores = subprocess.check_output(['sudo', 'taskset', '-pc', str(pid)]).decode().strip()
    current_cores = current_cores.split(':')[-1].strip().split(',')
    current_cores = len(current_cores)

    if current_cores == cores:
        print(f'No core adjustment. cur: {current_cores}, cores: {cores}')
        return False

    if cores == 1:
        subprocess.check_output(['sudo', 'taskset', '-a', '-cp', '0', str(pid)])
        sl.update_cores(Job.MEMCACHED, [0])
        print(f'Usage: {usage}, increase cores')
    elif cores == 2:
        subprocess.check_output(['sudo', 'taskset', '-a', '-cp', '0,1', str(pid)])
        sl.update_cores(Job.MEMCACHED, [0, 1])
        print(f'Usage: {usage}, increase cores')
    else:
        print(f'Number of cores not supported: {cores}')
    return True
     


queue_shared_cores = ['blackscholes', 'radix']
queue = ['dedup', 'ferret', 'freqmine', 'vips', 'canneal']

containers_1_ready = []
containers_1_done = []
container_1_running = None

containers_23_ready = []
containers_23_done = []
container_23_running = None

for name in queue_shared_cores:
    image = images_to_pull[name]
    command = image_commands[name]
    containers_1_ready += [client.containers.create(image, name=name, cpuset_cpus='1', detach=True, command=command)]

for name in queue:
    image = images_to_pull[name]
    command = image_commands[name]
    containers_23_ready +=  [client.containers.create(image, name=name, cpuset_cpus='2,3', detach=True, command=command)]

pid = subprocess.check_output(['pgrep', 'memcached']).decode().strip()


start = time.time()
while True:
    if len(containers_1_done) == 2 and len(containers_23_done) == 5:
        break

    time.sleep(1)

    usage = get_memached_cup_usage(pid)
    print(f'usage: {usage}')

    if container_1_running:
        container_1_running.reload()
        print(container_1_running.status)

    if usage >= USAGE_THRESHOLD:
        if adjust_memcached_cores(pid, 2) and container_1_running and container_1_running.status == 'running':
            container_1_running.pause()
    else:
        if adjust_memcached_cores(pid, 1) and container_1_running and container_1_running.status == 'paused':
            container_1_running.unpause()


    if container_1_running and container_1_running.status == 'exited':
        containers_1_done += [container_1_running]
        container_1_running = None
        
    if not container_1_running and len(containers_1_ready):
        container_1_running = containers_1_ready.pop()  
        container_1_running.start()

    
    # core 2, 3 logic
    if container_23_running:
        container_23_running.reload()

    if container_23_running and container_23_running.status == 'exited':
        containers_23_done += [container_23_running]
        container_23_running = None
    
    if not container_23_running and len(containers_23_ready):
        container_23_running = containers_23_ready.pop()  
        container_23_running.start()

end = time.time()

duration = end - start

print(f'Took {duration:.2f} seconds')
     
        
        
    
    
    
    
    


#print(containers_23)
# watch_cpu(pid)

# def cli():
#     while True:
#         cmd = input('>> ')
#         if cmd == 'run':
#             image = images_to_pull[0]
#             client.containers.run(image, cpuset_cpus='0', detach=True, remove=False, name='parsec', command='./run -a run -S parsec -p blackscholes -i native -n 2')
#         print(cmd)
# 
# cli()
    
    
