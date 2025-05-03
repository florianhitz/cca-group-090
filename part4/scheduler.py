import subprocess
import time

import docker

from scheduler_logger import SchedulerLogger, Job

USAGE_THRESHOLD = 35

CORES = [0, 1, 2, 3]
mem_cores = [0]

client = docker.from_env()
sl = SchedulerLogger()

job_images = {
    "blackscholes": "anakli/cca:parsec_blackscholes",
    "canneal": "anakli/cca:parsec_canneal",
    "dedup": "anakli/cca:parsec_dedup",
    "ferret": "anakli/cca:parsec_ferret",
    "freqmine": "anakli/cca:parsec_freqmine",
    "radix": "anakli/cca:splash2x_radix",
    "vips": "anakli/cca:parsec_vips",
}

# pull all images
for image in job_images.values():
    print(f"Pulling image {image}")
    client.images.pull(image)

# still pending jobs to be completed
pending = list(job_images.items())
# dict for tracking running jobs
running = {}


def get_memached_cup_usage(pid):
    out = (
        subprocess.check_output(["pidstat", "-p", str(pid), "1", "1"]).decode().strip()
    )
    out = out.split("\n")[-1].split()[-3]
    return float(out)


def adjust_memcached_cores(pid, cores):
    global mem_cores
    mask = "0" if cores == 1 else "0,1"
    subprocess.check_call(["sudo", "taskset", "-a", "-cp", mask, str(pid)])
    mem_cores = list(map(int, mask.split(",")))
    sl.update_cores(Job.MEMCACHED, mem_cores)
    print(f"Scaled memcached to cores {mem_cores}")


pid = subprocess.check_output(["pgrep", "-o", "memcached"]).decode().strip()

# only exit once all jobs are completed
while pending or running:
    # no job is running but there are still pending ones
    if not running and pending:
        job, image = pending.pop(0)
        free = [core for core in CORES if core not in mem_cores]
        cpuset = ",".join(str(core) for core in free)
        print(f"Launching batch job {job} on cores {cpuset}")
        ctr = client.containers.run(
            image,
            [
                "./run",
                "-a",
                "run",
                "-S",
                "parsec",
                "-p",
                job,
                "-i",
                "native",
                "-n",
                "2",
            ],
            cpuset_cpus=cpuset,
            detach=True,
        )
        running[job] = ctr
        sl.job_start(Job(job), free, 2)

    for job, ctr in list(running.items()):
        ctr.reload()
        if ctr.status == "exited":
            print(f"Batch job {job} completed")
            sl.job_end(Job(job))
            running.pop(job)

    usage = get_memached_cup_usage(pid)

    print(f"CPU usage: {usage}")

    if usage >= USAGE_THRESHOLD:
        print(f"Usage: {usage}, increase cores")
        sl.update_cores(Job.MEMCACHED, [0, 1])
        adjust_memcached_cores(pid, 2)
    else:
        print(f"Usage: {usage}, decrease cores")
        sl.update_cores(Job.MEMCACHED, [0])
        adjust_memcached_cores(pid, 1)

    # check if core is available, if so update batch job to run on it
    if running:
        job, ctr = next(iter(running.items()))
        free = [core for core in CORES if core not in mem_cores]
        cpuset = ",".join(str(c) for c in free)
        print(f"Resizing batch job {job} to cores {cpuset}")
        ctr.update(cpuset_cpus=cpuset)
        sl.update_cores(Job(job), free)

    time.sleep(1)

sl.end()
