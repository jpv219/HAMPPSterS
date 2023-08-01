### SMX_Automation_simulation_run, tailored for BLUE 12.5.1
### CFD scheduling, monitoring and post-processing script
### to be run locally
### Author: Juan Pablo Valdes,
### First commit: July, 2023
### Department of Chemical Engineering, Imperial College London

import os
from time import sleep
import pandas as pd
import subprocess
from logger import log
import paramiko
import configparser
import warnings
import json
import numpy as np

class SimScheduling:

    ### Init function
     
    def __init__(self) -> None:
        pass

    ### converting dictionary input from psweep run_local into readable JSON format

    @staticmethod
    def convert_to_json(obj):
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, np.int64):
            return int(obj) 
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    ### assigning input parametric values as attributes of the SimScheduling class and submitting jobs

    def run(self,pset_dict):
        ###Path and running attributes
        self.pset_dict = pset_dict
        self.case_type = pset_dict['case']
        self.run_ID = pset_dict['run_ID']
        self.local_path = pset_dict['local_path']
        self.save_path = pset_dict['save_path']
        self.run_path = pset_dict['run_path']

        self.main_path = os.path.join(self.run_path,'..')

        dict_str = json.dumps(pset_dict, default=self.convert_to_json)

        HPC_script = 'HPC_run_scheduling.py'
        command = f'python {self.main_path}/{HPC_script} run --pdict \'{dict_str}\''

        jobid, t_wait, status = self.execute_remote_command(command=command, dict_str=dict_str,search=1)

        ### calling monitoring function to check in on jobs
        mdict = pset_dict
        mdict['jobID'] = jobid
        mdict_str = json.dumps(mdict, default=self.convert_to_json)

        # running = True
        # while running:
        #     if t_wait>0:
        #         log.info(f'Sleeping for:{t_wait}')
        #         sleep(t_wait-1770)
        #         try:
        #             ssh.connect('login-a.hpc.ic.ac.uk', username=user, password=key)
        #             command = f'python {self.main_path}/{HPC_script} monitor --pdict \'{mdict_str}\''
        #             stdin, stdout, stderr = ssh.exec_command(command)
        #             out_lines = []
        #             for line in stdout:
        #                 stripped_line = line.strip()
        #                 log.info(stripped_line)
        #                 out_lines.append(stripped_line)

        #             results = self.search(out_lines=out_lines,search=0)
        #             t_wait = int(results.get("t_wait", None))
        #             status = results.get("status",None)
        #             log.info(f'updated sleeping time in job {t_wait} with status {status}')

        #         finally:
        #             stdin.close()
        #             stdout.close()
        #             stderr.close()
        #             ssh.close()
        #     else:
        #         running = False

        return {}
    
    def execute_remote_command(self,command,dict_str,search):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        warnings.filterwarnings("ignore", category=ResourceWarning)

        config = configparser.ConfigParser()
        config.read('configjp.ini')
        #config.read('confignk.ini')
        user = config.get('SSH', 'username')
        key = config.get('SSH', 'password')
        HPC_script = 'HPC_run_scheduling.py'
        dict_str = json.dumps(pset_dict, default=self.convert_to_json)

        try:
            ssh.connect('login-a.hpc.ic.ac.uk', username=user, password=key)
            command = f'python {self.mainpath}/{HPC_script} run --pdict \'{dict_str}\''

            stdin, stdout, stderr = ssh.exec_command(command)
            out_lines = []
            for line in stdout:
                stripped_line = line.strip()
                log.info(stripped_line)
                out_lines.append(stripped_line)
            
            ### Extracting job id and wait time for job
            results = self.search(out_lines=out_lines,search=search)

            jobid = results.get("jobid", None)
            t_wait = int(results.get("t_wait", None))
            status = results.get("status", None)

        ### closing HPC session
        finally:
            stdin.close()
            stdout.close()
            stderr.close()
            ssh.close()

        return jobid, t_wait, status
 
    def search(self,out_lines,search):
        if search >0:
            markers = {
                "====JOB_IDS====": "jobid",
                "====WAIT_TIME====": "t_wait",
                "====JOB_STATUS====": "status"
                }
            results = {}
            current_variable = None

            for idx, line in enumerate(out_lines):
                if line in markers:
                    current_variable = markers[line]
                    results[current_variable] = out_lines[idx + 1]
        else:
            markers = {
                "====WAIT_TIME====": "t_wait",
                "====JOB_STATUS====": "status"
                }
            results = {}
            current_variable = None

            for idx, line in enumerate(out_lines):
                if line in markers:
                    current_variable = markers[line]
                    results[current_variable] = out_lines[idx + 1]

        return results
    
    def post_process(self):

        script_path = os.path.join(self.local_path,'PV_ndrop_DSD.py')

        try:
            output = subprocess.run(['pvpython', script_path, self.save_path , self.run_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            captured_stdout = output.stdout.decode('utf-8')
            
            df_DSD = pd.read_json(captured_stdout, orient='split', dtype=float, precise_float=True)

            return df_DSD

        except subprocess.CalledProcessError as e:
            print(f"Error executing the script with pvpython: {e}")
        except FileNotFoundError:
            print("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")

