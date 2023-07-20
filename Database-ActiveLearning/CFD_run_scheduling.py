### SMX_Automation_simulation_run, tailored for BLUE
### Author: Juan Pablo Valdes,
### First commit: July, 2023
### Department of Chemical Engineering, Imperial College London

import numpy as np
import os
from subprocess import Popen, PIPE
from _thread import start_new_thread
from queue import Queue
from time import sleep
import pandas as pd
import shutil
import glob
import csv
import math
import datetime
import subprocess
import re

class SimScheduling:

    ### Init function
     
    def __init__(self) -> None:
        pass

    ### assigning input parametric values as attributes of the SimScheduling class and submitting jobs

    def run(self,pset_dict):
        self.pset_dict = pset_dict
        self.run_path = pset_dict['run_path']
        self.base_path = pset_dict['base_path']
        self.case_type = pset_dict['case']
        self.run_ID = pset_dict['_pset_ID']

        self.bar_width = pset_dict['bar_width']
        self.bar_thickness = pset_dict['bar_thickness']
        self.bar_angle = pset_dict['bar_angle']
        self.pipe_radius = pset_dict['pipe_radius']
        self.max_diameter = pset_dict['max_diameter']
        self.n_bars = pset_dict['n_bars']
        self.flowrate = pset_dict['flowrate']
        self.d_per_level = pset_dict['d_per_level']
        self.n_levels = pset_dict['n_levels']
        self.d_radius = pset_dict['d_radius']
        self.smx_pos = pset_dict['smx_pos']

        self.base_case_dir = os.path.join(self.base_path, self.case_type)
        
        self.init_wait_time = np.random.RandomState().randint(200,400)
        sleep(self.init_wait_time)  #each process waits a random amount of time after being created to stagger jobs and avoid launching thousands together

        self.submit_job()

        return {}
    
    ### creating f90 instance and executable

    def makef90(self):

        ## Create run_ID directory
        self.run_name = "run_"+str(self.run_ID)
        self.path = os.path.join(self.run_path, self.run_name)
        os.mkdir(self.path)

        ## Copy base files and rename to current run accordingly
        os.system(f'cp -r {self.base_case_dir}/* {self.path}')
        os.system(f'mv {self.path}/base_SMX.f90 {self.path}/{self.run_name}_SMX.f90')


        ## Assign values to placeholders
        os.system(f'sed -i \"s/\'pipe_radius\'/{self.pipe_radius}/\" {self.path}/{self.run_name}_SMX.f90')
        os.system(f'sed -i \"s/\'smx_pos\'/{self.smx_pos}/\" {self.path}/{self.run_name}_SMX.f90')
        os.system(f'sed -i \"s/\'bar_width\'/{self.bar_width}/g\" {self.path}/{self.run_name}_SMX.f90')
        os.system(f'sed -i \"s/\'bar_thickness\'/{self.bar_thickness}/\" {self.path}/{self.run_name}_SMX.f90')
        os.system(f'sed -i \"s/\'bar_angle\'/{self.bar_angle}/\" {self.path}/{self.run_name}_SMX.f90')
        os.system(f'sed -i \"s/\'n_bars\'/{self.n_bars}/\" {self.path}/{self.run_name}_SMX.f90')


        os.system(f'sed -i \"s/\'d_per_level\'/{self.d_per_level}/\" {self.path}/{self.run_name}_SMX.f90')
        os.system(f'sed -i \"s/\'n_levels\'/{self.n_levels}/\" {self.path}/{self.run_name}_SMX.f90')
        os.system(f'sed -i \"s/\'d_radius\'/{self.d_radius}/\" {self.path}/{self.run_name}_SMX.f90')


        os.system(f'sed -i \"s/\'flowrate\'/{self.flowrate}/\" {self.path}/{self.run_name}_SMX.f90')
        
        #modify the Makefile

        os.system(f'sed -i s/file/{self.run_name}_SMX/g {self.path}/Makefile')

        #compile the f90 into an executable

        os.chdir(self.path)
        os.system('make')
        os.system(f'mv {self.run_name}_SMX.x {self.run_name}.x')
        os.system('make clean')
        os.chdir('..')

    ### modifying .sh instance accordingly

    def setjobsh(self):
        
        d_pipe = 2*self.pipe_radius
        min_res = 18000

        if min_res*(2*self.max_diameter)/128 > 14:
            raise ValueError("Max p_diameter doesn't comply with min. res.")

        ## rename job with current run
        os.system(f'mv {self.path}/job_base.sh {self.path}/job_{self.run_name}.sh')

        ## Assign values to placeholders
        os.system(f'sed -i \"s/RUN_NAME/{self.run_name}/g\" {self.path}/job_{self.run_name}.sh')

        box_2 = math.ceil(4*self.pipe_radius*1000)/1000
        box_4 = math.ceil(2*self.pipe_radius*1000)/1000
        box_6 = math.ceil(2*self.pipe_radius*1000)/1000

        os.system(f'sed -i \"s/\'box2\'/{box_2}/\" {self.path}/job_{self.run_name}.sh')
        os.system(f'sed -i \"s/\'box4\'/{box_4}/\" {self.path}/job_{self.run_name}.sh')
        os.system(f'sed -i \"s/\'box6\'/{box_6}/\" {self.path}/job_{self.run_name}.sh')
        
        ## first cut for 64 cells per subdomain considering the max nodes can only be 10
        ## x-subdomain is 2 times the pipe's diameter
        first_d_cut = (64*10/(2*min_res))/self.max_diameter
        ## taking only 6 and 128 for the x configuration
        second_d_cut = ((6*64)/min_res)/self.max_diameter 

        if d_pipe < first_d_cut*self.max_diameter:
            cpus = min_res*(2*d_pipe)/64
            xsub = math.ceil(cpus / 2) * 2
            ysub = zsub = int(xsub/2)
            mem = 200
            cell1 = cell2 = cell3 = 64
            ncpus = int(xsub*ysub*zsub)
            n_nodes = 1
        elif d_pipe > second_d_cut*self.max_diameter:
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

        os.system(f'sed -i \"s/\'x_subd\'/{xsub}/\" {self.path}/job_{self.run_name}.sh')
        os.system(f'sed -i \"s/\'y_subd\'/{ysub}/\" {self.path}/job_{self.run_name}.sh')
        os.system(f'sed -i \"s/\'z_subd\'/{zsub}/\" {self.path}/job_{self.run_name}.sh')

        os.system(f'sed -i \"s/\'n_cpus\'/{ncpus}/\" {self.path}/job_{self.run_name}.sh')
        os.system(f'sed -i \"s/\'n_nodes\'/{n_nodes}/\" {self.path}/job_{self.run_name}.sh')
        os.system(f'sed -i \"s/\'mem\'/{mem}/\" {self.path}/job_{self.run_name}.sh')
        os.system(f'sed -i \"s/\'cell1\'/{cell1}/\" {self.path}/job_{self.run_name}.sh')
        os.system(f'sed -i \"s/\'cell2\'/{cell2}/\" {self.path}/job_{self.run_name}.sh')
        os.system(f'sed -i \"s/\'cell3\'/{cell3}/\" {self.path}/job_{self.run_name}.sh')

    ### checking job status and sending exceptions as fitting

    def job_wait(self, job_id, proc, job_name, queue):
        running = True
        while running:
            try:
                p = Popen(['qstat', '-a',f"{job_id}"],stdout=PIPE, stderr=PIPE)
                output, error = p.communicate()
            
                if p.returncode != 0:
                    raise subprocess.CalledProcessError(p.returncode, p.args)
                
                ## formatted to Imperial HPC 
                jobstatus = str(output,'utf-8').split()[-3:]

                if not jobstatus:
                    raise ValueError('Job exists but belongs to another account')
        
                if jobstatus[1] == 'Q' or jobstatus[1] == 'H':
                    sleep(1200)
                elif jobstatus[1] == 'R':
                    time_format = '%H:%M'
                    wall_time = datetime.datetime.strptime(jobstatus[0], time_format).time()
                    elap_time = datetime.datetime.strptime(jobstatus[2], time_format).time()
                    delta = datetime.datetime.combine(datetime.date.min, wall_time)-datetime.datetime.combine(datetime.date.min, elap_time)
                    remaining = delta.total_seconds()+120
                    sleep(remaining)

            except subprocess.CalledProcessError as e:
                queue.put((job_name, '0'))
                running = False
                raise RuntimeError("Job exists but belongs to another account")
            
            except ValueError as e:
                print(f"Error: {e}")
                raise ValueError('Existing job but doesnt belong to this account')

    ### checking termination condition (PtxEast position) and restarting sh based on last output restart reached

    def job_restart(self):

        ephemeral_path = os.path.join(os.environ['EPHEMERAL'],self.run_name)

        os.chdir(ephemeral_path)
        ## Checking location of the interface in the x direction -- stopping criterion
        ptxEast_f = pd.read_csv(f'{self.run_name}.csv').iloc[:,63].iloc[-1]
        domain_x = math.ceil(4*self.pipe_radius*1000)/1000
        min_lim = 0.95*domain_x

        if ptxEast_f < min_lim:
            os.chdir(self.path)
            line_with_pattern = None

            ### Checking last restart file instance in output file
            with open(f"{self.run_name}.out", 'r') as file:
                lines = file.readlines()
                pattern = 'writing restart file'
                for line in reversed(lines):
                    if pattern in line:
                        line_with_pattern = line.strip()
                        break
            ### Extracting restart number from line
            if line_with_pattern is not None:
                ### searching with re a sequence of 1 or more digits '\d+' in between two word boundaries '\b'
                match = re.search(r"\b\d+\b", line_with_pattern)
                if match is not None:
                    restart_num = int(match.group())
                else:
                    print('No restart number match found')
                    raise ValueError('No restart number match found')
                ### Modifying .sh file accordingly
                with open(f"job_{self.run_name}.sh", 'r+') as file:
                    lines = file.readlines()
                    restart_line = lines[384]
                    modified_restart = re.sub('FALSE', 'TRUE', restart_line)
                    ### modifying the restart number by searching dynamically with f-strings. 
                    modified_restart = re.sub(r'{}=\d+'.format('input_file_index'), '{}={}'.format('input_file_index', restart_num), modified_restart)
                    lines[384] = modified_restart
                    file.seek(0)
                    file.writelines(lines)
                    file.truncate()
                    os.chdir('..')
                    return True
            else:
                print("Pattern not found in the file.")
                raise ValueError('Restart file pattern in .out not found or does not exist')
            
        else:
            os.chdir(self.path)
            os.chdir('..')
            return False

    ### Converting vtk to vtr

    def vtk_convert(self):

        proc = []

        ephemeral_path = os.path.join(os.environ['EPHEMERAL'],self.run_name)
        convert_path = '/rds/general/user/jpv219/home/F_CONVERT'

        os.chdir(ephemeral_path)

        try:
            os.mkdir('RESULTS')
        except:
            pass

        ISO_file_list = glob.glob('ISO_*.vtk')
        VAR_file_list = glob.glob('VAR_*_*.vtk')
        
        last_vtk = max(int(file.split("_")[-1].split(".")[0]) for file in VAR_file_list)
        
        VAR_toconvert_list = glob.glob(f'VAR_*_{last_vtk}.vtk')

        files_to_convert = ISO_file_list + VAR_toconvert_list

        file_count = len(files_to_convert)

        for file in files_to_convert:
            shutil.move(file,'RESULTS')

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

        os.chdir(self.path)
        os.chdir('..')

        return jobid

    def submit_job(self):
        
        self.makef90()
        self.setjobsh()
        queue = Queue()
        proc = []





        




