### SMX_Automation_simulation_run, tailored for BLUE 12.5.1
### HPC scheduling and monitoring script
### to be run in the HPC node
### Author: Juan Pablo Valdes,
### Contributors: Paula Pico, Fuyue Liang
### Version: 2.0
### First commit: July, 2023
### Department of Chemical Engineering, Imperial College London

import os
from subprocess import Popen, PIPE
from time import sleep
import pandas as pd
import shutil
import glob
import math
import datetime
import subprocess
import re
import argparse
import json
import numpy as np
import operator

operator_map = {
    "<": operator.lt,
    ">": operator.gt,
    "<=": operator.le,
    ">=": operator.ge,
    "==": operator.eq,
    "!=": operator.ne
}

######################## EXCEPTION CLASSES ######################

class JobStatError(Exception):
    """Exception class for qstat exception when job has finished or has been removed from HPC run queue"""
    def __init__(self, message="Output empty on qstat execution, job finished or removed"):
        self.message = message
        super().__init__(self.message)

class ConvergenceError(Exception):
    """Exception class for convergence error on job"""
    def __init__(self, message="Convergence checks from csv have failed, job not converging and will be deleted"):
        self.message = message
        super().__init__(self.message)

class BadTerminationError(Exception):
    """Exception class for bad termination error on job after running"""
    def __init__(self, message="Job run ended on bad termination error"):
        self.message = message
        super().__init__(self.message)

#################################################################

################################################################################### PARAMETRIC STUDY ################################################################################

################################################################################# Author: Fuyue Liang #########################################################################

################################################################################# Tailored for stirred vessel study ###############################################################

class fuYUE:

        ### Init function
    def __init__(self,pset_dict) -> None:
                
        ### Initialising class attributes
        self.pset_dict = pset_dict
        self.run_path = pset_dict['run_path']
        self.convert_path = pset_dict['convert_path']
        self.case_type = pset_dict['case']
        self.run_ID = pset_dict['run_ID']
        self.run_name = pset_dict['run_name']
        self.local_path = pset_dict['local_path']
        self.save_path = pset_dict['save_path']
        self.convert_path = pset_dict['convert_path']

        self.cond_csv = pset_dict['cond_csv']
        self.conditional = pset_dict['conditional']
        self.cond_csv_limit = pset_dict['cond_csv_limit']

        self.path = os.path.join(self.run_path, self.run_name)
        self.mainpath = os.path.join(self.run_path,'..')
        self.output_file_path = os.path.join(self.path,f'{self.run_name}.out')
        self.ephemeral_path = os.path.join(os.environ['EPHEMERAL'],self.run_name)

        self.juan = HPCScheduling(pset_dict)

            ### Function shortcuts
        self.monitor = self.juan.monitor
        self.jobwait = self.juan.job_wait

    def __construct__(self,pset_dict):
        if self.case_type == 'geom' or self.case_type == 'sp_geom':

            ### Geometry features
            self.bar_width = pset_dict['bar_width']
            self.bar_thickness = pset_dict['bar_thickness']
            self.bar_angle = pset_dict['bar_angle']
            self.pipe_radius = pset_dict['pipe_radius']
            self.n_bars = pset_dict['n_bars']
            self.flowrate = pset_dict['flowrate']
            self.smx_pos = pset_dict['smx_pos']
            # two-phase
            if self.case_type == 'geom':
                self.d_per_level = pset_dict['d_per_level']
                self.n_levels = pset_dict['n_levels']
                self.d_radius = pset_dict['d_radius']
            # single-phase
            elif self.case_type == 'sp_geom':
                self.n_ele = pset_dict['n_ele']

        elif self.case_type == 'surf':

            ### Surfactant features
            self.diff1 = pset_dict['D_d']
            self.diff2 = format(float(pset_dict['D_b']),'.10f')
            self.ka = format(float(pset_dict['ka']),'.10f')
            self.kd = format(float(pset_dict['kd']),'.10f')
            self.ginf = format(float(pset_dict['ginf']),'.10f')
            self.gini = format(float(pset_dict['gini']),'.10f')
            self.diffs = format(float(pset_dict['D_s']),'.10f')
            self.beta = format(float(pset_dict['beta']),'.10f')
        else:
            pass


    def run(self):

        pass
    ### checking jobstate and sleeping until completion or restart commands

    def f90(self):
        pass

    def sh(self):
        pass


################################################################################### PARAMETRIC STUDY ################################################################################

################################################################################# Author: Juan Pablo Valdes #########################################################################

################################################################################# Tailored for SMX static mixer study ###############################################################

class HPCScheduling:

    ### Init function
     
    def __init__(self,pset_dict) -> None:
                
        ### Initialising class attributes
        self.pset_dict = pset_dict
        self.run_path = pset_dict['run_path']
        self.convert_path = pset_dict['convert_path']
        self.case_type = pset_dict['case']
        self.run_ID = pset_dict['run_ID']
        self.run_name = pset_dict['run_name']
        self.local_path = pset_dict['local_path']
        self.save_path = pset_dict['save_path']
        self.convert_path = pset_dict['convert_path']

        self.cond_csv = pset_dict['cond_csv']
        self.conditional = pset_dict['conditional']
        self.cond_csv_limit = pset_dict['cond_csv_limit']

        if self.case_type == 'geom' or self.case_type == 'sp_geom':

            ### Geometry features
            self.bar_width = pset_dict['bar_width']
            self.bar_thickness = pset_dict['bar_thickness']
            self.bar_angle = pset_dict['bar_angle']
            self.pipe_radius = pset_dict['pipe_radius']
            self.n_bars = pset_dict['n_bars']
            self.flowrate = pset_dict['flowrate']
            self.smx_pos = pset_dict['smx_pos']
            # two-phase
            if self.case_type == 'geom':
                self.d_per_level = pset_dict['d_per_level']
                self.n_levels = pset_dict['n_levels']
                self.d_radius = pset_dict['d_radius']
            # single-phase
            elif self.case_type == 'sp_geom':
                self.n_ele = pset_dict['n_ele']

        elif self.case_type == 'surf':

            ### Surfactant features
            self.diff1 = pset_dict['D_d']
            self.diff2 = format(float(pset_dict['D_b']),'.10f')
            self.ka = format(float(pset_dict['ka']),'.10f')
            self.kd = format(float(pset_dict['kd']),'.10f')
            self.ginf = format(float(pset_dict['ginf']),'.10f')
            self.gini = format(float(pset_dict['gini']),'.10f')
            self.diffs = format(float(pset_dict['D_s']),'.10f')
            self.beta = format(float(pset_dict['beta']),'.10f')
        else:
            pass

        self.path = os.path.join(self.run_path, self.run_name)
        self.mainpath = os.path.join(self.run_path,'..')
        self.output_file_path = os.path.join(self.path,f'{self.run_name}.out')
        self.ephemeral_path = os.path.join(os.environ['EPHEMERAL'],self.run_name)

    ### assigning input parametric values as attributes of the SimScheduling class and submitting jobs

    def run(self):

        ### Creating f90
        print('-' * 100)
        print('F90 CREATION')
        print('-' * 100)

        self.makef90()

        ### Creating job.sh
        print('-' * 100)
        print('JOB.SH CREATION')
        print('-' * 100)

        try:
            self.setjobsh()
        except ValueError as e:
            print(f'Case ID {self.run_ID} failed due to: {e}')
            print("====EXCEPTION====")
            print("ValueError")
            raise ValueError (f'Exited HPC with error {e}')

        ### Submitting job.sh
        print('-' * 100)
        print('JOB SUBMISSION')
        print('-' * 100)

        ### wait time to submit jobs, avoiding them to go all at once
        init_wait_time = np.random.RandomState().randint(60,180)
        sleep(init_wait_time)

        job_IDS = self.submit_job(self.path,self.run_name)

        print('-' * 100)
        print(f'Job {self.run_ID} submitted succesfully with ID {job_IDS}')

        sleep(120)

        ### Check job status and assign waiting time accordingly
        try:
            t_jobwait, status, update_jobID = self.job_wait(job_IDS)
            print("====JOB_IDS====")
            print(update_jobID)
            print("====JOB_STATUS====")
            print(status)
            print("====WAIT_TIME====")
            print(t_jobwait)

        except JobStatError:
            print(f'Job {self.run_ID} failed on initial submission')
            print("====EXCEPTION====")
            print("JobStatError")
        except ValueError:
            print("====EXCEPTION====")
            print("ValueError")

    ### checking jobstate and sleeping until completion or restart commands

    def monitor(self):

        ### Read dictionary with job_ID to monitor
        self.jobID = self.pset_dict['jobID']
        self.check = self.pset_dict['check']


        ### Call job waiting method and extract corresponding outputs
        try:
            t_jobwait, status, newjobid = self.job_wait(
                int(self.jobID))
            print("====JOB_IDS====")
            print(newjobid)
            print("====JOB_STATUS====")
            print(status)
            print("====WAIT_TIME====")
            print(t_jobwait)

            ### If job running, start convergence checks
            if status == 'R' and self.check:
                chk_status = self.check_convergence()

                ### Job likely to diverge, kill the job and raise the exception
                if chk_status == 'D':
                    print('-' * 100)
                    print("====EXCEPTION====")
                    print("ConvergenceError")
                    print('-' * 100)
                    print(f'Job from run {self.run_ID} is failing to converge')
                    print(f'Killing Job ID {self.jobID} from run {self.run_ID}')
                    print('-' * 100)
                    Popen(['qdel', f"{self.jobID}"])

                ### Convergence checks not needed at early stage in the run
                elif chk_status == 'NR':
                    print('-' * 100)
                    print('Convergence check starting condition not met, trying again later...')
                    print('-' * 100)
                ### Csv does not exist, convergence checks skipped
                elif chk_status == 'FNF':
                    print('-' * 100)
                    print('Warning: CSV file not found, cannot execute convergence checks, moving on...')
                    print('-' * 100)

                ### Job running and complying with all set checks
                else:
                    print('-' * 100)
                    print(f'Required convergence checks for job {self.run_ID} have passed successfully')
                    print('-' * 100)

        except JobStatError:
            print("====EXCEPTION====")
            print("JobStatError")
        except ValueError as e:
            print("====EXCEPTION====")
            print("ValueError")
            print(f'Exited with message: {e}')
           
    ### creating f90 instance and executable

    def makef90(self):

        ## Create run_ID directory
        os.mkdir(self.path)
        base_path = self.pset_dict['base_path']
        base_case_dir = os.path.join(base_path, self.case_type)

        ## Copy base files and rename to current run accordingly
        os.system(f'cp -r {base_case_dir}/* {self.path}')
        os.system(f'mv {self.path}/base_SMX.f90 {self.path}/{self.run_name}_SMX.f90')
        print('-' * 100)
        print(f'Run directory {self.path} created and base files copied')

        if self.case_type == 'geom' or self.case_type == 'sp_geom':

            ## Assign values to placeholders
            os.system(f'sed -i \"s/\'pipe_radius\'/{self.pipe_radius}/\" {self.path}/{self.run_name}_SMX.f90')
            os.system(f'sed -i \"s/\'smx_pos\'/{self.smx_pos}/\" {self.path}/{self.run_name}_SMX.f90')
            os.system(f'sed -i \"s/\'bar_width\'/{self.bar_width}/g\" {self.path}/{self.run_name}_SMX.f90')
            os.system(f'sed -i \"s/\'bar_thickness\'/{self.bar_thickness}/\" {self.path}/{self.run_name}_SMX.f90')
            os.system(f'sed -i \"s/\'bar_angle\'/{self.bar_angle}/\" {self.path}/{self.run_name}_SMX.f90')
            os.system(f'sed -i \"s/\'n_bars\'/{self.n_bars}/\" {self.path}/{self.run_name}_SMX.f90')
            os.system(f'sed -i \"s/\'flowrate\'/{self.flowrate}/\" {self.path}/{self.run_name}_SMX.f90')

            if self.case_type == 'geom':
                os.system(f'sed -i \"s/\'d_per_level\'/{self.d_per_level}/\" {self.path}/{self.run_name}_SMX.f90')
                os.system(f'sed -i \"s/\'n_levels\'/{self.n_levels}/\" {self.path}/{self.run_name}_SMX.f90')
                os.system(f'sed -i \"s/\'d_radius\'/{self.d_radius}/\" {self.path}/{self.run_name}_SMX.f90')

            else:
                os.system(f'sed -i \"s/\'n_elements\'/{self.n_ele}/\" {self.path}/{self.run_name}_SMX.f90')

            os.system(f'sed -i \"s/\'flowrate\'/{self.flowrate}/\" {self.path}/{self.run_name}_SMX.f90')
            print('-' * 100)
            print(f'Placeholders for geometry specs in {self.run_name}_SMX.f90 modified correctly')
        
        #modify the Makefile

        os.system(f'sed -i s/file/{self.run_name}_SMX/g {self.path}/Makefile')

        #compile the f90 into an executable

        os.chdir(self.path)
        subprocess.run('make',shell=True, capture_output=True, text=True, check=True)
        print('-' * 100)
        print('Makefile created succesfully')
        os.system(f'mv {self.run_name}_SMX.x {self.run_name}.x')
        subprocess.run('make cleanall',shell=True, capture_output=True, text=True, check=True)
        os.chdir('..')

    ### modifying .sh instance accordingly

    def setjobsh(self):
        
        ## rename job with current run
        os.system(f'mv {self.path}/job_base.sh {self.path}/job_{self.run_name}.sh')

        ## Assign values to placeholders
        os.system(f'sed -i \"s/RUN_NAME/{self.run_name}/g\" {self.path}/job_{self.run_name}.sh')

        ### If geometry variations are studied, construct domain and mesh specifications in job.sh accordingly
        if self.case_type == 'geom' or self.case_type == 'sp_geom':

            radius = float(self.pipe_radius)
            d_pipe = 2*radius

            if self.case_type == 'geom':
                min_res = 18000
                n_ele = 1
                ### Resolution and domain size condition: highest res scenario is with 6^3 and 128^3 cells
                if 128*5/d_pipe<min_res:
                    raise ValueError("Pipe diameter doesn't comply with min. res.")
            else:
                min_res = 9000
                n_ele = float(self.n_ele)
                ### Resolution and domain size condition: highest res scenario depending on the number of elements and the limit of cpus pre node = 256
                if (n_ele<=3 and 128*4/d_pipe<min_res) or (n_ele>3 and 128*3/d_pipe<min_res):
                    raise ValueError("Pipe diameter and n_elements doesn't comply with min. res.")

            ## x-subdomain (length) is (n_ele+1)*diameter large
            box_2 = math.ceil((n_ele+1)*2*radius*1000)/1000
            box_4 = math.ceil(2*radius*1000)/1000
            box_6 = math.ceil(2*radius*1000)/1000

            os.system(f'sed -i \"s/\'box2\'/{box_2}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'box4\'/{box_4}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'box6\'/{box_6}/\" {self.path}/job_{self.run_name}.sh')

            ### High and low cell number cases
            yz_cpus_l = (min_res*d_pipe)/64

            yz_cpus_h = (min_res*d_pipe)/128

            ### Two phase case with only one element
            # Settings designed to operate with only one node in the short queue in the HPC
            if n_ele == 1:
                
                if yz_cpus_l <= 5:
                    xsub = math.ceil(yz_cpus_l)*2
                    ysub = zsub = int(xsub/2)
                    mem = 200 
                    cell1 = cell2 = cell3 = 64
                    ncpus = int(xsub*ysub*zsub)
                    n_nodes = 1

                elif yz_cpus_l <=6:
                    xsub = math.ceil(yz_cpus_l)
                    ysub = zsub = int(xsub)
                    mem = 300 
                    cell1 = 128
                    cell2 = cell3 = 64
                    ncpus = int(xsub*ysub*zsub)
                    n_nodes = 1

                else:
                    xsub = math.ceil(yz_cpus_h)
                    ysub = zsub = int(xsub)
                    mem = 768
                    cell1 = cell2 = cell3 = 128
                    ncpus = int(xsub*ysub*zsub)
                    n_nodes = 1

            ### Single phase case with multiple elements
            ### First if looking for 64 cells and second if augmenting to 128 cell cases
            elif n_ele <=3:

                if yz_cpus_l<=4:
                    ysub = zsub = math.ceil(yz_cpus_l)
                    xsub = int(ysub*(n_ele+1))
                    mem = 200
                    cell1 = cell2 = cell3 = 64
                    ncpus = int(xsub*ysub*zsub)
                    n_nodes = 1

                else:
                    ysub = zsub = math.ceil(yz_cpus_h)
                    xsub = int(ysub*(n_ele+1))
                    mem = 768
                    cell1 = cell2 = cell3 = 128
                    ncpus = int(xsub*ysub*zsub)
                    n_nodes = 1

            elif n_ele>3:
                
                if yz_cpus_l<=3:
                    ysub = zsub = math.ceil(yz_cpus_l)
                    xsub = int(ysub*(n_ele+1))
                    mem = 200
                    cell1 = cell2 = cell3 = 64
                    ncpus = int(xsub*ysub*zsub)
                    n_nodes = 1

                else:
                    ysub = zsub = math.ceil(yz_cpus_h)
                    xsub = int(ysub*(n_ele+1))
                    mem = 768
                    cell1 = cell2 = cell3 = 128
                    ncpus = int(xsub*ysub*zsub)
                    n_nodes = 1

            ### Replacing placeholders in job.sh file after resolution calculations
            os.system(f'sed -i \"s/\'x_subd\'/{xsub}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'y_subd\'/{ysub}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'z_subd\'/{zsub}/\" {self.path}/job_{self.run_name}.sh')

            os.system(f'sed -i \"s/\'n_cpus\'/{ncpus}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'n_nodes\'/{n_nodes}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'mem\'/{mem}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'cell1\'/{cell1}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'cell2\'/{cell2}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'cell3\'/{cell3}/\" {self.path}/job_{self.run_name}.sh')

            print('-' * 100)
            print(f'Placeholders replaced succesfully in job.sh for run:{self.run_ID}')

        elif self.case_type == 'surf':

            ### Replacing placeholders for surfactant parametric study with fixed geometry
            os.system(f'sed -i \"s/\'diff1\'/{self.diff1}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'diff2\'/{self.diff2}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'ka\'/{self.ka}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'kd\'/{self.kd}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'ginf\'/{self.ginf}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'gini\'/{self.gini}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'diffs\'/{self.diffs}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'beta\'/{self.beta}/\" {self.path}/job_{self.run_name}.sh')

            print('-' * 100)
            print(f'Placeholders replaced succesfully in job.sh for run:{self.run_ID}')

    ### checking job status and sending exceptions as fitting

    def job_wait(self,job_id):
        try:
            p = Popen(['qstat', '-a',f"{job_id}"],stdout=PIPE, stderr=PIPE)
            output = p.communicate()[0]
        
            if p.returncode != 0:
                raise subprocess.CalledProcessError(p.returncode, p.args)
            
            ## formatted to Imperial HPC, extracting job status and performing actions accordingly 
            jobstatus = str(output,'utf-8').split()[-3:]
            status = jobstatus[1]

            if not jobstatus:
                raise ValueError('Job exists but belongs to another account')
    
            if status == 'Q':
                t_wait = 3600
                newjobid = job_id
            elif status == 'H':
                print(f'Deleting HELD job with old id: {job_id}')
                print('-' * 100)
                Popen(['qdel', f"{job_id}"])
                sleep(60)
                newjobid = self.submit_job(self.path,self.run_name)
                t_wait = 1800
                print(f'Submitted new job with id: {newjobid}')
            elif status == 'R':
                time_format = '%H:%M'
                wall_time = datetime.datetime.strptime(jobstatus[0], time_format).time()
                elap_time = datetime.datetime.strptime(jobstatus[2], time_format).time()
                delta = datetime.datetime.combine(datetime.date.min, wall_time)-datetime.datetime.combine(datetime.date.min, elap_time)
                remaining = delta.total_seconds()+60
                t_wait = remaining
                newjobid = job_id
            else:
                t_wait = 0
                
        except subprocess.CalledProcessError:
            raise JobStatError("qstat output empty, job finished or deleted from HPC run queue")
        
        except ValueError as e:
            print(f"Error: {e}")
            raise ValueError('Existing job but doesnt belong to this account')
            
        return t_wait, status, newjobid

    ### checking if the running job is diverging or not
    ### Author: Fuyue Liang

    def check_convergence(self):

        ### Jumping to ephemeral to read csv and begin checks
        ephemeral_path = os.path.join(os.environ['EPHEMERAL'],self.run_name)
        os.chdir(ephemeral_path)
        chk_status = None

        ### Checking if the csv exists
        if not os.path.exists(f'{self.run_name}.csv' if os.path.exists(f'{self.run_name}.csv') else f'HST_{self.run_name}.csv'):
            chk_status = 'FNF'
            return chk_status
       
        csv_to_check = pd.read_csv(f'{self.run_name}.csv' if os.path.exists(f'{self.run_name}.csv') else f'HST_{self.run_name}.csv')

        # verify whether convergence checks can start
        len_to_check = 300
        recent = int(len_to_check * 0.95)
        window_size = max(10,int(len_to_check * 0.05))
        window_step = max(10, int(window_size * 0.5))
        recent_data = csv_to_check.iloc[-recent:]
        relchg_thres = 0.15
        grad_thres = 0.01
        if len(csv_to_check) < len_to_check:
            # let the job run for longer, return NotReady NR status
            chk_status = 'NR'
            return chk_status

        else:
            # check the CFL and time step: CFL < dt or CFL drop below a lower bound
            lower_limit = csv_to_check['dt CFL'].nlargest(5).iloc[-1] * 1e-3
            CFL_check = np.any(csv_to_check['dt CFL'] < lower_limit)

            dt_CFL, dt = csv_to_check['dt CFL'].values, csv_to_check['dt'].values
            dt_arr = dt_CFL - dt
            dt_check = np.any(dt_arr < 0)
            ts_check = CFL_check or dt_check

            # check the Max(div): Max div fluctuate outside a threshold
            moving_avg_div = recent_data['Max(div(V))'].rolling(window=window_size).mean()[::window_step].dropna().values
            relchg_div = np.diff(moving_avg_div) / moving_avg_div[:-1]
            grad_div = np.gradient(moving_avg_div, 2)

            stable_period_div = int(len(relchg_div) * 0.9)
            stable_relchg_div = 0
            stable_grad_div = 0

            for rate in relchg_div:
                if abs(rate) < relchg_thres:
                       stable_relchg_div += 1
                else:
                       stable_relchg_div = 0
            for rate in grad_div:
                if abs(rate) < grad_thres:
                       stable_grad_div += 1
                else:
                       stable_grad_div = 0
            div_check = stable_relchg_div < stable_period_div or stable_grad_div < stable_period_div

            # check the KE: there exists an explosive increase (relative change larger than a threshold)
            moving_avg_ke = recent_data['Kinetic Energy'].rolling(window=window_size).mean()[::window_step].dropna().values
            relchg_ke = np.diff(moving_avg_ke) / moving_avg_ke[:-1]
            grad_ke = np.gradient(moving_avg_ke,2)
            stable_period_ke = int(len(relchg_ke) * 0.9)
            stable_relchg_ke = 0
            stable_grad_ke = 0
            
            for rate in relchg_ke:
                if abs(rate) < relchg_thres:
                       stable_relchg_ke += 1
                else:
                       stable_relchg_ke = 0
            for rate in grad_ke:
                if abs(rate) < grad_thres:
                       stable_grad_ke += 1
                else:
                       stable_grad_ke = 0
            ke_check = stable_relchg_ke < stable_period_ke or stable_grad_ke < stable_period_ke
            # check all the conditions
            checks = {
                'time step check':ts_check,
                'divergence check':div_check,
                'kinetic energy check':ke_check
            }
            
            ### Counting failed checks with True = 1 and False = 0
            failed_checks = sum(value for value in checks.values())
            ### Adding failed checks if value = True
            failed_keys = [key for key, value in checks.items() if value]

            ### If 2/3 checks fail, raise a diverging D status
            if failed_checks >=2:
                chk_status ='D'
                print(f'Job seems to be diverging or unstable since it does not pass {failed_checks} checks: {failed_keys}.')
            ### Else keep monitoring with converging status C, issuing warnings where appropiate
            elif failed_checks == 1:
                chk_status = 'C'
                print(f'WARNING: Check: {failed_keys} has failed to pass, job will continue')
            
            else:
                chk_status = 'C'
                print('All checks have passed successfully')

            return chk_status

    ### Function that performs multiple checks to decide if the simulation should restart
    ### Author: Paula Pico

    def condition_restart(self):
        new_restart_num = 0
        message = []
    
        # Check # 1: Does the .out file exist? If not raise exception and kill workflow --------------------------------------------------------------
        if not os.path.exists(self.output_file_path):
            message = ['-' * 100,"====EXCEPTION====","FileNotFoundError",f'File {self.run_name}.out does not exist','-' * 100]
            return False, new_restart_num, message

        # Check # 2: Did the simulation diverge or were the .rst files deleted? If so, raise exception and kill workflow -----------------------------
        os.chdir(self.path)
        line_with_pattern = None
        
        ### Checking last restart file instance in output file
        with open(f"{self.run_name}.out", 'r') as file:
            pattern = 'BAD TERMINATION OF ONE OF YOUR APPLICATION PROCESSES'
            # Only read the last 50 lines of .out file
            lines = file.readlines()[-50:]
            for line in reversed(lines):
                if pattern in line:
                    line_with_pattern = line.strip()
                    break
            if line_with_pattern is not None:
                message = ['-' * 100,"====EXCEPTION====","BadTerminationError",f'Simulation {self.run_name} diverged or .rst files deleted!','-' * 100]
                return False, new_restart_num, message
        
        # Check # 3: Has the finishing condition been satisfied? If so, raise exception and kill workflow  -----------------------------------------------
        os.chdir(self.ephemeral_path)

        if os.path.exists(os.path.join(".", f'{self.run_name}.csv' if os.path.exists(f'{self.run_name}.csv') else f'HST_{self.run_name}.csv')):
            csv_file = pd.read_csv(f'{self.run_name}.csv' if os.path.exists(f'{self.run_name}.csv') else f'HST_{self.run_name}.csv')

            ### Check if the key supplied as cond_csv acutally exists in the csv file before carrying on
            if self.cond_csv not in csv_file.columns:
                raise KeyError('Stop condition parameter defined does not exist in the csv file')
            
            cond_val_last = csv_file.iloc[:,csv_file.columns.get_loc(self.cond_csv)].iloc[-1]
            cond_val_ini = csv_file.iloc[:,csv_file.columns.get_loc(self.cond_csv)].iloc[0]
            progress = 100*np.abs(((cond_val_last - cond_val_ini)/(float(self.cond_csv_limit) - cond_val_ini)))
            comparison_func = operator_map[self.conditional]

            if not comparison_func(cond_val_last, float(self.cond_csv_limit)):
                message = ['-' * 100,f"Simulation {self.run_name} reached completion, no restarts required","====RETURN_BOOL====","False",'-' * 100]
                return False, new_restart_num, message
        else:
            print('-' * 100)
            print("WARNING: No *csv file found. Cannot check finishing condition. Simulation progress not calculated")
            progress = 0
            print('-' * 100)
            message.append(
                f"{'-' * 100}\n"
                f"WARNING: \n"
                f" No *csv file found. Cannot check finishing condition.\n"
                f"Simulation progress not calculated.\n"
                f"{'-' * 100}\n"
            )

        # Check # 4: Did the HPC kill the job due to lack of memory? If so, issue warning and continue -------------------------------------------------------
        os.chdir(self.path)
        line_with_pattern = None
        
        ### Checking last restart file instance in output file
        with open(f"{self.run_name}.out", 'r') as file:
            pattern = 'PBS: job killed: mem'
            # Only read the last 50 lines of .out file
            lines = file.readlines()[-50:]
            for line in reversed(lines):
                if pattern in line:
                    line_with_pattern = line.strip()
                    break
            if line_with_pattern is not None:
                message.append(
                    f"{'-' * 100}\n"
                    f"WARNING: \n"
                    f"Simulation {self.run_name} was killed due to lack of memory.\n"
                    f"Job will be re-submitted but please check.\n"
                    f"{'-' * 100}\n"
                )
        
        # Check # 5: Has it created .rst files? If not raise exception and kill workflow. Are they new files? If not, issue warning and continue -------------------
        os.chdir(self.path)
        line_with_pattern = None
        
        ### Checking last restart file instance in output file
        with open(f"{self.run_name}.out", 'r') as file:
            pattern = 'writing restart file'
            lines = file.readlines()
            for line in reversed(lines):
                if pattern in line:
                    line_with_pattern = line.strip()
                    break
            ### Extracting restart number from line
            if line_with_pattern is None:
                message = ['-' * 100,"====EXCEPTION====","ValueError",f'Restart file pattern in .out not found for simulation {self.run_name}','-' * 100]
                return False, new_restart_num, message       
            else:
                ### searching with re a sequence of 1 or more digits '\d+' in between two word boundaries '\b'
                match = re.search(r"\b\d+\b", line_with_pattern)
                if match is None:
                   message = ['-' * 100,"====EXCEPTION====","ValueError",f'No restart number match found in simulation {self.run_name}','-' * 100]
                   return False, new_restart_num, message
                else:
                    new_restart_num = int(match.group())
                with open(f"job_{self.run_name}.sh", 'r+') as file:
                    lines = file.readlines()
                    for line in reversed(lines):
                        match = re.search(r'input_file_index=(\d+)', line)
                        if match:
                            old_restart_num = int(match.group(1))
                            break
                if new_restart_num == old_restart_num:
                    message.append(
                        f"{'-' * 100}\n"
                        f"WARNING: \n"
                        f"No new .rst files were created in the previous run.\n"
                        f"Job will be re-submitted but please check.\n"
                        f"{'-' * 100}\n"
                    )

        message.append(
            f"{'-' * 100}\n"
            f"Simulation {self.run_name} passed all critical restarting checks!\n"
            f"The restart index is {new_restart_num}\n"
            f"The relative progress is {round(progress, 2)}%\n"
            f"{'-' * 100}\n"
        )

        # If all checks have been passed, then return True to restart the job
        return True, new_restart_num, message

    ### Restarting sh based on termination condition eval and last output restart reached
    ### Authors: Juan Pablo Valdes, Paula Pico
    
    def job_restart(self):

        # Calling the checking function to see if the simulation can restart, verifying cond_csv key exists condition in csv file
        try:
            ret_bool, new_restart_num, message = self.condition_restart()
        except KeyError as e:
            print(f'Exited with message: {e}')
            print("====EXCEPTION====")
            print("KeyError")
            return False

        # If the output of the cheking function is True, being the restarting process
        if ret_bool:
            for line in message:
                print(line)
            os.chdir(self.path)
            ### Modifying .sh file accordingly
            with open(f"job_{self.run_name}.sh", 'r+') as file:
                lines = file.readlines()
                for line in lines:
                    if "input_file_index=" in line:
                        restart_line = line
                        break
                modified_restart = re.sub('FALSE', 'TRUE', restart_line)

                ### modifying the restart number by searching dynamically with f-strings. 
                modified_restart = re.sub(r'{}=\d+'.format('input_file_index'), '{}={}'.format('input_file_index', new_restart_num), modified_restart)
                lines[lines.index(restart_line)] = modified_restart
                file.seek(0)
                file.writelines(lines)
                file.truncate()

            ### submitting job with restart modification
            job_IDS = self.submit_job(self.path,self.run_name)
            print('-' * 100)
            print(f'Job {self.run_name} re-submitted correctly with ID: {job_IDS}')
            sleep(120)

            ### check status and waiting time for re-submitted job
            try:
                t_jobwait, status, new_jobID = self.job_wait(job_IDS)
                print("====JOB_IDS====")
                print(new_jobID)
                print("====JOB_STATUS====")
                print(status)
                print("====WAIT_TIME====")
                print(t_jobwait)
                print("====RETURN_BOOL====")
                print("True")
                return True
            except JobStatError:
                print(f'Restart job {self.run_ID} failed on initial re-submission')
                print("====EXCEPTION====")
                print("JobStatError")
            except ValueError:
                print("====EXCEPTION====")
                print("ValueError")
            
        else:
            print('-' * 100)
            for line in message:
                print(line)
            return False

    ### Converting vtk to vtr

    def vtk_convert(self):

        ### Move to ephemeral and create RESULTS saving folder
        ephemeral_path = os.path.join(os.environ['EPHEMERAL'],self.run_name)

        os.chdir(ephemeral_path)

        try:
            os.mkdir('RESULTS')
            print('-' * 100)
            print(f'RESULTS folder created in {ephemeral_path}')
        except FileExistsError:
            pass

        ### Listing ISO and VAR vtks and pvds
        ISO_file_list = glob.glob('ISO_*.vtk')
        VAR_file_list = glob.glob('VAR_*_*.vtk')
        PVD_file_list = glob.glob('VAR_*_time=*.pvd')
        sorted_PVDs = sorted(PVD_file_list, key = lambda filename: 
                    float(filename.split('=')[-1].split('.pvd')[0]))
        last_vtk = max(int(file.split("_")[-1].split(".")[0]) for file in VAR_file_list)

        ### First and last pvd file for pvpython processing
        pvd_0file = glob.glob(f'VAR_{self.run_name}_time=0.00000E+00.pvd')[0]
        pvd_ffile = sorted_PVDs[-1]
    
        ### Files to be converted, last time step in VAR
        VAR_toconvert_list = glob.glob(f'VAR_*_{last_vtk}.vtk')
        files_to_convert = ISO_file_list + VAR_toconvert_list
        file_count = len(files_to_convert)

        ### Check if the files to be converted exist

        if (ISO_file_list and VAR_toconvert_list):

            ### Moving files to RESULTS
            for file in files_to_convert:
                try:
                    shutil.move(file,'RESULTS')
                except (FileNotFoundError, shutil.Error) as e:
                    print('-' * 100)
                    print("====EXCEPTION====")
                    print("FileNotFoundError")
                    print('-' * 100)
                    print(f"Exited with message :{e}, File or directory not found.")
                    print('-' * 100)
                    return
        ### If files don't exist, exit function and terminate pipeline
        else:
            print('-' * 100)
            print("====EXCEPTION====")
            print("FileNotFoundError")
            print('-' * 100)
            print("Either ISO or VAR files don't exist.")
            print('-' * 100)
            return

        print('-' * 100)
        print('Convert files copied to RESULTS')

        ### Moving individual files of interest: pvd, csv
        try:
            shutil.move(f'VAR_{self.run_name}.pvd','RESULTS')
            shutil.move(f'ISO_static_1_{self.run_name}.pvd','RESULTS')
            shutil.move(f'{self.run_name}.csv' if os.path.exists(f'{self.run_name}.csv') else f'HST_{self.run_name}.csv','RESULTS')
            if pvd_0file == pvd_ffile:

                shutil.move(f'{pvd_0file}', 'RESULTS')
                print('Warning: No vtk timesteps were generated, adjust vtk timestep save. Pvpython calculatons will be performed from the initial state')
            else:
                shutil.move(f'{pvd_0file}', 'RESULTS')
                shutil.move(f'{pvd_ffile}', 'RESULTS')
            print('-' * 100)
            print('VAR, ISO and csv files moved to RESULTS')
        except (FileNotFoundError, shutil.Error) as e:
            print('-' * 100)
            print("====EXCEPTION====")
            print("FileNotFoundError")
            print('-' * 100)
            print(f"Exited with message :{e}, File or directory not found.")
            print('-' * 100)
            return

        ### Cleaning previous restart and vtk from ephemeral
        os.system('rm *rst')

        os.chdir('RESULTS')

        try:
            os.mkdir('VTK_SAVE')
        except FileExistsError:
            pass

        ### Finding, copying and modifying convert files into RESULTS
        convert_scripts = glob.glob(os.path.join(self.convert_path, '*'))

        for file in convert_scripts:
            try:
                shutil.copy2(file, '.')
            except (FileNotFoundError, PermissionError, OSError):
                print("====EXCEPTION====")
                print("FileNotFoundError")
                print(f"Failed to copy '{file}'.")
                return

        os.system(f'sed -i \"s/\'FILECOUNT\'/{file_count}/\" Multithread_pool.py')

        ### Submitting job convert and extracting job_id, wait time and status
        jobid = self.submit_job(os.path.join(ephemeral_path,'RESULTS'),'convert')

        print('-' * 100)
        print(f'JOB CONVERT from {self.run_name} submitted succesfully with ID {jobid}')
        sleep(60)

        try:
            t_jobwait, status, new_jobID = self.job_wait(jobid)
            print("====JOB_IDS====")
            print(new_jobID)
            print("====JOB_STATUS====")
            print(status)
            if status == 'Q' or status == 'H':
                print("====WAIT_TIME====")
                print(t_jobwait-1800)
            elif status == 'R':
                print("====WAIT_TIME====")
                print(t_jobwait)

        except JobStatError:
            print(f'Convert job {self.run_ID} failed on initial submission')
            print("====EXCEPTION====")
            print("JobStatError")

        except ValueError:
            print("====EXCEPTION====")
            print("ValueError")

    ### submitting the SMX job and recording job_id

    def submit_job(self,path,name):

        proc = []
        os.chdir(f'{path}')
        proc = Popen(['qsub', f"job_{name}.sh"], stdout=PIPE)

        output = proc.communicate()[0].decode('utf-8').split()

        ### Search job id from output after qsub
        jobid = int(re.search(r'\b\d+\b',output[0]).group())

        return jobid
    
def main():
    ### Argument parser to specify function to run
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "function",
        choices=["run","monitor","job_restart","vtk_convert"], 
    )

    ### Input argument for dictionary
    parser.add_argument(
        "--pdict",
        type=json.loads,
    )

    args = parser.parse_args()

    simulator = HPCScheduling(args.pdict)

    if hasattr(simulator, args.function):
        func = getattr(simulator, args.function)
        func()
    else:
        print("Invalid function name")

if __name__ == "__main__":
    main()
