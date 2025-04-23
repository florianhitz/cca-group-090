import json
from datetime import datetime


def parse_batch_timings(json_path):
    """
    Parses a JSON file containing Kubernetes pod status info and extracts
    job execution times (excluding memcached), returning start/completion 
    times and total time span.
    
    Parameters:
        json_path (str): Path to the JSON file.
        
    Returns:
        job_timings (list of dict): Each with keys: 'name', 'start', 'end', 'duration'.
        total_time (timedelta): Total span between earliest start and latest completion.
    """
    time_format = '%Y-%m-%dT%H:%M:%SZ'
    with open(json_path, 'r') as file:
        data = json.load(file)

    job_timings = []
    start_times = []
    completion_times = []

    for item in data['items']:
        name = item['status']['containerStatuses'][0]['name']
        if name == "memcached":
            continue

        try:
            start_time = datetime.strptime(
                item['status']['containerStatuses'][0]['state']['terminated']['startedAt'],
                time_format)
            end_time = datetime.strptime(
                item['status']['containerStatuses'][0]['state']['terminated']['finishedAt'],
                time_format)
            job_timings.append({
                'job_name': name,
                'start_time': start_time,
                'completion_time': end_time,
                'job_time': end_time - start_time
            })
            start_times.append(start_time)
            completion_times.append(end_time)
        except KeyError:
            raise RuntimeError(f"Job '{name}' has not completed.")

    if len(job_timings) != 7:
        raise RuntimeError("You haven't run all the PARSEC jobs (7 expected).")

    total_time = max(completion_times) - min(start_times)
    return job_timings, total_time

"""
The following is provided by the course repo.
However I modified it to the one above for
the convenience of the visualization.
"""
# import json
# import sys
# from datetime import datetime


# time_format = '%Y-%m-%dT%H:%M:%SZ'
# file = open(sys.argv[1], 'r')
# json_file = json.load(file)

# start_times = []
# completion_times = []
# for item in json_file['items']:
#     name = item['status']['containerStatuses'][0]['name']
#     print("Job: ", str(name))
#     if str(name) != "memcached":
#         try:
#             start_time = datetime.strptime(
#                     item['status']['containerStatuses'][0]['state']['terminated']['startedAt'],
#                     time_format)
#             completion_time = datetime.strptime(
#                     item['status']['containerStatuses'][0]['state']['terminated']['finishedAt'],
#                     time_format)
#             print("Job time: ", completion_time - start_time)
#             start_times.append(start_time)
#             completion_times.append(completion_time)
#         except KeyError:
#             print("Job {0} has not completed....".format(name))
#             sys.exit(0)

# if len(start_times) != 7 and len(completion_times) != 7:
#     print("You haven't run all the PARSEC jobs. Exiting...")
#     sys.exit(0)

# print("Total time: {0}".format(max(completion_times) - min(start_times)))
# file.close()