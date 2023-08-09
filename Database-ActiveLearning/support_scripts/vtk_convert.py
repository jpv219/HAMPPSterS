import os
from subprocess import Popen, PIPE
import glob
import shutil
import re

run_name = 'run_1'
proc =[]

ephemeral_path = os.path.join(os.environ['EPHEMERAL'],run_name)
convert_path = '/rds/general/user/jpv219/home/F_CONVERT'

os.chdir(ephemeral_path)

try:
    os.mkdir('RESULTS')
except:
    pass

ISO_file_list = glob.glob('ISO_*.vtk')
VAR_file_list = glob.glob('VAR_*_*.vtk')
pvd_0file = glob.glob(f'VAR_{run_name}_time=0.00000E+00.pvd')[0]
        

last_vtk = max(int(file.split("_")[-1].split(".")[0]) for file in VAR_file_list)

VAR_toconvert_list = glob.glob(f'VAR_*_{last_vtk}.vtk')

files_to_convert = ISO_file_list + VAR_toconvert_list

file_count = len(files_to_convert)

for file in files_to_convert:
    shutil.move(file,'RESULTS')

try:
    shutil.move(f'VAR_{run_name}.pvd','RESULTS')
    shutil.move(f'ISO_static_1_{run_name}.pvd','RESULTS')
    shutil.move(f'{run_name}.csv','RESULTS')
    shutil.move(f'{pvd_0file}', 'RESULTS')
    print('-' * 100)
    print('VAR, ISO and csv files moved to RESULTS')
except:
    pass

os.chdir('RESULTS')

try:
    os.mkdir('VTK_SAVE')
except:
    pass

convert_scripts = glob.glob(os.path.join(convert_path, '*'))

for file in convert_scripts:
    shutil.copy2(file, '.')

os.system(f'sed -i \"s/\'FILECOUNT\'/{file_count}/\" Multithread_pool.py')

proc = Popen(['qsub', 'job_convert.sh'], stdout=PIPE)

output = proc.communicate()[0].decode('utf-8').split()

jobid = int(re.search(r'\b\d+\b',output[0]).group())

print(jobid)

