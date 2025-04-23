import os
import re
import sys
import subprocess
import time
import yaml
import argparse


core_state = {
    # 1 represents that this core is free
    # We put memcache on node-b-2core core 0
    "node-a-2core": [1, 1],
    "node-b-2core": [0, 1],
    "node-c-4core": [1, 1, 1, 1],
    "node-d-4core": [1, 1, 1, 1],
}


def build_path(job):
    return f"{POLICY}/parsec-benchmarks/{job}.yaml"


def add_job_info(jobs):
    """
    Add job to the node and core based on its yaml config
    """
    for job in jobs.keys():
        job_path = build_path(job)
        with open(job_path, "rb") as f:
            document = yaml.safe_load(f)
            node = document["spec"]["template"]["spec"]["nodeSelector"]["cca-project-nodetype"]
            cmd = document["spec"]["template"]["spec"]["containers"][0]["args"][1]
            match = re.match(r"taskset -c ([0-9,]+)", cmd)
            cores = [int(c) for c in match.group(1).split(",")]

            jobs[job]["node"] = node
            jobs[job]["cores"] = cores


def get_node(job):
    return job["node"]


def get_cores(job):
    return job["cores"]


def get_name(job):
    return job["name"]


def cores_avail(job):
    node = get_node(job)
    cores = get_cores(job)
    return all(core_state[node][i] for i in cores)


def claim_cores(job):
    name = get_name(job)
    node = get_node(job)
    cores = get_cores(job)
    for i in cores:
        core_state[node][i] = 0

    print(f"Claimed cores {cores} on node {node} for job {name}")


def free_cores(job):
    name = get_name(job)
    result = subprocess.run(
        ["kubectl", "get", "job", name, "-o", "jsonpath={.status.succeeded}"],
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        print(f"Job {name} not found or not accessible.")

    output = result.stdout.strip()
    print("Output", output, "type", type(output), "name", name)
    if output == "1":
        node = get_node(job)
        cores = get_cores(job)
        for i in cores:
            core_state[node][i] = 1
        return True

    return False
    # print(f"Job {name} finished, freed cores {cores} on node {node}")


def allocate_job(job):
    name = get_name(job)
    node = get_node(job)
    cores = get_cores(job)

    if not cores_avail(job):
        # print(f"Not sufficent cores {cores} available on for job {name} on {node}")
        return False
    print(f"Allocate {name} on {node} on cores {cores}")

    try:
        job_path = build_path(name)
        subprocess.run(["kubectl", "create", "-f", job_path], check=True)
        claim_cores(job)
        return True
    except subprocess.CalledProcessError:
        subprocess.run(["kubectl", "delete", "jobs", "--all"], check=True)
        sys.exit(1)


def run(jobs):
    jobs_allocated = []
    while len(jobs) > 0:
        time.sleep(2)
        print("\n==========================")
        print(core_state)
        print("==========================\n")
        job = jobs.pop(0)

        print("Processing ", job)
        if allocate_job(job):
            jobs_allocated.append(job)
        else:
            jobs.append(job)

        index_remove = []
        for i, job_allocated in enumerate(jobs_allocated):
            free = free_cores(job_allocated)
            if free:
                index_remove.append(i)

        jobs_allocated = [
            job for i, job in enumerate(jobs_allocated) if i not in index_remove
        ]


def print_jobs(jobs):
    for job in jobs:
        name = get_name(job)
        node = get_node(job)
        cores = get_cores(job)
        print(name, node, cores)


if __name__ == "__main__":

    policy_descriptions = """
    Scheduling Policies
        Policy 1:
            blackscholes    -> node-c-4core (0,1)
            canneal         -> node-a-2core (0,1)
            dedup:          -> node-c-4core (2,3)
            ferret:         -> node-a-2core (0,1)
            freqmine:       -> node-d-4core (0,1)
            radix:          -> node-b-2core (1)
            vips:           -> node-d-4core (2,3)
        Policy 2:
            blackscholes    -> node-c-4core (0,1,2,3)
            canneal         -> node-d-4core (0,1,2,3)
            dedup:          -> node-a-2core (0)
            ferret:         -> node-d-4core (0,1,2,3)
            freqmine:       -> node-c-4core (0,1,2,3)
            radix:          -> node-a-2core (0)
            vips:           -> node-d-4core (0,1,2,3)
        Policy 3:
            blackscholes    -> node-c-4core (0,1,2,3)
            canneal         -> node-a-2core (0,1)
            dedup:          -> node-a-2core (0,1)
            ferret:         -> node-c-4core (0,1,2,3)
            freqmine:       -> node-d-4core (0,1,2,3)
            radix:          -> node-a-2core (0,1)
            vips:           -> node-a-2core (0,1)
        Policy 4:
            blackscholes    -> node-a-2core (0,1)
            canneal         -> node-d-4core (0,1,2,3)
            dedup:          -> node-c-4core (0,1,2,3)
            ferret:         -> node-c-4core (0,1,2,3)
            freqmine:       -> node-d-4core (0,1,2,3)
            radix:          -> node-a-2core (0,1)
            vips:           -> node-d-4core (0,1,2,3)
        Policy 5:
            blackscholes    -> node-a-2core (0,1)
            canneal         -> node-d-4core (0,1,2,3)
            dedup:          -> node-c-4core (0,1,2,3)
            ferret:         -> node-c-4core (0,1,2,3)
            freqmine:       -> node-b-2core (1)
            radix:          -> node-a-2core (0,1)
            vips:           -> node-d-4core (0,1,2,3)
        Policy 6:
            blackscholes    -> node-a-2core (0,1)
            canneal         -> node-d-4core (0,1,2,3)
            dedup:          -> node-c-4core (0,1,2,3)
            ferret:         -> node-c-4core (0,1,2,3)
            freqmine:       -> node-a-2core (0,1)
            radix:          -> node-a-2core (0,1)
            vips:           -> node-d-4core (0,1,2,3)
        Policy 7:
            blackscholes    -> node-b-2core (1)
            canneal         -> node-d-4core (0,1,2,3)
            dedup:          -> node-a-2core (0,1)
            ferret:         -> node-c-4core (0,1)
            freqmine:       -> node-c-4core (2,3)
            radix:          -> node-a-2core (0,1)
            vips:           -> node-d-4core (0,1,2,3)
        Policy 8:
            blackscholes    -> node-b-2core (1)
            canneal         -> node-d-4core (0,1)
            dedup:          -> node-a-2core (0,1)
            ferret:         -> node-d-4core (2,3)
            freqmine:       -> node-c-4core (0,1,2,3)
            radix:          -> node-a-2core (0,1)
            vips:           -> node-c-4core (0,1,2,3)
    """

    parser = argparse.ArgumentParser(
        description="Select one of the available scheduling policies",
        epilog=policy_descriptions,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("policy_number",
                        type=int,
                        help="Policy number to use (see job-to-node&core mappings below)")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    POLICY = os.path.join("../policy", f"policy-{args.policy_number}")
    policy_path = os.path.join("../policy", f"policy-{args.policy_number}")

    # Validate the policy path exists
    if not os.path.exists(policy_path):
        sys.exit(f"Error: Policy {args.policy_number} not found")
    
    # Initialize jobs
    jobs = [job.removesuffix(".yaml") for job in os.listdir(f"{POLICY}/parsec-benchmarks")]
    jobs = {key: {"name": key, "node": "", "cores": []} for key in jobs}

    # Allocate job on nodes and the cores based on the policy
    add_job_info(jobs)
    jobs_list = list(jobs.values())
    run(jobs_list)
