import os
import pandas as pd
from get_time import *

# Global variable
experiment_iterations = 3


def batch_result_to_df(jobs_times, total_time):

    df = pd.DataFrame(jobs_times)
    df['job_time'] = df['job_time'].apply(lambda td: int(td.total_seconds()))
    
    # Add a new row into the df
    total = pd.DataFrame([{
        "job_name": "total_time",
        "start_time": pd.NaT,
        "completion_time": pd.NaT,
        "job_time": int(total_time.total_seconds())
    }])
    df = pd.concat([df, total], ignore_index=True)
    
    return df


def cal_job_time_mean_std(dfs):

    df_all = pd.concat(dfs)
    summary_df = df_all.groupby('job_name')['job_time'].agg(['mean', 'std'])
    summary_df = summary_df.round(3)

    return summary_df


if __name__ == "__main__":

    result_dir = "../result"
    dfs = []

    # I know this way is super stupid, but I don't wanna change get_time.py
    for i in range(0, experiment_iterations):

        result_file = os.path.join(result_dir, f"batch_result_{i+1}.json")
        jobs_times, total_time = parse_batch_timings(result_file)

        df = batch_result_to_df(jobs_times, total_time)
        dfs.append(df)
    
    for i, df in enumerate(dfs):
        print(f"\n===================== Result from Experiment {i+1} =====================")
        print(df)

    job_time_mean_std = cal_job_time_mean_std(dfs)
    print(job_time_mean_std)
