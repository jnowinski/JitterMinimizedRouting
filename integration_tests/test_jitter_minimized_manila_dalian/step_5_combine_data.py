import glob
import exputil
import numpy as np
import pandas as pd
from pandas.core.interchange.dataframe_protocol import DataFrame

try:
    from .run_list import *
except (ImportError, SystemError):
    from run_list import *

local_shell = exputil.LocalShell()

for run in get_tcp_run_list():
    if not local_shell.path_exists("temp/data/" + run["name"]):
        print("Making data directory")
        local_shell.make_full_dir("temp/data/" + run["name"])
    elif local_shell.file_exists("temp/data/" + run["name"] + "/combined_rtts.csv"):
        local_shell.remove("temp/data/" + run["name"] + "/combined_rtts.csv")

    print("Combining rtt csvs at temp/data/" + run["name"] + "/combined_rtts.csv")
    rtt_csvs = glob.glob("temp/data/" + run["name"] + "/*_rtt.csv")
    df = pd.concat((pd.read_csv(csv, header=None, names=['flow','time (s)','rtt (s)']) for csv in rtt_csvs), axis=0, ignore_index=True)
    df['time (s)'] = df['time (s)'] / 1e9
    df['rtt (s)'] = df['rtt (s)'] / 1e9
    second_averages = []
    for second in range(100):
        second_df = df.loc[(second <= df['time (s)']) & (df['time (s)'] < second + 1)]
        second_averages.append(second_df['rtt (s)'].var())
    pd.DataFrame(range(100), second_averages).to_csv("temp/data/" + run["name"] + "/combined_rtts.csv")
