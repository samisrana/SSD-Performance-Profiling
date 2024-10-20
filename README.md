# SSD-Performance-Profiling
This project aims to provide hands-on experience in profiling the performance of modern SSDs, focusing on latency and throughput under different conditions. We use the Flexible IO Tester (FIO), a widely used tool for benchmarking storage devices, to evaluate the performance of your SSD with different access patterns, data sizes, read/write ratios, and queue depths.


## Creating a new partition in disk via Windows Command Prompt

Follow these steps to create a new partition on your disk using the Command Prompt as an administrator.

### Step 1: Open Command Prompt as Administrator
1. Press `Win + X` and select **Command Prompt (Admin)**.

### Step 2: Start DiskPart
In the Command Prompt, type:
```cmd
diskpart
```

### Step 3: List Disks
To view all disks available on your system, run:
```cmd
list disk
```

### Step 4: Select the Disk
Choose the disk you want to work with. For example, select disk 0:
```cmd
select disk 0
```

### Step 5: List Volumes
Next, list all volumes on the selected disk:
```cmd
list volume
```

### Step 6: Select the Volume to Shrink
Pick the volume you wish to shrink. For example, to select volume 0:
```cmd
select volume 0
```

### Step 7: Shrink the Volume by 1024 MB (can be bigger if you want to make a bigger partition)
Shrink the selected volume by 1024 MB using the command:
```cmd
shrink desired=1024
```

### Step 8: Create a New Partition
After shrinking the volume, create a new primary partition of 1024 MB:
```cmd
create partition primary size=1024
```

### Step 9: Format the New Partition
Format the newly created partition with the NTFS file system:
```cmd
format fs=ntfs quick
```

### Step 10: Assign a Drive Letter
Assign a drive letter to the new partition. For example, assign it the letter `E`:
```cmd
assign letter=E
```

### Step 11: Exit DiskPart
Once all operations are complete, exit diskpart:
```cmd
exit
```
