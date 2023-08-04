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
import sys

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

    def localrun(self,pset_dict):
        ###Path and running attributes
        self.pset_dict = pset_dict
        self.case_type = pset_dict['case']
        self.run_ID = pset_dict['run_ID']
        self.local_path = pset_dict['local_path']
        self.save_path = pset_dict['save_path']
        self.run_path = pset_dict['run_path']
        self.run_name = "run_"+str(self.run_ID)

        self.main_path = os.path.join(self.run_path,'..')

        dict_str = json.dumps(pset_dict, default=self.convert_to_json, ensure_ascii=False)

        ### First job creation and submission

        HPC_script = 'HPC_run_scheduling.py'

        try:
            command = f'python {self.main_path}/{HPC_script} run --pdict \'{dict_str}\''
            jobid, t_wait, status, _ = self.execute_remote_command(command=command,search=0)
        except paramiko.AuthenticationException as e:
            print(f"Authentication failed: {e}")
            print(f'Error attempting to submit job with runID: {self.run_ID}')
            sys.exit(1)
        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
            print(f'Error attempting to submit job with runID: {self.run_ID}')
            sys.exit(1)
        
        ### Job monitor and restarting nested loop. Checks job status and restarts if needed.

        restart = True
        while restart:
            ### calling monitoring and restart function to check in on jobs
            mdict = pset_dict
            mdict['jobID'] = jobid
            mdict_str = json.dumps(mdict, default=self.convert_to_json, ensure_ascii=False)

            ### monitoring loop

            running = True
            while running:
                if t_wait>0:
                    log.info('-' * 100)
                    log.info(f'Sleeping for:{t_wait}')
                    log.info('-' * 100)
                    sleep(t_wait-1770)
                    try:
                        command = f'python {self.main_path}/{HPC_script} monitor --pdict \'{mdict_str}\''
                        _, new_t_wait, new_status, _ = self.execute_remote_command(command=command,search=1)
                        t_wait = new_t_wait
                        status = new_status
                        log.info('-' * 100)
                        log.info(f'Updated sleeping time: {t_wait} with status {status}')
                    except RuntimeError as e:
                        log.info(f'Exited with message: {e}')
                        t_wait = 0
                        status = 'F'
                        running = False
                    except ValueError as e:
                        log.info(f'Exited with message: {e}')
                    except NameError as e:
                        log.info(f'Exited with message: {e}')
                    except paramiko.AuthenticationException as e:
                        print(f"Authentication failed: {e}")
                        print(f'Error attempting to submit job with runID: {self.run_ID}')
                        sys.exit(1)
                    except paramiko.SSHException as e:
                        print(f"SSH connection failed: {e}")
                        print(f'Error attempting to submit job with runID: {self.run_ID}')
                        sys.exit(1)
                else:
                    running = False

            ### Job restart execution

            try:
                log.info('-' * 100)
                command = f'python {self.main_path}/{HPC_script} job_restart --pdict \'{dict_str}\''
                new_jobID, new_t_wait, new_status, ret_bool = self.execute_remote_command(command=command,search=2)
                log.info('-' * 100)

                ### updating
                jobid = new_jobID
                t_wait = new_t_wait
                status = new_status
                restart = eval(ret_bool)

            except ValueError as e:
                log.info(f'Exited with message: {e}')
            except paramiko.AuthenticationException as e:
                print(f"Authentication failed: {e}")
                print(f'Error attempting to submit job with runID: {self.run_ID}')
                sys.exit(1)
            except paramiko.SSHException as e:
                print(f"SSH connection failed: {e}")
                print(f'Error attempting to submit job with runID: {self.run_ID}')
                sys.exit(1)

        ### vtk convert job creation and submission

        try:
            log.info('-' * 100)
            command = f'python {self.main_path}/{HPC_script} vtk_convert --pdict \'{dict_str}\''
            conv_jobid, conv_t_wait, conv_status, _ = self.execute_remote_command(command=command,search=0)
            log.info('-' * 100)
        except paramiko.AuthenticationException as e:
            print(f"Authentication failed: {e}")
            print(f'Error attempting to submit job with runID: {self.run_ID}')
            sys.exit(1)
        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
            print(f'Error attempting to submit job with runID: {self.run_ID}')
            sys.exit(1)
        
        mdict['jobID'] = conv_jobid
        mdict_str = json.dumps(mdict, default=self.convert_to_json, ensure_ascii=False)

        ### job convert monitoring loop

        running = True
        while running:
            if conv_t_wait>0:
                log.info('-' * 100)
                log.info(f'Sleeping for:{conv_t_wait}')
                log.info('-' * 100)
                sleep(conv_t_wait-1770)
                try:
                    command = f'python {self.main_path}/{HPC_script} monitor --pdict \'{mdict_str}\''
                    _, new_t_wait, new_status, _ = self.execute_remote_command(command=command,search=1)
                    conv_t_wait = new_t_wait
                    conv_status = new_status
                    log.info('-' * 100)
                    log.info(f'Updated sleeping time: {conv_t_wait} with status {conv_status}')
                except RuntimeError as e:
                    log.info(f'Exited with message: {e}, for Job convert')
                    conv_t_wait = 0
                    conv_status = 'F'
                    running = False
                except ValueError as e:
                    log.info(f'Exited with message: {e}')
                except NameError as e:
                    log.info(f'Exited with message: {e}')
                except paramiko.AuthenticationException as e:
                    print(f"Authentication failed: {e}")
                    print(f'Error attempting to submit job with runID: {self.run_ID}')
                    sys.exit(1)
                except paramiko.SSHException as e:
                    print(f"SSH connection failed: {e}")
                    print(f'Error attempting to submit job with runID: {self.run_ID}')
                    sys.exit(1)
            else:
                running = False

        ### Downloading files and local Post-processing

        try:
            self.scp_download()
        except paramiko.AuthenticationException as e:
            print(f"Authentication failed: {e}")
            print(f'Error attempting to submit job with runID: {self.run_ID}')
            sys.exit(1)
        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
            print(f'Error attempting to submit job with runID: {self.run_ID}')
            sys.exit(1)
            
        return {}
    
    def execute_remote_command(self,command,search):
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
            t_wait = int(results.get("t_wait", 0))
            status = results.get("status", None)
            ret_bool = results.get("ret_bool", None)
            exc = results.get("exception",None)

            if exc is not None:
                if exc == "RuntimeError":
                    raise RuntimeError('Job finished')
                elif exc == "ValueError":
                    raise ValueError('Exception raised from qstat in job_wait or attempting to search restart in job_restart') 
                else:
                    raise NameError('Search for exception from log failed')

        ### closing HPC session
        finally:
            stdin.close()
            stdout.close()
            stderr.close()
            ssh.close()
        
        return jobid, t_wait, status, ret_bool
 
    def search(self,out_lines,search):
        ##### search = 0 : looks for JobID, status and wait time
        ##### search = 1 : looks for wait time, status
        ##### search = 2 : looks for JobID, status and wait time and boolean return values
        if search == 0:
            markers = {
                "====JOB_IDS====": "jobid",
                "====WAIT_TIME====": "t_wait",
                "====JOB_STATUS====": "status",
                "====EXCEPTION====" : "exception"
                }
            results = {}
            current_variable = None

            for idx, line in enumerate(out_lines):
                if line in markers:
                    current_variable = markers[line]
                    results[current_variable] = out_lines[idx + 1]
        elif search == 1:
            markers = {
                "====WAIT_TIME====": "t_wait",
                "====JOB_STATUS====": "status",
                "====EXCEPTION====" : "exception"
                }
            results = {}
            current_variable = None

            for idx, line in enumerate(out_lines):
                if line in markers:
                    current_variable = markers[line]
                    results[current_variable] = out_lines[idx + 1]
        elif search == 2:
            markers = {
                "====JOB_IDS====": "jobid",
                "====WAIT_TIME====": "t_wait",
                "====JOB_STATUS====": "status",
                "====RETURN_BOOL====": "ret_bool",
                "====EXCEPTION====" : "exception"
                }
            results = {}
            current_variable = None

            for idx, line in enumerate(out_lines):
                if line in markers:
                    current_variable = markers[line]
                    results[current_variable] = out_lines[idx + 1]

        return results

    def scp_download(self):

        ###Create run local directory to store data
        self.save_path_runID = os.path.join(self.save_path,self.run_name)
        ephemeral_path = '/rds/general/user/jpv219/ephemeral/'
        #ephemeral_path = '/rds/general/user/nkahouad/ephemeral/'
        try:
            os.mkdir(self.save_path_runID)
        except:
            pass
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        warnings.filterwarnings("ignore", category=ResourceWarning)

        config = configparser.ConfigParser()
        config.read('configjp.ini')
        #config.read('confignk.ini')
        user = config.get('SSH', 'username')
        key = config.get('SSH', 'password')

        try:
            ssh.connect('login-a.hpc.ic.ac.uk', username=user, password=key)
            transport = ssh.get_transport()
            sftp = paramiko.SFTPClient.from_transport(transport)

            remote_path = os.path.join(ephemeral_path,self.run_name,'RESULTS')

            remote_files = sftp.listdir_attr(remote_path)

            for file_attr in remote_files:
                remote_file_path = os.path.join(remote_path, file_attr.filename)
                local_file_path = os.path.join(self.save_path_runID, file_attr.filename)

                # Check if it's a regular file before copying
                if file_attr.st_mode & 0o100000:
                    sftp.get(remote_file_path, local_file_path)
                    log.info(f'Copied file {file_attr.filename}')
            

        ### closing HPC session
        finally:
            if 'sftp' in locals():
                sftp.close()
            if 'ssh' in locals():
                ssh.close()

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

