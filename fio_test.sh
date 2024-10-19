#!/bin/bash

# Create an output directory for FIO results
mkdir -p fio_results

# Array of block sizes to test (e.g., 4KB, 16KB, 32KB, 128KB)
block_sizes=("4k" "16k" "32k" "128k")

# Array of I/O queue depths to test (e.g., 1, 16, 64, 256, 1024)
io_depths=(1 16 64 256 1024)

# Array of read/write ratios (read, write, and mixed ratios)
rw_modes=("read" "write" "randread" "randwrite" "rw" "randrw")

# Set the file size to test on (adjust accordingly, use a dedicated test partition)
test_file="/mnt/test_partition/testfile"

# Test size
test_size="10G"

# Loop through different block sizes
for bs in "${block_sizes[@]}"; do
  # Loop through different I/O queue depths
  for iodepth in "${io_depths[@]}"; do
    # Loop through different read/write modes
    for rw in "${rw_modes[@]}"; do

      # Set output file name
      output_file="fio_results/fio_${rw}_${bs}_iodepth_${iodepth}.json"

      # Run FIO with the specified parameters
      fio --name=benchmark_test --filename=${test_file} --size=${test_size} \
          --rw=${rw} --bs=${bs} --iodepth=${iodepth} --ioengine=libaio --direct=1 \
          --numjobs=1 --runtime=60 --time_based --group_reporting \
          --output-format=json --output=${output_file}

      echo "Finished ${rw} with block size ${bs} and iodepth ${iodepth}, results saved in ${output_file}"
      
    done
  done
done

