import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Directory where FIO JSON result files are stored
fio_results_dir = "fio_results"

# Directory to store generated images
image_dir = "images"

# Create the images directory if it doesn't exist
os.makedirs(image_dir, exist_ok=True)

# Initialize lists to hold data
data = []

# Map random read/write modes to normal read/write for JSON extraction
rw_map = {
    'randread': 'read',
    'randwrite': 'write',
    'read': 'read',
    'write': 'write',
    'rw': 'mixed',
    'randrw': 'mixed'
}

def calculate_throughput(job, rw_key, bs):
    """Calculate throughput in MB/s regardless of block size"""
    if rw_key == 'mixed':
        # For mixed workloads, sum the bandwidth of both read and write
        read_bw = job['read']['bw'] / 1024  # Convert to MB/s
        write_bw = job['write']['bw'] / 1024  # Convert to MB/s
        return read_bw + write_bw
    else:
        # For single workloads, just get the bandwidth
        return job[rw_key]['bw'] / 1024  # Convert to MB/s

# Iterate through the JSON files in the results directory
for filename in os.listdir(fio_results_dir):
    if filename.endswith(".json"):
        filepath = os.path.join(fio_results_dir, filename)
        
        # Extract block size, rw_mode, and iodepth from the filename
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
            
            # Calculate throughput in MB/s
            throughput = calculate_throughput(job, rw_key, bs)
            
            # Calculate latency
            if rw_key == 'mixed':
                lat_avg_read = job['read']['lat_ns'].get('mean', 0) / 1000 if 'lat_ns' in job['read'] else 0
                lat_avg_write = job['write']['lat_ns'].get('mean', 0) / 1000 if 'lat_ns' in job['write'] else 0
                lat_avg = (lat_avg_read + lat_avg_write) / 2 if lat_avg_read > 0 or lat_avg_write > 0 else None
            else:
                lat_avg = job[rw_key]['lat_ns'].get('mean') / 1000 if 'lat_ns' in job[rw_key] else None
            
            # Append the data
            data.append({
                'block_size': bs,
                'rw_mode': rw,
                'iodepth': int(iodepth),
                'latency_us': lat_avg,
                'throughput': throughput
            })

# Convert list to a DataFrame
df = pd.DataFrame(data)

def plot_performance(metric, title, ylabel, log_scale=False):
    plt.figure(figsize=(12, 8))

    # Filter out rows with missing values for the given metric
    df_filtered = df.dropna(subset=[metric])

    if df_filtered.empty:
        print(f"No data available for {metric}.")
        return

    # Convert block_size to numeric for proper sorting
    df_filtered['block_size_numeric'] = df_filtered['block_size'].str.replace('k', '').astype(int)
    
    # Create distinct color and line style combinations
    colors = plt.cm.tab20(np.linspace(0, 1, len(df_filtered['rw_mode'].unique())))
    line_styles = ['-', '--', ':', '-.']
    
    for idx, ((rw_mode, iodepth), group_data) in enumerate(df_filtered.groupby(['rw_mode', 'iodepth'])):
        color = colors[idx % len(colors)]
        style = line_styles[(idx // len(colors)) % len(line_styles)]
        
        # Sort by numeric block sizes
        group_data = group_data.sort_values('block_size_numeric')
        plt.plot(group_data['block_size'], group_data[metric],
                 label=f'{rw_mode}, iodepth={iodepth}',
                 color=color, linestyle=style, marker='o')

    plt.title(title, pad=20, fontsize=14)
    plt.xlabel('Block Size', fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    if log_scale:
        plt.yscale('log')

    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0., fontsize=8)
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Create a valid filename
    filename = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
    filename = filename.replace(' ', '_') + '.png'
    
    plt.savefig(os.path.join(image_dir, filename), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved plot: {filename}")

def plot_parameter_effect(df, x_param, y_param, fixed_params, title):
    # Get unique values for each fixed parameter
    unique_values = {param: sorted(df[param].unique()) for param in fixed_params}
    
    # Set up a color palette
    color_palette = sns.color_palette("husl", n_colors=len(unique_values[fixed_params[1]]))
    
    # Create a separate plot for each value of the first fixed parameter
    for value in unique_values[fixed_params[0]]:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Filter data for this plot
        plot_data = df[df[fixed_params[0]] == value]
        
        # Prepare data for grouped bar plot
        plot_data_pivoted = plot_data.pivot(index=x_param, columns=fixed_params[1], values=y_param)
        
        # Create the grouped bar plot
        plot_data_pivoted.plot(kind='bar', ax=ax, width=0.8, color=color_palette)
        
        ax.set_xlabel(x_param)
        ax.set_ylabel(y_param)
        ax.set_title(f"{title}\n{fixed_params[0]} = {value}")
        ax.legend(title=fixed_params[1], bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, which="both", ls="-", alpha=0.2)
        
        if y_param == 'latency_us':
            ax.set_yscale('log')
        
        plt.tight_layout()
        
        # Create a valid filename
        filename = f"{title.replace(' ', '_')}_{fixed_params[0]}_{value}.png"
        filename = "".join(c for c in filename if c.isalnum() or c in ('_', '.')).rstrip()
        
        plt.savefig(os.path.join(image_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved plot: {filename}")

def plot_iodepth_effect(df, y_param, fixed_params, title):
    unique_values = {param: sorted(df[param].unique()) for param in fixed_params}
    
    for value in unique_values[fixed_params[0]]:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        plot_data = df[df[fixed_params[0]] == value]
        
        for second_value in unique_values[fixed_params[1]]:
            data = plot_data[plot_data[fixed_params[1]] == second_value]
            ax.semilogx(data['iodepth'], data[y_param], marker='o', linestyle='-', 
                        label=f'{fixed_params[1]}={second_value}')
        
        ax.set_xlabel('I/O Depth')
        ax.set_ylabel(y_param)
        ax.set_title(f"{title}\n{fixed_params[0]} = {value}")
        ax.legend(title=fixed_params[1], bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, which="both", ls="-", alpha=0.2)
        
        if y_param == 'latency_us':
            ax.set_yscale('log')
        
        plt.tight_layout()
        
        filename = f"{title.replace(' ', '_')}_{fixed_params[0]}_{value}.png"
        filename = "".join(c for c in filename if c.isalnum() or c in ('_', '.')).rstrip()
        
        plt.savefig(os.path.join(image_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved plot: {filename}")

def plot_consolidated_effects(df, metric):
    # Create a 2x2 grid of subplots
    fig, axes = plt.subplots(2, 2, figsize=(20, 20))
    fig.suptitle(f"Effects of Parameters on {metric.capitalize()}", fontsize=16)

    # Heatmap of rw_mode vs block_size
    pivot_data = df.pivot_table(values=metric, index='rw_mode', columns='block_size', aggfunc='mean')
    sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='YlOrRd', ax=axes[0, 0])
    axes[0, 0].set_title(f"{metric.capitalize()} - RW Mode vs Block Size")

    # Heatmap of rw_mode vs iodepth
    pivot_data = df.pivot_table(values=metric, index='rw_mode', columns='iodepth', aggfunc='mean')
    sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='YlOrRd', ax=axes[0, 1])
    axes[0, 1].set_title(f"{metric.capitalize()} - RW Mode vs IO Depth")

    # Faceted plot for block_size effect across rw_modes
    sns.boxplot(x='block_size', y=metric, hue='rw_mode', data=df, ax=axes[1, 0])
    axes[1, 0].set_title(f"Effect of Block Size on {metric.capitalize()} by RW Mode")
    axes[1, 0].set_xticklabels(axes[1, 0].get_xticklabels(), rotation=45)
    
    # Faceted plot for iodepth effect across rw_modes
    sns.boxplot(x='iodepth', y=metric, hue='rw_mode', data=df, ax=axes[1, 1])
    axes[1, 1].set_title(f"Effect of IO Depth on {metric.capitalize()} by RW Mode")
    axes[1, 1].set_xticklabels(axes[1, 1].get_xticklabels(), rotation=45)
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(os.path.join(image_dir, f"Consolidated_{metric}_effects.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved consolidated plot for {metric}")

# Generate plots
plot_parameter_effect(df[df['rw_mode'].isin(['read', 'write', 'rw', 'randrw'])], 
                      'rw_mode', 'throughput', ['block_size', 'iodepth'], 
                      "Effect of Read/Write Ratio on Bandwidth")

plot_consolidated_effects(df, 'throughput')
plot_consolidated_effects(df, 'latency_us')

if 'latency_us' in df.columns:
    plot_performance('latency_us', 'SSD Latency under Different Conditions', 'Latency (µs)', log_scale=True)

if 'throughput' in df.columns:
    plot_performance('throughput', 'SSD I/O Performance: Throughput vs Block Size', 'Throughput (MB/s)')
