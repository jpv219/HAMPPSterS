### SMX_Automation_simulation_run, tailored for BLUE 12.5.1
### CFD scheduling, monitoring and post-processing script
### to be run locally
### Authors: Juan Pablo Valdes, Paula Pico
### First commit: July, 2023
### Department of Chemical Engineering, Imperial College London

import os
from time import sleep
import pandas as pd
import subprocess
import paramiko
import configparser
import warnings
import json
import numpy as np
import logging
import shutil
import glob
from stat import S_ISDIR
from datetime import datetime

class SimScheduling:

    ### Init function
     
    def __init__(self) -> None:
        pass

    ### Defining individual logging files for each run.

    def set_log(self, log_filename):
        # Create a new logger instance for each process
        logger = logging.getLogger(__name__)

        # Clear existing handlers to avoid duplication
        logger.handlers = []

        # Create a new file handler and set its formatter
        file_handler = logging.FileHandler(log_filename)
        formatter = logging.Formatter(fmt="%(asctime)s - %(message)s", datefmt="[%d/%m/ - %H:%M:%S]")
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger's handlers
        logger.addHandler(file_handler)

        return logger  # Return the logger instance

    ### Checking if a pvpython process is active

    @staticmethod
    def is_pvpython_running():
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'] == 'pvpython':
                return True, process.info['pid']
        return False, None

    ### converting dictionary input from psweep run_local into readable JSON format

    @staticmethod
    def convert_to_json(obj):
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, np.int64):
            return int(obj) 
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    ### local run assigning parametric study to HPC handling script and performing overall BLUE workflow

    def localrun(self,pset_dict):
        ###Path and running attributes
        self.pset_dict = pset_dict
        self.case_type = pset_dict['case']
        self.run_ID = pset_dict['run_ID']
        self.local_path = pset_dict['local_path']
        self.save_path = pset_dict['save_path']
        self.run_path = pset_dict['run_path']
        self.run_name = "run_"+str(self.run_ID)
        self.usr = pset_dict['user']

        self.main_path = os.path.join(self.run_path,'..')

        ### Logger set-up
        log_filename = f"output_{self.case_type}/output_{self.run_name}.txt"
        log = self.set_log(log_filename)

        dict_str = json.dumps(pset_dict, default=self.convert_to_json, ensure_ascii=False)

        ### First job creation and submission

        HPC_script = 'HPC_run_scheduling.py'
        
        log.info('-' * 100)
        log.info('-' * 100)
        log.info('NEW RUN')
        log.info('-' * 100)
        log.info('-' * 100)

        ### wait time to connect at first, avoiding multiple simultaneuous connections
        init_wait_time = np.random.RandomState().randint(0,180)
        sleep(init_wait_time)

        try:
            command = f'python {self.main_path}/{HPC_script} run --pdict \'{dict_str}\''
            jobid, t_wait, status, _ = self.execute_remote_command(command=command,search=0,log=log)
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"SSH ERROR: Authentication failed: {e}")
            return {}
        except (ValueError, FileNotFoundError,NameError) as e:
            log.info(f'Exited with message: {e}')
            return {}
            
        ### Job monitor and restarting nested loop. Checks job status and restarts if needed.

        restart = True
        while restart:

            ### job monitoring loop

            log.info('-' * 100)
            log.info('JOB MONITORING')
            log.info('-' * 100)

            try:
                self.jobmonitor(t_wait, status, jobid, self.run_ID, HPC_script,log)
            except (ValueError, FileNotFoundError,NameError) as e:
                log.info(f'Exited with message: {e}')
                return {}
            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                log.info(f"SSH ERROR: Authentication failed: {e}")
                return {}

            ### Job restart execution

            log.info('-' * 100)
            log.info('JOB RESTARTING')
            log.info('-' * 100)

            try:
                log.info('-' * 100)
                command = f'python {self.main_path}/{HPC_script} job_restart --pdict \'{dict_str}\''
                new_jobID, new_t_wait, new_status, ret_bool = self.execute_remote_command(
                    command=command, search=2, log=log
                    )

                log.info('-' * 100)

                ### updating
                jobid = new_jobID
                t_wait = new_t_wait
                status = new_status
                restart = eval(ret_bool)

            except (ValueError,FileNotFoundError,NameError) as e:
                log.info(f'Exited with message: {e}')
                return {}
            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                log.info(f"SSH ERROR: Authentication failed: {e}")
                return {}

        ### vtk convert job creation and submission

        log.info('-' * 100)
        log.info('VTK CONVERTING')
        log.info('-' * 100)

        try:
            log.info('-' * 100)
            command = f'python {self.main_path}/{HPC_script} vtk_convert --pdict \'{dict_str}\''
            conv_jobid, conv_t_wait, conv_status, _ = self.execute_remote_command(
                command=command,search=0,log=log
                )
            log.info('-' * 100)
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"SSH ERROR: Authentication failed: {e}")
            return {}
        except (ValueError, FileNotFoundError,NameError) as e:
            log.info(f'Exited with message: {e}')
            return {}
        
        conv_name = 'Convert' + str(self.run_ID)

        ### job convert monitoring loop

        log.info('-' * 100)
        log.info('JOB MONITORING')
        log.info('-' * 100)

        try:
            self.jobmonitor(conv_t_wait,conv_status,conv_jobid,conv_name,HPC_script,log=log)
        except (ValueError, FileNotFoundError,NameError) as e:
            log.info(f'Exited with message: {e}')
            return {}
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"SSH ERROR: Authentication failed: {e}")
            return {}

        ### Downloading files and local Post-processing

        log.info('-' * 100)
        log.info('DOWNLOADING FILES FROM EPHEMERAL')
        log.info('-' * 100)

        try:
            self.scp_download(log)
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"SSH ERROR: Authentication failed: {e}")
            return {}

        log.info('-' * 100)
        log.info('PVPYTHON POSTPROCESSING')
        log.info('-' * 100)

        ### Checking if a pvpython is operating on another process, if so sleeps.

        pvpyactive, pid = self.is_pvpython_running()

        while pvpyactive:
            log.info(f'pvpython is active in process ID : {pid}')
            sleep(600)
            pvpyactive, pid = self.is_pvpython_running()

        ### Exectuing post-processing
        dfDSD, IntA = self.post_process(log)
        Nd = dfDSD.size

        log.info('-' * 100)
        log.info('Post processing completed succesfully')
        log.info('-' * 100)
        log.info(f'Number of drops in this run: {Nd}')
        log.info(f'Drop size dist. {dfDSD}')
            
        return {"Nd":Nd, "DSD":dfDSD, "IntA":IntA}
    
    ### Local monitoring of existing jobs in HPC and performing overall BLUE workflow
    
    def localmonitor(self,pset_dict):
        ###Path and running attributes
        self.pset_dict = pset_dict
        self.local_path = pset_dict['local_path']
        self.save_path = pset_dict['save_path']
        self.save_path_csv = pset_dict['save_path_csv']
        self.run_path = pset_dict['run_path']
        self.init_jobID = pset_dict['init_jobID']
        self.case_name = pset_dict['case_name']
        self.run_ID = pset_dict['run_ID']
        self.main_path = os.path.join(self.run_path,'..')
        self.usr = pset_dict['user']

        ### Logger set-up
        log_filename = f"output_{self.case_name}.txt"
        log = self.set_log(log_filename)
        dict_str = json.dumps(pset_dict, default=self.convert_to_json, ensure_ascii=False)

        HPC_script = 'HPC_run_scheduling.py'

        ##Initial values
        t_wait = 1
        status = 'I'
        jobid = self.init_jobID

        restart = True
        while restart:

            ### job monitoring loop

            log.info('-' * 100)
            log.info('JOB MONITORING')
            log.info('-' * 100)

            try:
                self.jobmonitor(t_wait, status, jobid, self.run_ID, HPC_script,log)
            except (ValueError, FileNotFoundError,NameError) as e:
                log.info(f'Exited with message: {e}')
                return {}
            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                log.info(f"Authentication failed: {e}")
                return {}
            

            ### Downloading csv file

            log.info('-' * 100)
            log.info('DOWNLOADING csv FILE')
            log.info('-' * 100)

            try:
                self.copy_csv(log)
            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                log.info(f"SSH ERROR: Authentication failed: {e}")
                return {}

            ### Job restart execution

            log.info('-' * 100)
            log.info('JOB RESTARTING')
            log.info('-' * 100)

            try:
                log.info('-' * 100)
                command = f'python {self.main_path}/{HPC_script} test_restart --pdict \'{dict_str}\''
                new_jobID, new_t_wait, new_status, ret_bool = self.execute_remote_command(
                    command=command, search=2, log=log
                    )

                log.info('-' * 100)

                ### updating
                jobid = new_jobID
                t_wait = new_t_wait
                status = new_status
                restart = eval(ret_bool)

            except (ValueError,FileNotFoundError,NameError) as e:
                log.info(f'Exited with message: {e}')
                return {}
            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                log.info(f"Authentication failed: {e}")
                return {}

    ### Local pipeline for converting vtk files

    def localconvert(self,pset_dict):
        ###Path and running attributes
        self.pset_dict = pset_dict
        self.local_path = pset_dict['local_path']
        self.save_path = pset_dict['save_path']
        self.run_path = pset_dict['run_path']
        self.init_jobID = pset_dict['init_jobID']
        self.case_name = pset_dict['case_name']
        self.run_ID = pset_dict['run_ID']
        self.main_path = os.path.join(self.run_path,'..')
        self.usr = pset_dict['user']

        ### Logger set-up
        log_filename = f"testest_{self.case_name}.txt"
        log = self.set_log(log_filename)
        dict_str = json.dumps(pset_dict, default=self.convert_to_json, ensure_ascii=False)
        HPC_script = 'HPC_run_scheduling.py'

        log.info('-' * 100)
        log.info('-' * 100)
        log.info('NEW CONVERSION PROCESS')
        log.info('-' * 100)
        log.info('-' * 100)

        try:
            log.info('-' * 100)
            command = f'python {self.main_path}/{HPC_script} test_vtk_convert --pdict \'{dict_str}\''
            conv_jobid, conv_t_wait, conv_status, _ = self.execute_remote_command(
                command=command, search=2, log=log
                )

            log.info('-' * 100)

        except (ValueError,FileNotFoundError,NameError) as e:
            log.info(f'Exited with message: {e}')
            return {}
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"Authentication failed: {e}")
            return {}
        
        ### job monitoring loop

        log.info('-' * 100)
        log.info('JOB MONITORING')
        log.info('-' * 100)

        try:
            self.jobmonitor(conv_t_wait, conv_status, conv_jobid, self.run_ID, HPC_script,log)
        except (ValueError, FileNotFoundError,NameError) as e:
            log.info(f'Exited with message: {e}')
            return {}
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"Authentication failed: {e}")
            return {}
    
        ### vtk convert job creation and submission

        log.info('-' * 100)
        log.info('CHECKING IF CONVERSION WAS SUCCESFUL')
        log.info('-' * 100)

        try:
            log.info('-' * 100)
            command = f'python {self.main_path}/{HPC_script} test_check_convert --pdict \'{dict_str}\''
            _ = self.execute_remote_command(
                command=command, search=2, log=log
                )

            log.info('-' * 100)

        except (ValueError,FileNotFoundError,NameError) as e:
            log.info(f'Exited with message: {e}')
            return {}
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"Authentication failed: {e}")
            return {}

        ### Downloading files and local Post-processing

        log.info('-' * 100)
        log.info('DOWNLOADING FILES FROM EPHEMERAL')
        log.info('-' * 100)

        try:
            self.copy_convert(log)
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"SSH ERROR: Authentication failed: {e}")
            return {}
        
    #### Local function to copy converted files from EPHEMERAL to local directory 'postProcessing' within main directory of the case
    def copy_convert(self,log):

        ###Create run local directory to store data
        self.save_path = os.path.join(self.save_path)
        ephemeral_path = f'/rds/general/user/{self.usr}/ephemeral/'
        self.path = os.path.join(self.run_path)

        ### Config file with keys to login to the HPC
        config = configparser.ConfigParser()
        config.read(f'config_{self.usr}.ini')
        user = config.get('SSH', 'username')
        key = config.get('SSH', 'password')
        try_logins = ['login.hpc.ic.ac.uk','login-a.hpc.ic.ac.uk','login-b.hpc.ic.ac.uk','login-c.hpc.ic.ac.uk']

        for login in try_logins:
            
            ### Establish an SSH connection using a context manager
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            warnings.filterwarnings("ignore", category=ResourceWarning)

            try:
                ssh.connect(login, username=user, password=key)
                stdin, _, _ = ssh.exec_command("echo 'SSH connection test'")
                transport = ssh.get_transport()
                sftp = paramiko.SFTPClient.from_transport(transport)

                try:
                    remote_files = sftp.listdir_attr(self.path)
                    for item in remote_files:
                        remote_item_path = f"{self.path}/{item.filename}"
                        # Read remote "last_convert.txt" file to find the last directory of converted files to copy
                        if item.filename == "last_convert.txt":
                            with sftp.open(remote_item_path, "r") as remote_file:
                                last_FILES = remote_file.readline().strip()
                                print("Last directory of converted files:", last_FILES)
                                break  # Exit loop if file is found
                    else:
                        print("File not found.")
                except Exception as e:
                    print("An error occurred:", e)

                remote_path = os.path.join(ephemeral_path,self.case_name,last_FILES)

                # General function to copy "FILES_X+1" and everything inside this directory, except for "VTK_SAVE"
                def copy_remote_dir(remote_path, local_path, sftp):
                    for item in sftp.listdir_attr(remote_path):
                        remote_item_path = f"{remote_path}/{item.filename}"
                        local_item_path = os.path.join(local_path, item.filename)
                        if item.filename == "VTK_SAVE":
                            print(f"Skipping directory: {remote_item_path}")
                        elif S_ISDIR(item.st_mode):
                            os.makedirs(local_item_path, exist_ok=True)
                            copy_remote_dir(remote_item_path, local_item_path, sftp)
                        else:
                            sftp.get(remote_item_path, local_item_path)
                            print(f"Copying file: {remote_item_path} to {local_item_path}")

                remote_basename = os.path.basename(remote_path)
                local_directory_path = os.path.join(self.save_path, remote_basename)
                os.makedirs(local_directory_path, exist_ok=True)
                copy_remote_dir(remote_path, local_directory_path, sftp)
        
                log.info('-' * 100)
                log.info(f'{last_FILES} successfully copied to {self.save_path}')

                if stdin is not None:
                    break
                
            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                if login == try_logins[-1]:
                    raise e
                else:
                    log.info(f'SSH connection failed with login {login}, trying again ...')
                    continue

            ### closing HPC session
            finally:
                if 'sftp' in locals():
                    sftp.close()
                if 'stdin' in locals():
                    stdin.close()
                if 'ssh' in locals():
                    ssh.close()

        # Once the directory of converted files is copied from EPHEMERAL, move the pvds and vtrs to postProcessing (main post-processing directory)
        os.chdir(self.save_path)
        # Get a list of files matching the pattern
        pvds_to_move = [filename for filename in os.listdir(local_directory_path) if filename.endswith(".pvd")]

        for filename in pvds_to_move:
            source_file_path = os.path.join(local_directory_path, filename)
            destination_file_path = os.path.join(self.save_path, filename)
            
            # Move the file to the destination directory
            shutil.move(source_file_path, destination_file_path)
        print(f"pvds correctly moved to from {last_FILES} to postProcessing")

        vtrs_to_move = [filename for filename in os.listdir(f"{local_directory_path}/VTR_SAVE/") if filename.endswith(".vtr")]

        for filename in vtrs_to_move:
            source_file_path = os.path.join(local_directory_path, "VTR_SAVE", filename)
            destination_file_path = os.path.join(self.save_path, filename)
            
            # Move the file to the destination directory
            shutil.move(source_file_path, destination_file_path)
        print(f"vtrs correctly moved to from {last_FILES}/VTR_SAVE to postProcessing")

        log.info('-' * 100)
        log.info('-' * 100)
    
    ### Function to copy the csv file. To be executed at the end of every run
    def copy_csv(self,log):

        ###Create run local directory to store data
        self.save_path = os.path.join(self.save_path)
        self.save_path_csv = os.path.join(self.save_path_csv)
        ephemeral_path = f'/rds/general/user/{self.usr}/ephemeral/'
        self.path = os.path.join(self.run_path)

        ### Config file with keys to login to the HPC
        config = configparser.ConfigParser()
        config.read(f'config_{self.usr}.ini')
        user = config.get('SSH', 'username')
        key = config.get('SSH', 'password')
        try_logins = ['login.hpc.ic.ac.uk','login-a.hpc.ic.ac.uk','login-b.hpc.ic.ac.uk','login-c.hpc.ic.ac.uk']

        for login in try_logins:
            
            ### Establish an SSH connection using a context manager
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            warnings.filterwarnings("ignore", category=ResourceWarning)

            try:
                ssh.connect(login, username=user, password=key)
                stdin, _, _ = ssh.exec_command("echo 'SSH connection test'")
                transport = ssh.get_transport()
                sftp = paramiko.SFTPClient.from_transport(transport)
                remote_path = os.path.join(ephemeral_path,self.case_name)

                # Trying to Find .csv file in EPHEMERAL
                try:
                    remote_files = sftp.listdir(remote_path)
                    csv_files = [file for file in remote_files if file.endswith(".csv")]

                    # If csv is found. Create a directory named with current date in "temporal", copy the csv there and rename it to: *_{today_date}.csv
                    if csv_files:
                        print('-' * 100)
                        print(f"*.csv file found in remote directory")
                        print('-' * 100)
                        today_date = datetime.now().strftime("%d%m%y")
                        target_directory = os.path.join(self.save_path_csv, today_date)
                        os.makedirs(target_directory, exist_ok=True)
                        print(f"Directory {today_date} created")

                        for csv_file in csv_files:
                            new_csv_file_name = f"{os.path.splitext(csv_file)[0]}_{today_date}.csv"
                            remote_file_path = os.path.join(remote_path, csv_file)
                            local_file_path = os.path.join(target_directory, new_csv_file_name)
                            sftp.get(remote_file_path, local_file_path)
                            print(f"File {new_csv_file_name} copied and renamed")
                    else:
                        # If no csv file is found. Continue with the job restarting process and issue a warning
                        print("WARNING: No CSV files found on remote server. Simulation will be restarted but please check")
                finally:
                    print("Restarting process will begin")
                

                if stdin is not None:
                    break

            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                if login == try_logins[-1]:
                    raise e
                else:
                    log.info(f'SSH connection failed with login {login}, trying again ...')
                    continue

            ### closing HPC session
            finally:
                if 'sftp' in locals():
                    sftp.close()
                if 'stdin' in locals():
                    stdin.close()
                if 'ssh' in locals():
                    ssh.close()
        return True

    ### calling monitoring and restart function to check in on jobs

    def jobmonitor(self, t_wait, status, jobid, run, HPC_script,log):
        running = True
        while running:
            
            ### Setting updated dictionary with jobid from submitted job
            mdict = self.pset_dict   
            mdict['jobID'] = jobid
            mdict_str = json.dumps(mdict, default=self.convert_to_json, ensure_ascii=False)

            if t_wait>0:
                log.info('-' * 100)
                log.info(f'Job {run} with id: {jobid} has status {status}. Sleeping for:{t_wait/60} mins')
                log.info('-' * 100)

                #sleep(t_wait)
                sleep(60)

                try:
                    ### Execute monitor function in HPC to check job status
                    command = f'python {self.main_path}/{HPC_script} monitor --pdict \'{mdict_str}\''
                    new_jobid, new_t_wait, new_status, _ = self.execute_remote_command(
                        command=command,search=0,log=log
                        )
                    
                    ### update t_wait and job status accordingly
                    t_wait = new_t_wait
                    status = new_status
                    jobid = new_jobid

                    log.info('-' * 100)
                    log.info(f'Job {run} with id {jobid} status is {status}. Updated sleeping time: {t_wait/60} mins')
                except (RuntimeError, ValueError, NameError) as e:  
                    if isinstance(e, RuntimeError):

                        log.info('-' * 100)
                        log.info(f'Exited with message: {e}')
                        log.info('-' * 100)
                        log.info(f'JOB {run} FINISHED')
                        log.info('-' * 100)

                        ### Update t_wait and job status for finished job condition, exiting the loop
                        t_wait = 0
                        status = 'F'
                        running = False

                    else:
                        log.info('-' * 100)
                        log.info(f'Exited with message: {e}')
                        log.info('-' * 100)
                        raise e

                except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                    log.info(f"Authentication failed: {e}")
                    raise e
            else:
                running = False

    ### Executing HPC functions remotely via Paramiko SSH library.

    def execute_remote_command(self,command,search,log):

        ### Read SSH configuration from config file
        config = configparser.ConfigParser()
        config.read(f'config_{self.usr}.ini')
        user = config.get('SSH', 'username')
        key = config.get('SSH', 'password')
        try_logins = ['login.hpc.ic.ac.uk','login-a.hpc.ic.ac.uk','login-b.hpc.ic.ac.uk','login-c.hpc.ic.ac.uk']

        ### Initialize variables for result storage
        jobid, t_wait, status, ret_bool = None, 0, None, None
        exc = None

        for login in try_logins:

            ### Establish an SSH connection using a context manager
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            warnings.filterwarnings("ignore", category=ResourceWarning)

            try:
                ssh.connect(login, username=user, password=key)

                stdin, stdout, stderr = ssh.exec_command(command)
                out_lines = []
                for line in stdout:
                    stripped_line = line.strip()
                    log.info(stripped_line)
                    out_lines.append(stripped_line)
                
                ### Extracting exceptions, job id, job wait time, status and restart condition
                results = self.search(out_lines=out_lines,search=search)

                jobid = results.get("jobid", None)
                t_wait = float(results.get("t_wait", 0))
                status = results.get("status", None)
                ret_bool = results.get("ret_bool", None)
                exc = results.get("exception",None)

                ### Handle exceptions
                if exc is not None:
                    if exc == "RuntimeError":
                        raise RuntimeError('Job finished')
                    elif exc == "ValueError":
                        raise ValueError('Exception raised from job sh creation, or qstat in job_wait \
                                    or attempting to search restart in job_restart')
                    elif exc == "FileNotFoundError":
                        raise FileNotFoundError('Cannot execute restart procedure, either .out or .csv files not found')
                    elif exc == "SystemExit":
                        raise SystemExit('Simulation finished')
                    else:
                        raise NameError('Search for exception from log failed')
                    
                if stdin is not None:
                    break

            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                if login == try_logins[-1]:
                    raise e
                else:
                    log.info(f'SSH connection failed with login {login}, trying again ...')
                    continue

            ### Closing HPC session
            finally:
                if 'stdin' in locals():
                    stdin.close()
                if 'stdout' in locals():
                    stdout.close()
                if 'stderr' in locals():
                    stderr.close()
                ssh.close()
        
        return jobid, t_wait, status, ret_bool
 
    ### Search and extract communications from the functions executed remotely on the HPC

    def search(self,out_lines,search):
        ##### search = 0 : looks for JobID, status and wait time
        ##### search = 1 : looks for wait time, status
        ##### search = 2 : looks for JobID, status and wait time and boolean return values

        ### Define markers and corresponding result keys for different search types
        if search == 0:
            markers = {
                "====JOB_IDS====": "jobid",
                "====WAIT_TIME====": "t_wait",
                "====JOB_STATUS====": "status",
                "====EXCEPTION====" : "exception"
                }
        elif search == 1:
            markers = {
                "====WAIT_TIME====": "t_wait",
                "====JOB_STATUS====": "status",
                "====EXCEPTION====" : "exception"
                }
        elif search == 2:
            markers = {
                "====JOB_IDS====": "jobid",
                "====WAIT_TIME====": "t_wait",
                "====JOB_STATUS====": "status",
                "====RESTART====": "ret_bool",
                "====EXCEPTION====" : "exception"
                }
            
        results = {}
        current_variable = None

        for idx, line in enumerate(out_lines):
            if line in markers:
                current_variable = markers[line]
                # Store the value associated with the marker as the value of the current variable
                results[current_variable] = out_lines[idx + 1]


        return results

    ### Download final converted data to local processing machine

    def scp_download(self,log):

        ###Create run local directory to store data
        self.save_path_runID = os.path.join(self.save_path,self.run_name)
        ephemeral_path = f'/rds/general/user/{self.usr}/ephemeral/'

        try:
            os.mkdir(self.save_path_runID)
            log.info(f'Saving folder created at {self.save_path}')
        except:
            pass

        ### Config faile with keys to login to the HPC
        config = configparser.ConfigParser()
        config.read(f'config_{self.usr}.ini')
        user = config.get('SSH', 'username')
        key = config.get('SSH', 'password')
        try_logins = ['login.hpc.ic.ac.uk','login-a.hpc.ic.ac.uk','login-b.hpc.ic.ac.uk','login-c.hpc.ic.ac.uk']

        for login in try_logins:
            
            ### Establish an SSH connection using a context manager
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            warnings.filterwarnings("ignore", category=ResourceWarning)

            try:
                ssh.connect(login, username=user, password=key)
                stdin, _, _ = ssh.exec_command("echo 'SSH connection test'")
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

                log.info('-' * 100)
                log.info(f'Files successfully copied at {self.save_path}')

                if stdin is not None:
                    break
                
            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                if login == try_logins[-1]:
                    raise e
                else:
                    log.info(f'SSH connection failed with login {login}, trying again ...')
                    continue

            ### closing HPC session
            finally:
                if 'sftp' in locals():
                    sftp.close()
                if 'stdin' in locals():
                    stdin.close()
                if 'ssh' in locals():
                    ssh.close()
                    
            log.info('-' * 100)
            log.info('-' * 100)

    ### Post-processing function extracting relevant outputs from sim's final timestep.

    def post_process(self,log):

        ### Extracting Interfacial Area from CSV
        os.chdir(self.save_path_runID) 
        pvdfiles = glob.glob('VAR_*_time=*.pvd')
        maxpvd_tf = max(float(filename.split('=')[-1].split('.pvd')[0]) for filename in pvdfiles)

        df_csv = pd.read_csv(os.path.join(self.save_path_runID,f'{self.run_name}.csv'))
        df_csv['diff'] = abs(df_csv['Time']-maxpvd_tf)
        log.info('Reading data from csv')
        log.info('-'*100)

        tf_row = df_csv.sort_values(by='diff')

        IntA = tf_row.iloc[0]['INTERFACE_SURFACE_AREA']
        log.info('Interfacial area extracted')
        log.info('-'*100)

        os.chdir(self.local_path)

        ### Running pvpython script for Nd and DSD
        script_path = os.path.join(self.local_path,'PV_ndrop_DSD.py')

        log.info('Executing pvpython script')
        log.info('-'*100)

        try:
            output = subprocess.run(['pvpython', script_path, self.save_path , self.run_name], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            captured_stdout = output.stdout.decode('utf-8').strip().split('\n')
            outlines= []
            for i, line in enumerate(captured_stdout):
                stripline = line.strip()
                outlines.append(stripline)
                if i < len(captured_stdout) - 1:
                    log.info(stripline)
            
            df_DSD = pd.read_json(outlines[-1], orient='split', dtype=float, precise_float=True)


        except subprocess.CalledProcessError as e:
            log.info(f"Error executing the script with pvpython: {e}")
            df_DSD = None
        except FileNotFoundError:
            log.info("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")
            df_DSD = None

        return df_DSD, IntA
