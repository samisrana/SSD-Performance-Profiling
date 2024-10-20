import os
import json
import pandas as pd
import matplotlib.pyplot as plt

# Directory where FIO JSON result files are stored
fio_results_dir = "fio_results"

# Initialize lists to hold data
data = []

# Map random read/write modes to normal read/write for JSON extraction
rw_map = {
    'randread': 'read',
    'randwrite': 'write',
    'read': 'read',
    'write': 'write',
    'rw': 'mixed',       # New key for mixed mode
    'randrw': 'mixed'    # New key for random mixed mode
}

# Iterate through the JSON files in the results directory
for filename in os.listdir(fio_results_dir):
    if filename.endswith(".json"):
        filepath = os.path.join(fio_results_dir, filename)
        
        # Try to extract block size, rw_mode, and iodepth from the filename
        try:
            parts = filename.split('_')
            rw = parts[1]  # read/write mode
            bs = parts[2]  # block size
            iodepth = parts[4].replace(".json", "")  # iodepth
        except IndexError:
            print(f"Error parsing filename: {filename}")
            continue
        
        # Open and parse the JSON file
        with open(filepath, 'r') as f:
            fio_data = json.load(f)
            
            # Extract relevant information from the JSON
            job = fio_data['jobs'][0]
            
            # Determine the actual key to use based on read/write or mixed mode
            rw_key = rw_map.get(rw, None)
            if rw_key is None:
                print(f"Unsupported rw_mode in {filename}")
                continue
            
            # Handle latency and throughput for mixed modes
            if rw_key == 'mixed':
                # Mixed mode (rw or randrw), so we need to combine read and write
                lat_avg_read = job['read']['lat_ns'].get('mean', 0) / 1000 if 'lat_ns' in job['read'] else 0
                lat_avg_write = job['write']['lat_ns'].get('mean', 0) / 1000 if 'lat_ns' in job['write'] else 0
                lat_avg = (lat_avg_read + lat_avg_write) / 2 if lat_avg_read > 0 or lat_avg_write > 0 else None

                throughput_read = job['read']['iops'] if int(bs[:-1]) <= 64 else job['read']['bw'] / 1024
                throughput_write = job['write']['iops'] if int(bs[:-1]) <= 64 else job['write']['bw'] / 1024
                throughput = (throughput_read + throughput_write) / 2
            else:
                # Non-mixed mode (just read, write, randread, randwrite)
                lat_avg = job[rw_key]['lat_ns'].get('mean') / 1000 if 'lat_ns' in job[rw_key] else None
                throughput = job[rw_key]['iops'] if int(bs[:-1]) <= 64 else job[rw_key]['bw'] / 1024
            
            # Only append data if we have either latency or throughput
            if lat_avg is not None or throughput is not None:
                data.append({
                    'block_size': bs,
                    'rw_mode': rw,
                    'iodepth': int(iodepth),
                    'latency_us': lat_avg,
                    'throughput': throughput
                })
            else:
                print(f"Skipping {filename} due to missing data.")

# Convert list to a DataFrame
df = pd.DataFrame(data)

# Check if we have valid data
if df.empty:
    print("No valid data to plot.")
    exit()

# Function to plot latency and throughput with optional log scale for latency
def plot_performance(metric, title, ylabel, log_scale=False):
    fig, ax = plt.subplots(figsize=(10, 6))

    # Filter out rows with missing values for the given metric
    df_filtered = df.dropna(subset=[metric])

    if df_filtered.empty:
        print(f"No data available for {metric}.")
        return

    # Convert block_size to numeric for proper sorting
    df_filtered['block_size_numeric'] = df_filtered['block_size'].str.replace('k', '000').astype(int)

    for (rw_mode, iodepth), group_data in df_filtered.groupby(['rw_mode', 'iodepth']):
        # Sort by numeric block sizes
        group_data = group_data.sort_values('block_size_numeric')
        ax.plot(group_data['block_size_numeric'], group_data[metric], label=f'{rw_mode}, iodepth={iodepth}')
    
    ax.set_title(title)
    ax.set_xlabel('Block Size (Bytes)')
    ax.set_ylabel(ylabel)
    if log_scale:
        ax.set_yscale('log')  # Apply log scale to Y-axis for better visualization of small values
    ax.legend()
    plt.xticks([4000, 16000, 32000, 128000], ['4k', '16k', '32k', '128k'], rotation=45)  # Adjust x-ticks manually for clarity
    plt.tight_layout()
    plt.show()

# Re-run the plots
if 'latency_us' in df.columns:
    plot_performance('latency_us', 'SSD Latency under Different Conditions', 'Latency (µs)', log_scale=True)

if 'throughput' in df.columns:
    plot_performance('throughput', 'SSD Throughput under Different Conditions', 'Throughput (IOPS or MB/s)')
