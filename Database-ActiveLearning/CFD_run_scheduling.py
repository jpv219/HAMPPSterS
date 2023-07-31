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

class SimScheduling:

    ### Init function
     
    def __init__(self) -> None:
        pass

    @staticmethod
    def convert_to_json(obj):
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

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

        self.base_case_dir = os.path.join(self.base_path, self.case_type)
        self.mainpath = os.path.join(self.run_path,'..')

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
            output = stdout.read().decode('utf-8').strip()
            log.info(output)

        finally:
            stdin.close()
            stdout.close()
            stderr.close()
            ssh.close()


        return {}
    
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

