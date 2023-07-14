import os

run_ID = 54
run_path = '/rds/general/user/jpv219/home/BLUE-12.5.1/project/TRIALS'
base_case_dir = '/rds/general/user/jpv219/home/BLUE-12.5.1/project/TRIALS/home'
pipe_radius = 15
smx_pos = 19
bar_width = 0.1
bar_thickness = 0.01
bar_angle = 60
n_bars= 8
d_per_level = 3
n_levels = 2
d_radius = "[0.2,0.5]"
flowrate = 100

run_name = "run_"+str(run_ID)
path = os.path.join(run_path, run_name)
os.mkdir(path)

os.system(f'cp -r {base_case_dir}/* {path}')
os.system(f'mv {path}/base_SMX.f90 {path}/{run_name}_SMX.f90')


## Assign values to placeholders
os.system(f'sed -i \"s/\'pipe_radius\'/{pipe_radius}/\" {path}/{run_name}_SMX.f90')
os.system(f'sed -i \"s/\'smx_pos\'/{smx_pos}/\" {path}/{run_name}_SMX.f90')
os.system(f'sed -i \"s/\'bar_width\'/{bar_width}/g\" {path}/{run_name}_SMX.f90')
os.system(f'sed -i \"s/\'bar_thickness\'/{bar_thickness}/\" {path}/{run_name}_SMX.f90')
os.system(f'sed -i \"s/\'bar_angle\'/{bar_angle}/\" {path}/{run_name}_SMX.f90')
os.system(f'sed -i \"s/\'n_bars\'/{n_bars}/\" {path}/{run_name}_SMX.f90')


os.system(f'sed -i \"s/\'d_per_level\'/{d_per_level}/\" {path}/{run_name}_SMX.f90')
os.system(f'sed -i \"s/\'n_levels\'/{n_levels}/\" {path}/{run_name}_SMX.f90')
os.system(f'sed -i \"s/\'d_radius\'/{d_radius}/\" {path}/{run_name}_SMX.f90')


os.system(f'sed -i \"s/\'flowrate\'/{flowrate}/\" {path}/{run_name}_SMX.f90')

#modify the Makefile

os.system(f'sed -i s/file/{run_name}_SMX/g {path}/Makefile')

#compile the f90 into an executable

os.chdir(path)
os.system('make')
os.system(f'mv {run_name}_SMX.x {run_name}.x')
os.system('make cleanall')
os.chdir('..')
