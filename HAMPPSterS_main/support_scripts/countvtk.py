import glob
import time
import psutil

# Method 1: Original approach
start_time = time.time()

VAR_file_list = glob.glob('VAR_*_*.vtk')
last_vtk = max(int(file.split("_")[-1].split(".")[0]) for file in VAR_file_list)

end_time = time.time()
elapsed_time = end_time - start_time
memory_usage = psutil.Process().memory_info().rss / 1024 / 1024

print("Method 1:")
print("Elapsed Time:", elapsed_time, "seconds")
print("Memory Usage:", memory_usage, "MB")
print("Last VTK:", last_vtk)
print()

# Method 2: Optimized approach
start_time = time.time()

max_vtk = -float('inf')

for file in glob.iglob('VAR_*_*.vtr'):
    vtk_value = int(file.split("_")[-1].split(".")[0])
    if vtk_value > max_vtk:
        max_vtk = vtk_value

end_time = time.time()
elapsed_time = end_time - start_time
memory_usage = psutil.Process().memory_info().rss / 1024 / 1024

print("Method 2:")
print("Elapsed Time:", elapsed_time, "seconds")
print("Memory Usage:", memory_usage, "MB")
print("Max VTK:", max_vtk)
