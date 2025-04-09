import pandas as pd
import os


def get_color(value):
    if value <= 1.3:
        return "green"
    elif value <= 2:
        return "YellowOrange"
    else:
        return "red"


def cal_average_val(result_dir, num_repeat):

    repeat_metadata_csv = []
    for repeat_idx in range(1, num_repeat+1):
        repeat_metadata_csv.append(os.path.join(result_dir, f"repeat_{repeat_idx}", "metadata.csv"))
    
    df_list = [pd.read_csv(file) for file in repeat_metadata_csv]

    df_all = pd.concat(df_list)
    df_all.columns = df_all.columns.str.strip().str.lower()
    average_df = df_all.groupby(["program", "interference"])["value"].mean().reset_index()
    average_df["color"] = average_df["value"].apply(get_color)
    average_df.to_csv(os.path.join(result_dir, "metadata.csv"), index=False)


if __name__ == '__main__':

    result_dir = "../results"
    num_repeat = 3
    cal_average_val(result_dir, num_repeat)