import subprocess
import time

import docker

from scheduler_logger import SchedulerLogger, Job

USAGE_THRESHOLD = 60

client = docker.from_env()
sl = SchedulerLogger()

images_to_pull = [
    'anakli/cca:parsec_blackscholes',
    'anakli/cca:parsec_canneal',
    'anakli/cca:parsec_dedup',
    'anakli/cca:parsec_ferret',
    'anakli/cca:parsec_freqmine',
    'anakli/cca:splash2x_radix',
    'anakli/cca:parsec_vips',
]

for image in images_to_pull:
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

    
    print(f'Requested Cores: {cores}, running cores: {current_cores}')
    if current_cores == cores:
        return

    if cores == 1:
        subprocess.check_output(['sudo', 'taskset', '-a', '-cp', '0', str(pid)])
    elif cores == 2:
        subprocess.check_output(['sudo', 'taskset', '-a', '-cp', '0,1', str(pid)])
    else:
        print(f'Number of cores not supported: {cores}')
        
    
    


pid = subprocess.check_output(['pgrep', 'memcached']).decode().strip()
while True:
    usage = get_memached_cup_usage(pid)

    print(f'CPU usage: {usage}')

    time.sleep(1)

    if usage >= USAGE_THRESHOLD:
        print(f'Usage: {usage}, increase cores')
        sl.update_cores(Job.MEMCACHED, [0,1])
        adjust_memcached_cores(pid, 2)
    else:
        print(f'Usage: {usage}, decrease cores')
        sl.update_cores(Job.MEMCACHED, [0])
        adjust_memcached_cores(pid, 1)


    
    
