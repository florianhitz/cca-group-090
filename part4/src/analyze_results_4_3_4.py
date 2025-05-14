import re
import os
import ast
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta


job_label_y = {
    "blackscholes": 0.1,
    "canneal": 0.2,
    "dedup": 0.3,
    "ferret": 0.4,
    "freqmine": 0.5,
    "radix": 0.6,
    "vips": 0.7
}

job_colors = {
    "blackscholes": "rgba(204, 160, 0, 0.6)",
    "canneal": "rgba(204, 204, 170, 0.6)",
    "dedup": "rgba(204, 172, 202, 0.6)",
    "ferret": "rgba(170, 204, 202, 0.6)",
    "freqmine": "rgba(12, 202, 0, 0.6)",
    "radix": "rgba(0, 204, 160, 0.6)",
    "vips": "rgba(204, 10, 0, 0.6)"
}


def amplify_jobs_file(job_file, memcache_cpu_core_file):

    memcache_cpu_core = {}

    with open(memcache_cpu_core_file) as f:
        for line in f:
            if "At" in line:
                parts = line.strip().split()
                timestamp = datetime.fromtimestamp(float(parts[1].strip(','))) - timedelta(hours=2)
                num_cores = int(parts[-2])
                if num_cores == 1:
                    cores = [0]
                elif num_cores == 2:
                    cores = [0,1]
                memcache_cpu_core[timestamp] = cores
    
    with open(job_file, "r") as f:
        lines = f.readlines()

    combined_entries = []

    for line in lines:
        if "update_cores memcached" in line:
            continue
        parts = line.strip().split()
        timestamp = pd.to_datetime(parts[0])
        combined_entries.append((timestamp, line))
    
    for timestamp, cores in memcache_cpu_core.items():
        formatted_cores = "[" + ",".join(map(str, memcache_cpu_core[timestamp])) + "]"
        line = f"{timestamp.isoformat()} update_cores memcached {formatted_cores}\n"
        combined_entries.append((timestamp, line))

    combined_entries.sort(key=lambda x: x[0])

    with open(job_file, "w") as f:
        for _, line in combined_entries:
            f.write(line)


def load_mcperf_file(mcperf_file):

    p95_latency = []
    actual_qps = []
    timestamp_start = None
    timestamp_end = None

    with open(mcperf_file, "r") as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith("read"):
            parts = re.split(r"\s+", line.strip())
            p95 = round(float(parts[-6]) / 1000, 1)
            qps = float(parts[-2])
            p95_latency.append(p95)
            actual_qps.append(qps)
        elif line.startswith("Timestamp start"):
            timestamp_start = int(line.strip().split()[-1])/1000
        elif line.startswith("Timestamp end"):
            timestamp_end = int(line.strip().split()[-1])/1000
    
    return p95_latency, actual_qps, timestamp_start, timestamp_end


def load_job_file(job_info_file):

    job_info = {}
    total_makespan = 0
    job_names = job_label_y.keys()
    memcache_cpu_core = {}

    with open(job_info_file) as f:
        for line in f:
            if "start" in line and any(job in line for job in job_names):
                parts = line.strip().split()
                job_name = parts[2]
                start_time = parts[0]
                if job_name not in job_info:
                    job_info[job_name] = {}
                job_info[job_name]["start"] = start_time
            elif "end" in line and any(job in line for job in job_names):
                parts = line.strip().split()
                job_name = parts[-1]
                if job_name not in job_info:
                    job_info[job_name] = {}
                job_info[job_name]["end"] = parts[0]
            elif "memcached" in line:
                parts = line.strip().split()
                timestamp = pd.to_datetime(parts[0]) + pd.Timedelta(hours=2)
                if "start" in line:
                    cores = len(ast.literal_eval(parts[-2]))
                else:
                    cores = len(ast.literal_eval(parts[-1]))
                memcache_cpu_core[timestamp] = cores
    
    job_info_df = pd.DataFrame.from_dict(job_info, orient="index")
    job_info_df.index.name = "job"
    job_info_df = job_info_df.reset_index()
    job_info_df["start"] = pd.to_datetime(job_info_df["start"]) + pd.Timedelta(hours=2)
    job_info_df["end"] = pd.to_datetime(job_info_df["end"])+ pd.Timedelta(hours=2)
    job_info_df["duration"] = job_info_df["end"] - job_info_df["start"]
    job_info_df["duration"] = job_info_df["duration"].dt.total_seconds()

    total_makespan = job_info_df["end"].max() - job_info_df["start"].min()
    total_makespan = total_makespan.total_seconds()

    return job_info_df, total_makespan, memcache_cpu_core


def plot_type_a(mcperf_file, job_file, exp_idx, report_part):

    p95_latency, actual_qps, timestamp_start, timestamp_end = load_mcperf_file(mcperf_file)
    job_info_df, total_makespan, memcache_cpu_core = load_job_file(job_file)
    benchmark_start = datetime.fromtimestamp(timestamp_start)
    benchmark_start_mark = benchmark_start.strftime('%Y-%m-%d %H:%M:%S')

    time_axis = list(range(0, len(p95_latency)*10, 10))

    fig = go.Figure()

    # Left y-axis: p95 latency
    fig.add_trace(go.Scatter(
        x = time_axis,
        y = p95_latency,
        name = "p95 latency (ms)",
        yaxis="y1",
        mode = "lines+markers"
    ))

    # Right y-axis: QPS
    fig.add_trace(go.Scatter(
        x=time_axis,
        y=actual_qps,
        name="Achieved QPS",
        yaxis="y2",
        mode="lines"
    ))

    # The horizontal 0.8ms SLO
    fig.add_shape(
        type="line",
        x0=0, x1=max(time_axis),
        y0=0.8, y1=0.8,
        line=dict(
            color="blue",
            width=2,
            dash="dash"
        ),
        yref="y"
    )

    # Indicate the start time
    fig.add_annotation(
        text=f"Experiment Start Time: {benchmark_start_mark}",
        xref="paper", yref="paper",
        x=0, y=-0.2,
        showarrow=False,
        font=dict(size=12),
        align="left"
    )

    # Add job annotations
    for _, row in job_info_df.iterrows():
        rel_start = (row["start"] - benchmark_start).total_seconds()
        job = row["job"]

        if job in job_label_y:
            y_label_pos = job_label_y[job]
            duration = (row["end"] - row["start"]).total_seconds()
            color = job_colors.get(job, "#CCCCCC")

            # Jobs start
            fig.add_shape(
                type="line",
                x0=rel_start, x1=rel_start,
                y0=0, y1=y_label_pos - 0.03,
                xref="x",
                yref="paper",
                line=dict(
                    color=color,
                    width=1,
                    dash="dash"
                )
            )

            fig.add_annotation(
                x=rel_start,
                y=y_label_pos,
                text=f"<b>{job}</b><br>start: {rel_start:.1f}s<br>duration: {duration:.1f}s",
                showarrow=False,
                yref="paper",
                bgcolor=color,
                font=dict(color="black", size=10)
            )

    # Layout with dual y-axes
    fig.update_layout(
        title = f"Experiment {exp_idx}: P95 Latency and Achieved QPS Over 30 Mins",
        width=1200,
        height=500,
        xaxis = dict(title="Time (s)", range=[0, 1800]),
        yaxis = dict(
            title = "p95 Latency (ms)",
            side = "left",
            showgrid=False
        ),
        yaxis2 = dict(
            title = "Achieved QPS",
            overlaying = "y",
            side = "right",
            showgrid=False
        ),
        legend = dict(x=0.01, y=0.99),
        template = "plotly_white"
    )

    fig.show()
    fig_dir = "../result/fig/"
    fig.write_image(os.path.join(fig_dir, f"part_{report_part}_experiment_{exp_idx}_p95_latency_and_achieved_qps_30mins.png"), scale=3, engine="kaleido")
    fig.write_html(os.path.join(fig_dir, f"part_{report_part}_experiment_{exp_idx}_p95_latency_and_achieved_qps_30mins.html"))


def plot_type_b(mcperf_file, job_file, exp_idx, report_part):

    p95_latency, actual_qps, timestamp_start, timestamp_end = load_mcperf_file(mcperf_file)
    job_info_df, total_makespan, memcache_cpu_core = load_job_file(job_file)
    benchmark_start = datetime.fromtimestamp(timestamp_start)
    benchmark_start_mark = benchmark_start.strftime('%Y-%m-%d %H:%M:%S')
    timestamp_end = datetime.fromtimestamp(timestamp_end)

    # Time axis based on QPS data (10-second intervals)
    time_axis = list(range(0, len(actual_qps) * 10, 10))

    memcache_core_timestamps = []
    core_num_list = []

    for memcache_core_timestamp, core_num in memcache_cpu_core.items():
        if memcache_core_timestamp > timestamp_end:
            break
        memcache_core_timestamps.append((memcache_core_timestamp-benchmark_start).total_seconds())
        core_num_list.append(core_num)

    fig = go.Figure()

    # Left y-axis: cores for memcache
    fig.add_trace(go.Scatter(
        x=memcache_core_timestamps,
        y=core_num_list,
        name = "Memcached CPU Cores",
        yaxis="y1",
        mode = "lines+markers"
    ))

    # Right y-axis: QPS
    fig.add_trace(go.Scatter(
        x=time_axis,
        y=actual_qps,
        name="Achieved QPS",
        yaxis="y2",
        mode="lines"
    ))

    # Indicate the start time
    fig.add_annotation(
        text=f"Experiment Start Time: {benchmark_start_mark}",
        xref="paper", yref="paper",
        x=0, y=-0.2,
        showarrow=False,
        font=dict(size=12),
        align="left"
    )

    # Add job annotations
    for _, row in job_info_df.iterrows():
        rel_start = (row["start"] - benchmark_start).total_seconds()
        job = row["job"]
        duration = (row["end"] - row["start"]).total_seconds()

        if job in job_label_y:
            y_label_pos = job_label_y[job]
            rel_end = rel_start + duration
            color = job_colors.get(job, "#CCCCCC")

            # Jobs start
            fig.add_shape(
                type="line",
                x0=rel_start, x1=rel_start,
                y0=0, y1=y_label_pos - 0.03,
                xref="x",
                yref="paper",
                line=dict(
                    color=color,
                    width=1,
                    dash="dash"
                )
            )

            fig.add_annotation(
                x=rel_start,
                y=y_label_pos,
                text=f"<b>{job}</b><br>start: {rel_start:.1f}s<br>duration: {duration:.1f}s",
                showarrow=False,
                yref="paper",
                bgcolor=color,
                font=dict(color="black", size=10)
            )

    # Layout with dual y-axes
    fig.update_layout(
        title = f"Experiment {exp_idx}: Memcached CPU Core Allocation",
        width=1200,
        height=500,
        xaxis = dict(title="Time (s)", range=[0, 1800]),
        yaxis = dict(
            title = "Memcached CPU Cores",
            side = "left",
            tickmode="linear",
            dtick=1,
            tickvals=[1, 2],
            range=[0.5, 2.5]
        ),
        yaxis2 = dict(
            title = "Achieved QPS",
            overlaying = "y",
            side = "right",
            showgrid=False
        ),
        legend = dict(x=0.01, y=0.99),
        template = "plotly_white"
    )

    fig.show()
    fig_dir = "../result/fig/"
    fig.write_image(os.path.join(fig_dir, f"part_{report_part}_experiment_{exp_idx}_memcached_cpu_core_allocation_over_30mins.png"), scale=3, engine="kaleido")
    fig.write_html(os.path.join(fig_dir, f"part_{report_part}_experiment_{exp_idx}_memcached_cpu_core_allocation_over_30mins.html"))


def cal_job_mean_std_time(job_info_dfs, total_makespans):

    print("total_makespans: ", total_makespans)

    df_all = pd.concat(job_info_dfs, ignore_index=True)
    df_all["duration"] = df_all["duration"].astype(float)
    job_mean_std_time = df_all.groupby("job")["duration"].agg(["mean", "std"]).reset_index()

    makespan_mean = np.mean(total_makespans)
    makespan_std = np.std(total_makespans)

    return job_mean_std_time, makespan_mean, makespan_std


def cal_slo_violation_ratio(mcperf_file, job_info_file, idx):

    p95_latency, actual_qps, timestamp_start, timestamp_end = load_mcperf_file(mcperf_file)
    job_info_df, total_makespan, memcache_cpu_core = load_job_file(job_info_file)

    # Calculate the job time period:
    job_start = job_info_df["start"].min().timestamp()
    job_end = job_info_df["end"].max().timestamp()
    timestamp_start = (datetime.fromtimestamp(timestamp_start) + timedelta(hours=2)).timestamp()
    timestamp_end = (datetime.fromtimestamp(timestamp_end) + timedelta(hours=2)).timestamp()

    # Find the common area with job batch and memcache
    start = max(job_start, timestamp_start)
    end = min(job_end, timestamp_end)

    rel_start = start - timestamp_start
    rel_end = end - timestamp_start
    time_axis = list(range(0, len(p95_latency) * 5, 5))

    valid_indices = [i for i, t in enumerate(time_axis) if rel_start <= t <= rel_end]
    violations = sum(1 for i in valid_indices if p95_latency[i] > 0.8)
    total_points = len(valid_indices)
    violation_ratio = violations / total_points if total_points > 0 else 0.0

    print(f"Exp {idx} SLO violation ratio: {violation_ratio:.2%} ({violations}/{total_points})")
    
    return violation_ratio


if __name__ == "__main__":
    
    result_path_4_3 = "../result/log/4-3/"
    result_path_4_4 = "../result/log/4-4/"
    mcperf_files = ["mcperf_1.txt", "mcperf_2.txt", "mcperf_3.txt"]
    job_files = ["jobs_1.txt", "jobs_2.txt", "jobs_3.txt"]
    memcache_cpu_core_files = ["memcache_cpu_core_run1.txt", "memcache_cpu_core_run2.txt", "memcache_cpu_core_run3.txt"]

    job_info_dfs = []
    total_makespans = []

    for idx in range(1, 4):
        mcperf_file = os.path.join(result_path_4_4, mcperf_files[idx-1])
        job_file = os.path.join(result_path_4_4, job_files[idx-1])
        memcache_cpu_core_file = os.path.join(result_path_4_4, memcache_cpu_core_files[idx-1])

        amplify_jobs_file(job_file, memcache_cpu_core_file)

        plot_type_a(mcperf_file, job_file, idx, "4_4")
        plot_type_b(mcperf_file, job_file, idx, "4_4")

        cal_slo_violation_ratio(mcperf_file, job_file, idx)

        job_info_df, total_makespan, memcache_cpu_core = load_job_file(job_file)
        
        job_info_dfs.append(job_info_df)
        total_makespans.append(total_makespan)
    
    job_mean_std_time, makespan_mean, makespan_std = cal_job_mean_std_time(job_info_dfs, total_makespans)
    print("job_mean_std_time:\n", job_mean_std_time)
    print("makespan_mean: ", makespan_mean)
    print("makespan_std: ", makespan_std)
