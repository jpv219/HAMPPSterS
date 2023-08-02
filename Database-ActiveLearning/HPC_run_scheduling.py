### SMX_Automation_simulation_run, tailored for BLUE 12.5.1
### CFD scheduling and monitoring script
### to be run in the HPC node
### Author: Juan Pablo Valdes,
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

class HPCScheduling:

    ### Init function
     
    def __init__(self) -> None:
        pass

    ### assigning input parametric values as attributes of the SimScheduling class and submitting jobs

    def run(self,pset_dict):
        ###Path and running attributes
        self.pset_dict = pset_dict
        self.run_path = pset_dict['run_path']
        self.base_path = pset_dict['base_path']
        self.convert_path = pset_dict['convert_path']
        self.case_type = pset_dict['case']
        self.run_ID = pset_dict['run_ID']
        self.local_path = pset_dict['local_path']
        self.save_path = pset_dict['save_path']

        if self.case_type == 'Geom':

            ### Geometry features
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

        else:

            ### Surfactant features
            self.diff1 = pset_dict['D_d']
            self.diff2 = pset_dict['D_b']
            self.ka = pset_dict['ka']
            self.kd = pset_dict['kd']
            self.ginf = pset_dict['ginf']
            self.gini = pset_dict['gini']
            self.diffs = pset_dict['D_s']
            self.beta = pset_dict['beta']

        self.base_case_dir = os.path.join(self.base_path, self.case_type)
        self.mainpath = os.path.join(self.run_path,'..')

        self.makef90()

        if self.case_type == 'Geom':
            try:
                self.setjobsh()
            except ValueError as e:
                print(f'Case ID {self.run_ID} failed due to: {e}')

        job_IDS = self.submit_job()

        print("====JOB_IDS====")
        print(job_IDS)

        #sleep(300)

        t_jobwait, status = self.job_wait(job_IDS)

        print("====JOB_STATUS====")
        print(status)
        print("====WAIT_TIME====")
        print(t_jobwait)

    ### checking jobstate and sleeping until completion or restart commands

    def monitor(self,mdict):
        self.mdict = mdict
        self.jobID = mdict['jobID']
        self.run_ID = mdict['run_ID']
        self.run_path = mdict['run_path']


        self.run_name = "run_"+str(self.run_ID)
        self.path = os.path.join(self.run_path, self.run_name)

        try:
            t_jobwait, status = self.job_wait(int(self.jobID))
            print("====JOB_STATUS====")
            print(status)
            print("====WAIT_TIME====")
            print(t_jobwait)

        except RuntimeError as e:
            print(f'Exited with message: {e}')
        except ValueError as e:
            print(f"Error: {e}")
           
    ### creating f90 instance and executable

    def makef90(self):

        ## Create run_ID directory
        self.run_name = "run_"+str(self.run_ID)
        self.path = os.path.join(self.run_path, self.run_name)
        os.mkdir(self.path)

        ## Copy base files and rename to current run accordingly
        os.system(f'cp -r {self.base_case_dir}/* {self.path}')
        os.system(f'mv {self.path}/base_SMX.f90 {self.path}/{self.run_name}_SMX.f90')
        print('-' * 100)
        print(f'Run directory {self.path} created and base files copied')

        if self.case_type == 'Geom':

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
            print('-' * 100)
            print(f'Placeholders for geometry specs in {self.run_name}_SMX.f90 modified correctly')
        
        #modify the Makefile

        os.system(f'sed -i s/file/{self.run_name}_SMX/g {self.path}/Makefile')

        #compile the f90 into an executable

        os.chdir(self.path)
        make_proc = subprocess.run('make',shell=True, capture_output=True, text=True, check=True)
        output = make_proc.stdout
        print('-' * 100)
        print(output)
        os.system(f'mv {self.run_name}_SMX.x {self.run_name}.x')
        subprocess.run('make cleanall',shell=True, capture_output=True, text=True, check=True)
        os.chdir('..')

    ### modifying .sh instance accordingly

    def setjobsh(self):
        
        ## rename job with current run
        os.system(f'mv {self.path}/job_base.sh {self.path}/job_{self.run_name}.sh')

        ## Assign values to placeholders
        os.system(f'sed -i \"s/RUN_NAME/{self.run_name}/g\" {self.path}/job_{self.run_name}.sh')

        if self.case_type == 'Geom':

            radius = float(self.pipe_radius)
            max_diameter = float(self.max_diameter)
            d_pipe = 2*radius
            min_res = 18000

            if min_res*(2*self.max_diameter)/128 > 16:
                raise ValueError("Max p_diameter doesn't comply with min. res.")

            box_2 = math.ceil(4*radius*1000)/1000
            box_4 = math.ceil(2*radius*1000)/1000
            box_6 = math.ceil(2*radius*1000)/1000

            os.system(f'sed -i \"s/\'box2\'/{box_2}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'box4\'/{box_4}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'box6\'/{box_6}/\" {self.path}/job_{self.run_name}.sh')
        
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
                    ysub = zsub = int(xsub/2)
                    mem = 920
                    cell1 = cell2 = cell3 = 128
                    ncpus = int(xsub*ysub*zsub)
                    n_nodes = 1
                elif cpus >10 and cpus <= 12:
                    xsub = 12
                    ysub = zsub = int(xsub/2)
                    cell1 = cell2 = cell3 = 128
                    n_nodes = 4
                    ncpus = int(xsub*ysub*zsub/n_nodes)
                    mem = 200
                elif cpus >12 and cpus <= 14:
                    xsub = 14
                    ysub = zsub = int(xsub/2)
                    cell1 = cell2 = cell3 = 128
                    n_nodes = 7
                    ncpus = int(xsub*ysub*zsub/n_nodes)
                    mem = 200
                elif cpus > 14 and cpus <=16:
                    xsub = 16
                    ysub = zsub = int(xsub/2)
                    cell1 = cell2 = cell3 = 128
                    n_nodes = 8
                    ncpus = int(xsub*ysub*zsub/n_nodes)
                    mem = 200

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

            print('-' * 100)
            print(f'Placeholders replaced succesfully in job for run:{self.run_ID}')

        elif self.case_type == 'Surf':

            os.system(f'sed -i \"s/\'diff1\'/{self.diff1}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'diff2\'/{self.diff2}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'ka\'/{self.ka}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'kd\'/{self.kd}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'ginf\'/{self.ginf}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'gini\'/{self.gini}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'diffs\'/{self.diffs}/\" {self.path}/job_{self.run_name}.sh')
            os.system(f'sed -i \"s/\'beta\'/{self.beta}/\" {self.path}/job_{self.run_name}.sh')

            print('-' * 100)
            print(f'Placeholders replaced succesfully in job for run:{self.run_ID}')

    ### checking job status and sending exceptions as fitting

    def job_wait(self,job_id):
        try:
            p = Popen(['qstat', '-a',f"{job_id}"],stdout=PIPE, stderr=PIPE)
            output = p.communicate()[0]
        
            if p.returncode != 0:
                raise subprocess.CalledProcessError(p.returncode, p.args)
            
            ## formatted to Imperial HPC 
            jobstatus = str(output,'utf-8').split()[-3:]
            status = jobstatus[1]

            if not jobstatus:
                raise ValueError('Job exists but belongs to another account')
    
            if status == 'Q' or status == 'H':
                t_wait = 1800
            elif status == 'R':
                time_format = '%H:%M'
                wall_time = datetime.datetime.strptime(jobstatus[0], time_format).time()
                elap_time = datetime.datetime.strptime(jobstatus[2], time_format).time()
                delta = datetime.datetime.combine(datetime.date.min, wall_time)-datetime.datetime.combine(datetime.date.min, elap_time)
                remaining = delta.total_seconds()+60
                t_wait = remaining
            else:
                t_wait = 0
                
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Job finished")
        
        except ValueError as e:
            print(f"Error: {e}")
            raise ValueError('Existing job but doesnt belong to this account')
            
        return t_wait, status

    ### checking termination condition (PtxEast position) and restarting sh based on last output restart reached

    def job_restart(self,pset_dict):

        self.run_ID = pset_dict['run_ID']
        self.run_name = "run_"+str(self.run_ID)
        self.convert_path = pset_dict['convert_path']
        self.pipe_radius = pset_dict['pipe_radius']
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

        shutil.move(f'VAR_{self.run_name}.pvd','RESULTS')

        os.system('rm *vtk')
        os.system('rm *rst')

        os.chdir('RESULTS')

        try:
            os.mkdir('VTK_SAVE')
        except:
            pass

        convert_scripts = glob.glob(os.path.join(self.convert_path, '*'))

        for file in convert_scripts:
            shutil.copy2(file, '.')

        os.system(f'sed -i \"s/\'FILECOUNT\'/{file_count}/\" Multithread_pool.py')
        
        proc = Popen(['qsub', 'job_convert.sh'], stdout=PIPE)

        output = proc.communicate()[0].decode('utf-8').split()

        jobid = int(re.search(r'\b\d+\b',output[0]).group())

        os.chdir(self.path)
        os.chdir('..')

        return jobid

    ### submitting the SMX job and recording job_id

    def submit_job(self):

        proc = []
        proc = Popen(['qsub', f"{self.path}/job_{self.run_name}.sh"], stdout=PIPE)

        output = proc.communicate()[0].decode('utf-8').split()

        jobid = int(re.search(r'\b\d+\b',output[0]).group())

        print('-' * 100)
        print(f'job {self.run_ID} submitted succesfully with ID {jobid}')

        return jobid
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "function",
        choices=["run","monitor","job_restart"], 
    )

    parser.add_argument(
        "--pdict",
        type=json.loads,
    )

    args = parser.parse_args()

    simulator = HPCScheduling()

    if hasattr(simulator, args.function):
        func = getattr(simulator, args.function)
        func(args.pdict)
    else:
        print("Invalid function name")

if __name__ == "__main__":
    main()
