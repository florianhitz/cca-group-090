import os
import re
import sys
import subprocess
import time

import yaml

policy = sys.argv[1]

core_state = {
    "node-a-2core": [1, 1],
    "node-b-2core": [0, 1],  # memcached
    "node-c-4core": [1, 1, 1, 1],
    "node-d-4core": [1, 1, 1, 1],
}


job_paths = os.listdir(f"{policy}/parsec-benchmarks")


def cores_avail(node, cores):
    return all(core_state[node][i] for i in cores)


def claim_cores(node, cores):
    for i in cores:
        core_state[node][i] = 0


def allocate_job(job_path):
    job_path_abs = f"{policy}/parsec-benchmarks/{job_path}"
    with open(job_path_abs, "rb") as f:
        document = yaml.safe_load(f)
        node = document["spec"]["template"]["spec"]["nodeSelector"][
            "cca-project-nodetype"
        ]
        cmd = document["spec"]["template"]["spec"]["containers"][0]["args"][1]
        match = re.match(r"taskset -c ([0-9,]+)", cmd)
        cores = [int(c) for c in match.group(1).split(",")]

        if not cores_avail(node, cores):
            print(
                f"Not sufficent cores available on requested machine. {node}, {cores}"
            )
            return False

        try:
            subprocess.run(["kubectl", "create", "-f", job_path_abs], check=True)
            claim_cores(node, cores)
            return True
        except subprocess.CalledProcessError as e:
            subprocess.run(["kubectl", "delete", "jobs", "--all"], check=True)
            print(e.stderr)
            sys.exit(1)


while len(job_paths) > 0:
    print(core_state)
    time.sleep(1)
    job = job_paths.pop()
    if not allocate_job(job):
        job_paths.append(job)
