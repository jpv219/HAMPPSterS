import numpy as np
import os
from subprocess import Popen, PIPE
from _thread import start_new_thread
from queue import Queue
from time import sleep
import pandas as pd
import numpy as np
import shutil
import glob
import random
import csv

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
        self.run = "run_"+str(self.run_ID)
        self.path = os.path.join(self.run_path, self.run)
        os.mkdir(self.path)

        os.system(f'cp -r {self.base_case_dir}/* {self.path}')
        os.system(f'mv {self.path}/base_SMX.f90 {self.path}/{self.run_ID}_SMX.f90')


        ## Assign values to placeholders
        os.system(f'sed -i s/\'pipe_radius\'/{self.pipe_radius}/ {self.path}/{self.run_ID}_SMX.f90')
        os.system(f'sed -i s/\'smx_pos\'/{self.smx_pos}/ {self.path}/{self.run_ID}_SMX.f90')
        os.system(f'sed -i s/\'bar_width\'/{self.bar_width}/g {self.path}/{self.run_ID}_SMX.f90')
        os.system(f'sed -i s/\'bar_thickness\'/{self.bar_thickness}/ {self.path}/{self.run_ID}_SMX.f90')
        os.system(f'sed -i s/\'bar_angle\'/{self.bar_angle}/ {self.path}/{self.run_ID}_SMX.f90')
        os.system(f'sed -i s/\'pipe_radius\'/{self.pipe_radius}/ {self.path}/{self.run_ID}_SMX.f90')
        
        




