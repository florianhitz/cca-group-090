import re
import os
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime


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


def load_qps_p95_file(qps_p95_file):

    p95_latency = []
    actual_qps = []
    timestamp_start = None
    timestamp_end = None

    with open(qps_p95_file, "r") as f:
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


def load_job_info_file(job_info_file):

    job_info = {}
    total_makespan = 0

    with open(job_info_file) as f:
        for line in f:
            if "starts" in line:
                parts = line.strip().split()
                job_name = parts[0]
                start_time = parts[-1]
                if job_name not in job_info:
                    job_info[job_name] = {}
                job_info[job_name]["start"] = start_time
            elif "lasts" in line:
                parts = line.strip().split()
                job_name = parts[0]
                duration = parts[-2]
                if job_name not in job_info:
                    job_info[job_name] = {}
                job_info[job_name]["duration"] = duration
            elif "Total makespan" in line:
                parts = line.strip().split()
                total_makespan = float(parts[-2])
    
    job_info_df = pd.DataFrame.from_dict(job_info, orient="index")
    job_info_df.index.name = "job"
    job_info_df = job_info_df.reset_index()
    return job_info_df, total_makespan


def load_memcache_cpu_core_file(memcache_cpu_core_file):
    
    memcache_cpu_core = {}

    with open(memcache_cpu_core_file) as f:
        for line in f:
            if "At" in line:
                parts = line.strip().split()
                timestamp = float(parts[1].strip(','))
                cores = int(parts[-2])
                memcache_cpu_core[timestamp] = cores
    
    return memcache_cpu_core


def plot_type_a(qps_p95_file, job_info_file, exp_idx):

    p95_latency, actual_qps, timestamp_start, timestamp_end = load_qps_p95_file(qps_p95_file)
    job_info_df, _ = load_job_info_file(job_info_file)
    benchmark_start = datetime.fromtimestamp(timestamp_start)
    benchmark_start = benchmark_start.strftime('%Y-%m-%d %H:%M:%S')

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
        text=f"Experiment Start Time: {benchmark_start}",
        xref="paper", yref="paper",
        x=0, y=-0.2,
        showarrow=False,
        font=dict(size=12),
        align="left"
    )

    # Add job annotations
    for _, row in job_info_df.iterrows():
        rel_start = float(row["start"]) - timestamp_start
        job = row["job"]
        duration = float(row["duration"])

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
    fig.write_image(os.path.join(fig_dir, f"experiment_{exp_idx}_p95_latency_and_achieved_qps_30mins.png"), scale=3, engine="kaleido")
    fig.write_html(os.path.join(fig_dir, f"experiment_{exp_idx}_p95_latency_and_achieved_qps_30mins.html"))


def plot_type_b(qps_p95_file, job_info_file, memcache_cpu_core_file, exp_idx):

    p95_latency, actual_qps, timestamp_start, timestamp_end = load_qps_p95_file(qps_p95_file)
    job_info_df, _ = load_job_info_file(job_info_file)
    memcache_cpu_core = load_memcache_cpu_core_file(memcache_cpu_core_file)
    benchmark_start = datetime.fromtimestamp(timestamp_start)
    benchmark_start = benchmark_start.strftime('%Y-%m-%d %H:%M:%S')

    # Time axis based on QPS data (10-second intervals)
    time_axis = list(range(0, len(actual_qps) * 10, 10))

    memcache_core_timestamps = []
    core_num_list = []

    for memcache_core_timestamp, core_num in memcache_cpu_core.items():
        if memcache_core_timestamp > timestamp_end:
            break
        memcache_core_timestamps.append(memcache_core_timestamp-timestamp_start)
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
        text=f"Experiment Start Time: {benchmark_start}",
        xref="paper", yref="paper",
        x=0, y=-0.2,
        showarrow=False,
        font=dict(size=12),
        align="left"
    )

    # Add job annotations
    for _, row in job_info_df.iterrows():
        rel_start = float(row["start"]) - timestamp_start
        job = row["job"]
        duration = float(row["duration"])

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
            tickvals=[1, 2, 3, 4],
            range=[0.1, 4]
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
    fig.write_image(os.path.join(fig_dir, f"experiment_{exp_idx}_memcached_cpu_core_allocation_over_30mins.png"), scale=3, engine="kaleido")
    fig.write_html(os.path.join(fig_dir, f"experiment_{exp_idx}_memcached_cpu_core_allocation_over_30mins.html"))



def cal_job_mean_std_time(job_info_dfs, total_makespans):

    df_all = pd.concat(job_info_dfs, ignore_index=True)
    df_all["duration"] = df_all["duration"].astype(float)
    job_mean_std_time = df_all.groupby("job")["duration"].agg(["mean", "std"]).reset_index()

    makespan_mean = np.mean(total_makespans)
    makespan_std = np.std(total_makespans)

    return job_mean_std_time, makespan_mean, makespan_std


def cal_slo_violation_ratio(qps_p95_file, job_info_file, idx):

    p95_latency, actual_qps, timestamp_start, timestamp_end = load_qps_p95_file(qps_p95_file)
    job_info_df, _ = load_job_info_file(job_info_file)

    # Calculate the job time period:
    job_start = job_info_df["start"].astype(float).min()
    job_info_df["end"] = job_info_df["start"].astype(float) + job_info_df["duration"].astype(float)
    job_end = job_info_df["end"].max()

    # Find the common area with job batch and memcache
    start = max(job_start, timestamp_start)
    end = min(job_end, timestamp_end)

    rel_start = start - timestamp_start
    rel_end = end - timestamp_start
    time_axis = list(range(0, len(p95_latency) * 10, 10))

    valid_indices = [i for i, t in enumerate(time_axis) if rel_start <= t <= rel_end]
    violations = sum(1 for i in valid_indices if p95_latency[i] > 0.8)
    total_points = len(valid_indices)
    violation_ratio = violations / total_points if total_points > 0 else 0.0

    print(f"Exp {idx} SLO violation ratio: {violation_ratio:.2%} ({violations}/{total_points})")
    
    return violation_ratio


if __name__ == "__main__":
    
    result_path = "../result/log/4-3/"
    qps_p95_files = ["qps_p95_run1.txt", "qps_p95_run2.txt", "qps_p95_run3.txt"]
    job_info_files = ["job_info_run1.txt", "job_info_run2.txt", "job_info_run3.txt"]
    memcache_cpu_core_files = ["memcache_cpu_core_run1.txt", "memcache_cpu_core_run2.txt", "memcache_cpu_core_run3.txt"]
    
    job_info_dfs = []
    total_makespans = []

    for idx in range(1, 4):
        qps_p95_file = os.path.join(result_path, qps_p95_files[idx-1])
        job_info_file = os.path.join(result_path, job_info_files[idx-1])
        memcache_cpu_core_file = os.path.join(result_path, memcache_cpu_core_files[idx-1])

        plot_type_a(qps_p95_file, job_info_file, idx)
        plot_type_b(qps_p95_file, job_info_file, memcache_cpu_core_file, idx)
        cal_slo_violation_ratio(qps_p95_file, job_info_file, idx)

        job_info_df, total_makespan = load_job_info_file(job_info_file)
        
        job_info_dfs.append(job_info_df)
        total_makespans.append(total_makespan)
    
    job_mean_std_time, makespan_mean, makespan_std = cal_job_mean_std_time(job_info_dfs, total_makespans)
    print("job_mean_std_time:\n", job_mean_std_time)
    print("makespan_mean: ", makespan_mean)
    print("makespan_std: ", makespan_std)
