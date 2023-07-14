import os
import math


run_ID = 54
run_path = '/rds/general/user/jpv219/home/BLUE-12.5.1/project/TRIALS'
base_case_dir = '/rds/general/user/jpv219/home/BLUE-12.5.1/project/TRIALS/home'
pipe_radius = 0.015
max_diameter = 0.06


## Create run_ID directory
run_name = "run_"+str(run_ID)
path = os.path.join(run_path, run_name)

## rename job with current run
os.system(f'mv {path}/job_base.sh {path}/{run_name}.sh')

## Assign values to placeholders
os.system(f'sed -i \"s/RUN_NAME/{run_name}/g\" {path}/{run_name}.sh')

box_2 = math.ceil(4*pipe_radius*1000)/1000
box_4 = math.ceil(2*pipe_radius*1000)/1000
box_6 = math.ceil(2*pipe_radius*1000)/1000

os.system(f'sed -i \"s/\'box2\'/{box_2}/\" {path}/{run_name}.sh')
os.system(f'sed -i \"s/\'box4\'/{box_4}/\" {path}/{run_name}.sh')
os.system(f'sed -i \"s/\'box6\'/{box_6}/\" {path}/{run_name}.sh')

d_pipe = 2*pipe_radius
min_res = 16000
## first cut for 64 cells per subdomain considering the max nodes can only be 10
## x-subdomain is 2 times the pipe's diameter
first_d_cut = (64*10/(2*min_res))/max_diameter
## taking only 6 and 128 for the x configuration
second_d_cut = ((6*64)/min_res)/max_diameter 

if d_pipe < first_d_cut*max_diameter:
    cpus = min_res*(2*d_pipe)/64
    xsub = math.ceil(cpus / 2) * 2
    ysub = zsub = int(xsub/2)
    mem = 200
    cell1 = cell2 = cell3 = 64
    ncpus = int(xsub*ysub*zsub)
    n_nodes = 1
elif d_pipe > second_d_cut*max_diameter:
    cpus = min_res*(2*d_pipe)/128
    if cpus <= 10:
        xsub = math.ceil(cpus / 2) * 2
        ysub = zsub = xsub/2
        mem = 920
        cell1 = cell2 = cell3 = 128
        ncpus = int(xsub*ysub*zsub)
        n_nodes = 1
    elif cpus >10 and cpus <= 12:
        xsub = 12
        ysub = zsub = int(xsub/2)
        cell1 = cell2 = cell3 = 128
        ncpus = int(xsub*ysub*zsub)
        mem = 200
        n_nodes = 4
    elif cpus >12 and cpus <= 14:
        xsub = 14
        ysub = zsub = int(xsub/2)
        cell1 = cell2 = cell3 = 128
        ncpus = int(xsub*ysub*zsub)
        mem = 200
        n_nodes = 6
    elif cpus > 14 and cpus <=16:
        xsub = 16
        ysub = zsub = int(xsub/2)
        cell1 = cell2 = cell3 = 128
        ncpus = int(xsub*ysub*zsub)
        mem = 200
        n_nodes = 8

else:
    xsub = ysub = zsub = 6
    mem = 800
    ncpus = int(xsub*ysub*zsub)
    n_nodes=1
    cell1= 128
    cell2 = cell3 = 64

os.system(f'sed -i \"s/\'x_subd\'/{xsub}/\" {path}/{run_name}.sh')
os.system(f'sed -i \"s/\'y_subd\'/{ysub}/\" {path}/{run_name}.sh')
os.system(f'sed -i \"s/\'z_subd\'/{zsub}/\" {path}/{run_name}.sh')

os.system(f'sed -i \"s/\'n_cpus\'/{ncpus}/\" {path}/{run_name}.sh')
os.system(f'sed -i \"s/\'n_nodes\'/{n_nodes}/\" {path}/{run_name}.sh')
os.system(f'sed -i \"s/\'mem\'/{mem}/\" {path}/{run_name}.sh')
os.system(f'sed -i \"s/\'cell1\'/{cell1}/\" {path}/{run_name}.sh')
os.system(f'sed -i \"s/\'cell2\'/{cell2}/\" {path}/{run_name}.sh')
os.system(f'sed -i \"s/\'cell3\'/{cell3}/\" {path}/{run_name}.sh')
