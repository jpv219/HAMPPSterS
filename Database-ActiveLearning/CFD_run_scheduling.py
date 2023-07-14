import numpy as np
import os
from subprocess import Popen, PIPE
from _thread import start_new_thread
from queue import Queue
from time import sleep
import pandas as pd
import shutil
import glob
import random
import csv
import math

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
        
        self.init_wait_time = np.random.RandomState().randint(0,300)
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

    def setjobsh(self):

        ## Create run_ID directory
        self.run_name = "run_"+str(self.run_ID)
        self.path = os.path.join(self.run_path, self.run_name)
        
        ## rename job with current run
        os.system(f'mv {self.path}/job_base.sh {self.path}/{self.run_name}.sh')

        ## Assign values to placeholders
        os.system(f'sed -i \"s/RUN_NAME/{self.run_name}/\" {self.path}/{self.run_name}.sh')

        box_2 = math.ceil(4*self.pipe_radius*1000)/1000
        box_4 = math.ceil(self.pipe_radius*1000)/1000
        box_6 = math.ceil(self.pipe_radius*1000)/1000

        os.system(f'sed -i \"s/\'box2\'/{box_2}/\" {self.path}/{self.run_name}.sh')
        os.system(f'sed -i \"s/\'box4\'/{box_4}/\" {self.path}/{self.run_name}.sh')
        os.system(f'sed -i \"s/\'box6\'/{box_6}/\" {self.path}/{self.run_name}.sh')

        d_pipe = 2*self.pipe_radius

        
     
        os.system(f'sed -i \"s/\'x_subd\'/{xsub}/\" {self.path}/{self.run_name}.sh')
        os.system(f'sed -i \"s/\'y_subd\'/{ysub}/\" {self.path}/{self.run_name}.sh')
        os.system(f'sed -i \"s/\'z_subd\'/{zsub}/\" {self.path}/{self.run_name}.sh')

        os.system(f'sed -i \"s/\'n_cpus\'/{ncpus}/\" {self.path}/{self.run_name}.sh')
        os.system(f'sed -i \"s/\'mem\'/{mem}/\" {self.path}/{self.run_name}.sh')
        os.system(f'sed -i \"s/\'cell1\'/{cell1}/\" {self.path}/{self.run_name}.sh')
        os.system(f'sed -i \"s/\'cell2\'/{cell2}/\" {self.path}/{self.run_name}.sh')
        os.system(f'sed -i \"s/\'cell3\'/{cell3}/\" {self.path}/{self.run_name}.sh')
        




        




