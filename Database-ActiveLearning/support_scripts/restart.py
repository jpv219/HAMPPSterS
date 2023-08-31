import os
import re
import pandas as pd
from time import sleep
from subprocess import Popen, PIPE
import datetime
import subprocess
import operator
import numpy as np

class JobStatError(Exception):
    """Exception class for qstat exception when job has finished or has been removed from HPC run queue"""
    def __init__(self, message="Output empty on qstat execution, job finished or removed"):
        self.message = message
        super().__init__(self.message)

operator_map = {
    "<": operator.lt,
    ">": operator.gt,
    "<=": operator.le,
    ">=": operator.ge,
    "==": operator.eq,
    "!=": operator.ne
}

class Restart:

    ### Init function
     
    def __init__(self) -> None:
        pass

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

    def job_restart(self,pset_dict):

        self.pset_dict = pset_dict
        self.run_ID = pset_dict['run_ID']
        self.run_name = pset_dict['run_name']
        self.cond_csv = pset_dict['cond_csv']
        self.conditional = pset_dict['conditional']
        self.cond_csv_limit = pset_dict['cond_csv_limit']

        self.run_path = pset_dict['run_path']
        self.path = os.path.join(self.run_path, self.run_name)
        self.output_file_path = os.path.join(self.path,f'{self.run_name}.out')
        self.ephemeral_path = os.path.join(os.environ['EPHEMERAL'],self.run_name)

        # Calling the checking function to see if the the simulation can restart
        
        try:
            ret_bool, new_restart_num, message = self.condition_restart()
        except KeyError as e:
            print(f'Exited with message: {e}')
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
    
    def submit_job(self,path,name):

        proc = []
        os.chdir(f'{path}')
        proc = Popen(['qsub', f"job_{name}.sh"], stdout=PIPE)

        output = proc.communicate()[0].decode('utf-8').split()

        ### Search job id from output after qsub
        jobid = int(re.search(r'\b\d+\b',output[0]).group())

        return jobid

        
def main():

    restart = Restart()
    pset_dict = {'run_ID': '5', 'run_name': 'run_sp_5', 'cond_csv':'Time','conditional':'<','cond_csv_limit':'1.067e-6',
                 'run_path':'/rds/general/user/nkovalc1/home/BLUE-12.5.1/project/ACTIVE_LEARNING/RUNS'}
    
    ret = restart.job_restart(pset_dict)

    print(ret)



if __name__ == "__main__":
    main()
