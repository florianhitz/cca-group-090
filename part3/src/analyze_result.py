import os
import pandas as pd
import plotly.express as px
from datetime import datetime
from collections import defaultdict
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


def memcache_file_to_df(memcache_file):

    data = []

    with open(memcache_file, "r") as f:
        for line in f:
            if line.startswith("read"):
                parts = line.split()
                p95 = float(parts[12])
                ts_start = datetime.utcfromtimestamp(int(parts[-2])/1000)
                ts_end = datetime.utcfromtimestamp(int(parts[-1])/1000)
                data.append({"p95": p95, "ts_start": ts_start, "ts_end": ts_end})

    df = pd.DataFrame(data)

    return df


def plot_bar_p95_latency_over_time(df, jobs_times, exp_idx):

    job_label_y = {
        "blackscholes": 0.1,
        "canneal": 0.15,
        "dedup": 0.2,
        "ferret": 0.25,
        "freqmine": 0.3,
        "radix": 0.35,
        "vips": 0.4
    }

    job_colors = {
        "blackscholes": "#CCA000",
        "canneal": "#CCCCAA",
        "dedup": "#CCACCA",
        "ferret": "#AACCCA",
        "freqmine": "#0CCA00",
        "radix": "#00CCA0",
        "vips": "#CC0A00"
    }

    start_ref = min(job["start_time"] for job in jobs_times)
    df = df[df["ts_start"] >= start_ref].reset_index(drop=True)

    # How the following start time different from the first one
    df["start_offset_sec"] = (df["ts_start"] - start_ref).dt.total_seconds()
    # Define the width of each bar
    df["duration"] = (df["ts_end"] - df["ts_start"]).dt.total_seconds()
    df["p95_ms"] = df["p95"]/1000
    
    # Plot with plotly
    fig = px.bar(
        df,
        x = "start_offset_sec",
        y = "p95_ms",
        custom_data=["ts_start", "ts_end", "duration"],
        labels = {
            "start_offset_sec": "Time since first container start (s)",
            "p95_ms": "p95 Latency (ms)"
        },
        title = f"Memcached p95 Latency Over Time (Experiment {exp_idx})",
    )

    # Add bar width and hoverover info
    fig.update_traces(
        width = df["duration"],
        marker_color = "LightSkyBlue",
        hovertemplate = 
            "ts_start: %{customdata[0]|%Y-%m-%d %H:%M:%S}<br>" \
            "ts_end: %{customdata[1]|%Y-%m-%d %H:%M:%S}<br>" \
            "duration: %{width} s<br>" \
            "p95_ms: %{y} ms"
    )

    for job in jobs_times:
        job_name = job["job_name"].split("-")[1]
        x_start = (job["start_time"] - start_ref).total_seconds()
        x_end = (job["completion_time"] - start_ref).total_seconds()
        y_pos = job_label_y.get(job_name, df["p95_ms"].max() * 1.05)

        # For start of job batch
        fig.add_shape(
            type="line",
            x0=x_start,
            x1=x_start,
            y0=0,
            y1=y_pos,
            line=dict(color=job_colors.get(job_name, "rgba(255, 255, 255, 1)"), width=2.5, dash="dot"),
            layer="above"
        )

        fig.add_annotation(
            x=x_start,
            y=y_pos,
            text=f"<b>{job_name}</b><br>{x_start:.1f}",
            showarrow=False,
            font=dict(size=8, color="black"),
            bgcolor=job_colors.get(job_name, "rgba(255, 255, 255, 1)")
        )

        # For end of job batch
        fig.add_shape(
            type="line",
            x0=x_end,
            x1=x_end,
            y0=0,
            y1=y_pos,
            line=dict(color=job_colors.get(job_name, "rgba(255, 255, 255, 1)"), width=2.5, dash="dot"),
            layer="above"
        )

        fig.add_annotation(
            x=x_end,
            y=y_pos,
            text=f"<b>{job_name}</b><br>{x_end:.1f}",
            showarrow=False,
            font=dict(size=8, color="black"),
            bgcolor=job_colors.get(job_name, "rgba(255, 255, 255, 1)")
        )

        # Horizontal line connecting start and end
        fig.add_shape(
            type="line",
            x0=x_start,
            y0=y_pos,
            x1=x_end,
            y1=y_pos,
            line=dict(color=job_colors.get(job_name, "rgba(255, 255, 255, 1)"), width=2.5, dash="dot"),
            layer="above"
        )

    fig.update_layout(
        bargap=0.1,
        width = 1000,
        height = 500,
        xaxis=dict(
            title="Time Since the First Job Starts (s)", 
            tickformat=".1f"
        ),
        yaxis=dict(title="p95 Latency (ms)", range=[0, df["p95_ms"].max() * 1.5])
    )

    # fig.show()
    fig_dir = "../result/fig/"
    os.makedirs(fig_dir, exist_ok=True)

    fig.write_image(os.path.join(fig_dir, f"experiment_{exp_idx}_p95_latency_plot.png"), engine="kaleido")
    fig.write_html(os.path.join(fig_dir, f"experiment_{exp_idx}_p95_latency_plot.html"))


if __name__ == "__main__":

    result_dir = "../result"
    batch_result_dfs = []

    for i in range(0, experiment_iterations):

        memcache_file = os.path.join(result_dir, f"memcache_{i+1}.csv")
        df_memcache = memcache_file_to_df(memcache_file)

        batch_result_file = os.path.join(result_dir, f"batch_result_{i+1}.json")
        jobs_times, total_time = parse_batch_timings(batch_result_file)
        print("job_times: ", jobs_times)
        df = batch_result_to_df(jobs_times, total_time)
        batch_result_dfs.append(df)

        print(f"\n===================== Memcache Result from Experiment {i+1} =====================")
        print(df_memcache)

        # Visualize the bar plot of p95 latency over time
        plot_bar_p95_latency_over_time(df_memcache, jobs_times, i+1)

    # Calculate the mean and std times for 7 jobs and the total time
    job_time_mean_std = cal_job_time_mean_std(batch_result_dfs)
    print(job_time_mean_std)