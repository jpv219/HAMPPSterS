import os
from subprocess import Popen, PIPE
import glob
import shutil

path = '/rds/general/user/jpv219/home/BLUE-12.5.1/project/TRIALS'
run_name = 'smx_ml'
proc =[]

ephemeral_path = os.path.join(os.environ['EPHEMERAL'],run_name)
os.chdir(ephemeral_path)
convert_path = '/rds/general/user/jpv219/home/F_CONVERT'
try:
    os.mkdir('VTK_SAVE')
except:
    pass
convert_files = glob.glob(os.path.join(convert_path, '*'))

for file in convert_files:
    shutil.copy2(file, '.')

ISO_file_list = glob.glob('ISO_*.vtk')
VAR_file_list = glob.glob('VAR_*_*.vtk')

last_vtk = max(int(file.split("_")[-1].split(".")[0]) for file in VAR_file_list)

print(last_vtk)

VAR_toconvert_list = glob.glob(f'VAR_*_{last_vtk}.vtk')

file_count = len(ISO_file_list) + len(VAR_toconvert_list)

print(file_count)

os.system(f'sed -i \"s/\'FILECOUNT\'/{file_count}/\" Multithread_pool.py')

proc.append(Popen(['qsub', 'job_convert.sh'], stdout=PIPE))

jobid = int(str(proc[-1].stdout.read(), 'utf-8').split()[2])

print(jobid)

os.chdir(path)
os.chdir('..')
print(os.getcwd())