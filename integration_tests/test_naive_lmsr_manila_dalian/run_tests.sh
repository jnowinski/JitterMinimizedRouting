
# Manila to Dalian over Kuiper-630 first shell
python step_1_generate_satellite_networks_state.py || exit 1
python step_2_generate_runs.py || exit 1
python step_3_run.py || exit 1
python step_4_generate_plots.py || exit 1
