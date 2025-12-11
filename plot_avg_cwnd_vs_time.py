import os
import numpy as np
import matplotlib.pyplot as plt
import glob

def load_cwnd_data(folder):
    # Find all cwnd files
    files = sorted(glob.glob(os.path.join(folder, 'tcp_flow_*_cwnd.csv')))
    flow_data = []
    for f in files:
        data = []
        with open(f, 'r') as fin:
            for line in fin:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    # time (ns), cwnd (bytes)
                    t = int(parts[1]) / 1e9  # convert ns to seconds
                    cwnd = int(parts[2])
                    data.append((t, cwnd))
        flow_data.append(data)
    return flow_data

def average_cwnd_over_flows(flow_data):
    # Find all unique time points
    all_times = sorted(set(t for flow in flow_data for t, _ in flow))
    avg_cwnd = []
    for t in all_times:
        cwnds = []
        for flow in flow_data:
            # Find cwnd for this time (if present)
            for t2, cwnd in flow:
                if t2 == t:
                    cwnds.append(cwnd)
                    break
        if cwnds:
            avg_cwnd.append((t, np.mean(cwnds)))
    return avg_cwnd

def main():
    jitter_dir = 'jitter_minimalized_first_100_run/data/jitter_minimized_630_to_631_with_TcpNewReno_at_10_Mbps'
    lmsr_dir = 'naive_lmsr_first_100_run/data/naive_lmsr_630_to_631_with_TcpNewReno_at_10_Mbps'

    print('Loading jitter minimized data...')
    jitter_flows = load_cwnd_data(jitter_dir)
    print('Loading naive LMSR data...')
    lmsr_flows = load_cwnd_data(lmsr_dir)

    print('Averaging...')
    jitter_avg = average_cwnd_over_flows(jitter_flows)
    lmsr_avg = average_cwnd_over_flows(lmsr_flows)

    # Plot
    plt.figure(figsize=(10,6))
    plt.plot([t for t, _ in jitter_avg], [c for _, c in jitter_avg], label='Jitter Minimized', color='blue')
    plt.plot([t for t, _ in lmsr_avg], [c for _, c in lmsr_avg], label='Naive LMSR', color='red')
    plt.xlabel('Time (s)')
    plt.ylabel('Average CWND (bytes)')
    plt.title('Average CWND vs Time (100 Flows)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('avg_cwnd_vs_time.png')
    plt.show()

if __name__ == '__main__':
    main()
