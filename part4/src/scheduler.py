#!/usr/bin/env python3

import subprocess
import time
import docker

from scheduler_logger import SchedulerLogger, Job

# Increase CPU cores if memcached CPU usage >= 65%
USAGE_THRESHOLD = 65

client = docker.from_env()
sl = SchedulerLogger()
sl.job_start(Job.MEMCACHED, [0], 2)

images_to_pull = {
    "blackscholes": "anakli/cca:parsec_blackscholes",
    "canneal": "anakli/cca:parsec_canneal",
    "dedup": "anakli/cca:parsec_dedup",
    "ferret": "anakli/cca:parsec_ferret",
    "freqmine": "anakli/cca:parsec_freqmine",
    "radix": "anakli/cca:splash2x_radix",
    "vips": "anakli/cca:parsec_vips",
}

# for minimum thread number see
# https://users.soe.ucsc.edu/~renau/docs/wddd15.pdf
image_commands = {
    "blackscholes": "./run -a run -S parsec -p blackscholes -i native -n 2",
    "canneal": "./run -a run -S parsec -p canneal -i native -n 4",
    "dedup": "./run -a run -S parsec -p dedup -i native -n 4",
    "ferret": "./run -a run -S parsec -p ferret -i native -n 4",
    "freqmine": "./run -a run -S parsec -p freqmine -i native -n 4",
    "radix": "./run -a run -S splash2x -p radix -i native -n 4",
    "vips": "./run -a run -S parsec -p vips -i native -n 2",
}

for image in images_to_pull.values():
    print(f"Pulling image {image}")
    client.images.pull(image)


def measure_memcache_cpu_core():
    pid = subprocess.check_output(["pgrep", "memcached"]).decode().strip()
    current_cores = (
        subprocess.check_output(["sudo", "taskset", "-pc", str(pid)]).decode().strip()
    )
    current_cores = current_cores.split(":")[-1].strip().split(",")
    current_cores = len(current_cores)

    return current_cores


def get_memached_cup_usage(pid):
    """
    Uses pidstat to retrieve memcached CPU usage by PID
    """
    out = (
        subprocess.check_output(["pidstat", "-p", str(pid), "1", "1"]).decode().strip()
    )
    out = out.split("\n")[-1].split()[-3]
    return float(out)


def adjust_memcached_cores(pid, cores=1):
    """
    Uses taskset to bind memcached to 1 or 2 cores depending on need.
    And logs changes using SchedulerLogger.
    """
    t0 = time.time()
    sl.custom_event(Job.MEMCACHED, f"scale-request at {t0}")
    current_cores = (
        subprocess.check_output(["sudo", "taskset", "-pc", str(pid)]).decode().strip()
    )
    current_cores = current_cores.split(":")[-1].strip().split(",")
    current_cores = len(current_cores)

    if current_cores == cores:
        print(f"No core adjustment. cur: {current_cores}, cores: {cores}")
        return False

    if cores == 1:
        subprocess.check_output(["sudo", "taskset", "-a", "-cp", "0", str(pid)])
        sl.update_cores(Job.MEMCACHED, [0])
        print(f"Usage: {usage}, increase cores")
    elif cores == 2:
        subprocess.check_output(["sudo", "taskset", "-a", "-cp", "0,1", str(pid)])
        sl.update_cores(Job.MEMCACHED, [0, 1])
        print(f"Usage: {usage}, increase cores")
    else:
        print(f"Number of cores not supported: {cores}")

    t1 = time.time()
    sl.custom_event(Job.MEMCACHED, f"scale-effective at {t1}")

    timestamp = time.time()
    memcached_core_log[timestamp] = cores

    return True


queue_shared_cores = []
queue = ["dedup", "ferret", "freqmine", "vips", "canneal", "radix", "blackscholes"]

containers_1_ready = []
containers_1_done = []
container_1_running = None

containers_23_ready = []
containers_23_done = []
container_23_running = None

memcached_core_log = {}

for name in queue_shared_cores:
    image = images_to_pull[name]
    command = image_commands[name]
    containers_1_ready += [
        client.containers.create(
            image, name=name, cpuset_cpus="1", detach=True, command=command
        )
    ]

for name in queue:
    image = images_to_pull[name]
    command = image_commands[name]
    containers_23_ready += [
        client.containers.create(
            image, name=name, cpuset_cpus="2,3", detach=True, command=command
        )
    ]

pid = subprocess.check_output(["pgrep", "memcached"]).decode().strip()

usage = get_memached_cup_usage(pid)

start = time.time()
end = 0
last_measure_time = time.time()

while True:
    if len(containers_1_done) == 0 and len(containers_23_done) == 7:
        end = time.time()

    current_time = time.time()
    if current_time > start + 1800:
        break

    if current_time - last_measure_time >= 5:
        core_count = measure_memcache_cpu_core()
        memcached_core_log[current_time] = core_count
        print(f"[{current_time:.2f}] memcached uses {core_count} cores")
        last_measure_time = current_time

    time.sleep(1)
    usage = get_memached_cup_usage(pid)
    print(f"usage: {usage}")

    if container_1_running:
        container_1_running.reload()
        print(container_1_running.status)

    """
    core 1 logic: memcache core allocation is done here
    If memcached uses >= 65%, allocate 2 cores to it and reduce batch job CPU quota.
    If memcached uses < 65%, reduce its cores and restore CPU to batch job.
    """
    if usage >= USAGE_THRESHOLD:
        t_detect = time.time()
        if (
            adjust_memcached_cores(pid, 2)
            and container_1_running
            and container_1_running.status == "running"
        ):
            # container_1_running.pause()
            container_1_running.update(
                cpuset_cpus="1", cpu_period=100_000, cpu_quota=25_000
            )
    else:
        t_detect = time.time()
        if (
            adjust_memcached_cores(pid, 1)
            and container_1_running
            and container_1_running.status == "running"
        ):
            # if adjust_memcached_cores(pid, 1) and container_1_running and container_1_running.status == 'paused':
            container_1_running.update(
                cpuset_cpus="1", cpu_period=100_000, cpu_quota=100_000
            )
            # container_1_running.unpause()

    if container_1_running and container_1_running.status == "exited":
        job_name = container_1_running.name
        sl.job_end(Job[job_name.upper()])
        containers_1_done += [container_1_running]
        container_1_running = None

    if not container_1_running and len(containers_1_ready):
        container_1_running = containers_1_ready.pop()
        job_name = container_1_running.name
        sl.job_start(Job[job_name.upper()], [1], 4)
        container_1_running.start()

    """
    core 2,3 logic
    When memcached load is low, increase quota for batch applications.
    """
    if container_23_running:
        container_23_running.reload()

    # when container_1 finished allow to use max resources available
    if (
        len(containers_1_done) == 0
        and container_23_running
        and container_23_running.status == "running"
    ):
        job_name = container_23_running.name
        if usage <= 30:
            print(f"usage: {usage}, setting new quota 350")
            container_23_running.update(
                cpuset_cpus="0,1,2,3", cpu_period=100_000, cpu_quota=350_000
            )
            sl.update_cores(Job[job_name.upper()], [0, 1, 2, 3])
        elif usage <= USAGE_THRESHOLD:
            print(f"usage: {usage}, setting new quota 325")
            container_23_running.update(
                cpuset_cpus="0,1,2,3", cpu_period=100_000, cpu_quota=325_000
            )
            sl.update_cores(Job[job_name.upper()], [0, 1, 2, 3])
        elif usage <= 100:
            print(f"usage: {usage}, setting new quota 300")
            container_23_running.update(
                cpuset_cpus="1,2,3", cpu_period=100_000, cpu_quota=300_000
            )
            sl.update_cores(Job[job_name.upper()], [1, 2, 3])
        else:
            print(f"usage: {usage}, setting new quota 200")
            container_23_running.update(
                cpuset_cpus="2,3", cpu_period=100_000, cpu_quota=200_000
            )
            sl.update_cores(Job[job_name.upper()], [2, 3])

    if container_23_running and container_23_running.status == "exited":
        job_name = container_23_running.name
        sl.job_end(Job[job_name.upper()])
        containers_23_done += [container_23_running]
        container_23_running = None

    if not container_23_running and len(containers_23_ready):
        container_23_running = containers_23_ready.pop()
        job_name = container_23_running.name
        sl.job_start(Job[job_name.upper()], [2, 3], 4)
        container_23_running.start()

    if "t_detect" in locals():
        t_done = time.time()
        sl.custom_event(Job.MEMCACHED, f"reaction-latency {t_done - t_detect:.3f}")
        del t_detect

sl.end()

# Report
print("\nMemcached Core Allocation Log:")
for t, c in memcached_core_log.items():
    print(f"At {t:.3f}, memcached was assigned {c} cores")
