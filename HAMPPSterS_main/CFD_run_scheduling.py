### SMX_Automation_simulation_run, tailored for BLUE 12.5.1
### CFD scheduling, monitoring and post-processing script
### to be run locally
### Author: Juan Pablo Valdes,
### Contributors: Paula Pico, Fuyue Liang
### Version: 5.0
### First commit: July, 2023
### Department of Chemical Engineering, Imperial College London
#######################################################################################################################################################################################
#######################################################################################################################################################################################

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
import psutil
import glob
from datetime import datetime

############################################################################ EXCEPTION CLASSES  ###################################################################################

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

################################################################################### PARAMETRIC STUDY ################################################################################

################################################################################# Author: Juan Pablo Valdes #########################################################################

################################################################################# Tailored for SMX static mixer study ###############################################################

########################################################################################### PARENT CLASS ############################################################################

class SimScheduling:

    ### Init function
     
    def __init__(self) -> None:
        pass

    ### Constructor function to be initialized through localrun via psweep call

    def __construct__(self,pset_dict):

        ### Initialising class attributes
        self.pset_dict = pset_dict
        self.case_type = pset_dict['case']
        self.run_ID = pset_dict['run_ID']
        self.local_path = pset_dict['local_path']
        self.save_path = pset_dict['save_path']
        self.run_path = pset_dict['run_path']
        self.run_name = pset_dict['run_name']
        self.usr = pset_dict['user']

        self.save_path_runID = os.path.join(self.save_path,self.run_name)
        self.main_path = os.path.join(self.run_path,'..')

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

        ### constructor
        self.__construct__(pset_dict)

        ### Logger set-up
        log_filename = os.path.join(self.local_path,f"output_{self.case_type}/output_{self.run_name}.txt")
        log = self.set_log(log_filename)

        dict_str = json.dumps(self.pset_dict, default=self.convert_to_json, ensure_ascii=False)

        ### Exception return mapped by case type, to guarantee correct psweep completion
        return_from_casetype = {
            'sp_geom': {'L': 0, 'e_max': 0, 'Q': 0, 'E_diss': 0, 'Gamma': 0, 'Pressure': 0, 'Velocity': 0},
            'surf': {"Nd": 0, "DSD": 0, "IntA": 0},
            'geom' : {"Nd": 0, "DSD": 0, "IntA": 0}
                                }

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
            return return_from_casetype.get(self.case_type,{})
        except (ValueError, JobStatError, NameError) as e:
            log.info(f'Exited with message: {e}')
            return return_from_casetype.get(self.case_type,{})
            
        ### Job monitor and restarting nested loop. Checks job status and restarts if needed.

        restart = True
        while restart:

            ### job monitoring loop

            log.info('-' * 100)
            log.info('JOB MONITORING')
            log.info('-' * 100)

            try:
                self.jobmonitor(t_wait, status, jobid, self.run_ID, HPC_script,log)
            except (ValueError, NameError, ConvergenceError) as e:
                log.info(f'Exited with message: {e}')
                return return_from_casetype.get(self.case_type,{})
            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                log.info(f"SSH ERROR: Authentication failed: {e}")
                return return_from_casetype.get(self.case_type,{})

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

            except (ValueError,FileNotFoundError,NameError,BadTerminationError,JobStatError,TypeError,KeyError) as e:
                log.info(f'Exited with message: {e}')
                return return_from_casetype.get(self.case_type,{})
            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                log.info(f"SSH ERROR: Authentication failed: {e}")
                return return_from_casetype.get(self.case_type,{})

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
            return return_from_casetype.get(self.case_type,{})
        except (FileNotFoundError, JobStatError, ValueError, NameError) as e:
            log.info(f'Exited with message: {e}')
            return return_from_casetype.get(self.case_type,{})
        
        conv_name = 'Convert' + str(self.run_ID)

        ### job convert monitoring loop

        log.info('-' * 100)
        log.info('JOB MONITORING')
        log.info('-' * 100)

        try:
            self.jobmonitor(conv_t_wait,conv_status,conv_jobid,conv_name,HPC_script,log=log)
        except (ValueError, NameError) as e:
            log.info(f'Exited with message: {e}')
            return return_from_casetype.get(self.case_type,{})
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"SSH ERROR: Authentication failed: {e}")
            return return_from_casetype.get(self.case_type,{})

        ### Downloading files and local Post-processing

        log.info('-' * 100)
        log.info('DOWNLOADING FILES FROM EPHEMERAL')
        log.info('-' * 100)

        try:
            self.scp_download(log)
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"SSH ERROR: Authentication failed: {e}")
            return return_from_casetype.get(self.case_type,{})

        log.info('-' * 100)
        log.info('PVPYTHON POSTPROCESSING')
        log.info('-' * 100)

        # CSV backup saving file for post-processed variables
        csvbkp_file_path = os.path.join(self.local_path,'CSV_BKP',f'{self.case_type}.csv')

        ### Checking if a pvpython is operating on another process, if so sleeps.

        pvpyactive, pid = self.is_pvpython_running()

        while pvpyactive:
            log.info(f'pvpython is active in process ID : {pid}')
            sleep(600)
            pvpyactive, pid = self.is_pvpython_running()

        ### Exectuing post-processing instructions depending on single or two-phase case type
        if self.case_type == 'sp_geom':

            ### pvpython execution
            df_hyd = self.post_process_SP(log)

            if df_hyd is not None:
                L = df_hyd['Length']
                emax = df_hyd['e_max']
                Q = df_hyd['Q']
                ediss =  df_hyd['E_diss']
                gamma = df_hyd['Gamma']
                P = df_hyd['Pressure']
                u = df_hyd['Velocity']

                log.info('-' * 100)
                log.info('Post processing completed succesfully')
                log.info('-' * 100)
                log.info('Extracted relevant hydrodynamic data')

                df_hyd.insert(0,'Run', self.run_name)

                # Check if the CSV file already exists
                if not os.path.exists(csvbkp_file_path):
                    # If it doesn't exist, create a new CSV file with a header
                    df = pd.DataFrame({'Run_ID': [], 'Length': [], 'E_max': [], 
                                       'Q': [], 'E_diss': [], 'Gamma': [], 'Pressure': [], 'Velocity':[]})
                    df.to_csv(csvbkp_file_path, index=False)
                
                ### Append data to csvbkp file
                df_hyd.to_csv(csvbkp_file_path, mode='a', header= False, index=False)
                log.info('-' * 100)
                log.info(f'Saved backup post-process data successfully to {csvbkp_file_path}')
                log.info('-' * 100)

                return {'L': L, 'e_max':emax, 
                        'Q': Q, 'E_diss':ediss, 'Gamma': gamma, 
                        'Pressure': P, 'Velocity': u}

            else:
                log.info('Pvpython postprocessing failed, returning empty dictionary')
                return {'L': 0, 'e_max':0, 
                        'Q': 0, 'E_diss':0, 'Gamma': 0, 
                        'Pressure': 0, 'Velocity': 0}

        else:

            ### pvpython execution
            dfDSD, IntA = self.post_process(log)

            if dfDSD is not None:

                Nd = dfDSD.size

                df_scalar = pd.DataFrame({'Run':[self.run_name],'IA': [IntA], 'Nd': [Nd]})
                df_drops = pd.concat([df_scalar,dfDSD], axis = 1)


                log.info('-' * 100)
                log.info('Post processing completed succesfully')
                log.info('-' * 100)
                log.info(f'Number of drops in this run: {Nd}')
                log.info(f'Drop size dist. {dfDSD}')
                log.info(f'Interfacial Area : {IntA}')

                # Check if the CSV file already exists
                if not os.path.exists(csvbkp_file_path):
                    # If it doesn't exist, create a new CSV file with a header
                    df = pd.DataFrame({'Run_ID': [], 'Interfacial Area': [], 'Number of Drops': [], 
                                        'DSD': []})
                    df.to_csv(csvbkp_file_path, index=False)
                
                ### Append data to csvbkp file
                df_drops.to_csv(csvbkp_file_path, mode='a', header= False, index=False)
                log.info('-' * 100)
                log.info(f'Saved backup post-process data successfully to {csvbkp_file_path}')
                log.info('-' * 100)

                
                return {"Nd":Nd, "DSD":dfDSD, "IntA":IntA}
            else:
                log.info('Pvpython postprocessing failed, returning empty dictionary')
                return{"Nd":0, "DSD":0, "IntA":0}
    
    ### calling monitoring and restart function to check in on jobs

    def jobmonitor(self, t_wait, status, jobid, run, HPC_script,log):

        running = True
        chk_counter = 0
        csv_check = False # Option to deactivate csv checks and only run qstat
        
        while running:
            
            ### Setting updated dictionary with jobid from submitted job and csv_check logical gate
            mdict = self.pset_dict
            mdict['jobID'] = jobid
            mdict['check'] = csv_check
            mdict_str = json.dumps(mdict, default=self.convert_to_json, ensure_ascii=False)
                        
            ### If t_wait>0, job is either running or queieng
            if t_wait>0:

            ### Performing monitoring and waiting processes depending on job status and type
                if (status == 'Q' or status == 'H' or (status == 'R' and 'Convert' in run)):
                    ### If Q or H, wait and qstat later
                    log.info('-' * 100)
                    log.info(f'Job {run} with id: {jobid} has status {status}. Sleeping for:{t_wait/60} mins')
                    log.info('-' * 100)
                    sleep(t_wait)
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
                    except (JobStatError, ValueError, NameError) as e:  
                        if isinstance(e, JobStatError):

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
                    ### Status here is R and not jobconvert, performing convergence checks in HPC monitor
                    n_checks = 16 # has to be larger than 0
                    log.info('-' * 100)
                    log.info(f'Job {run} with id: {jobid} has status {status}. Currently on check {chk_counter} out of {n_checks} checks during runtime.')
                    log.info('-' * 100)

                    ### Initializing run_t_wait with initial run time extracted
                    if chk_counter == 0:
                        run_t_wait = t_wait
                        log.info('-' * 100)
                        log.info('First check to be performed')

                    ### Sleep extra after last check to guarantee job has finished at the end
                    if run_t_wait > (t_wait)/(n_checks+1):
                        log.info('-' * 100)
                        log.info(f'Sleeping for {t_wait/(n_checks+1)/60} mins until next check')
                        sleep(t_wait/(n_checks+1))
                    else:
                        log.info('-' * 100)
                        log.info(f'Final check done, sleeping for {run_t_wait/60} mins until completion')
                        sleep((t_wait/(n_checks+1))* 1.05)

                    try:
                        ### Execute monitor function in HPC to check job status
                        command = f'python {self.main_path}/{HPC_script} monitor --pdict \'{mdict_str}\''
                        _, run_t_wait, run_status, _ = self.execute_remote_command(
                            command=command,search=0,log=log
                            )
                        
                        status = run_status
                        chk_counter += 1

                        log.info('-' * 100)
                        log.info(f'Run time remaining: {run_t_wait/60} mins')

                        log.info('-' * 100)
                        log.info(f'Job {run} with id {jobid} status is {status}. Continuing checks')
                    except (JobStatError, ValueError, NameError, ConvergenceError) as e:  
                        if isinstance(e, JobStatError):

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
        configfile = os.path.join(self.local_path, f'config_{self.usr}.ini')
        config.read(configfile)
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
                    if exc == "JobStatError":
                        raise JobStatError('qstat output empty, job finished or deleted from HPC run queue')
                    elif exc == "ValueError":
                        raise ValueError('Exception raised from job sh creation, qstat in job_wait \
                                         or attempting to search restart in job_restart')
                    elif exc == "FileNotFoundError":
                        raise FileNotFoundError('File not found: either .out or .csv files not found when attempting restart \
                                                or vtk/pvd/convert files not found when attempting to convert')
                    elif exc == "ConvergenceError":
                        raise ConvergenceError('Convergence checks on HPC failed, job killed as a result')
                    elif exc == "BadTerminationError":
                        raise BadTerminationError("Job run ended with a bad termination error message in the output file. Check convergence or setup issues")
                    elif exc == 'KeyError':
                        raise KeyError('Error while attempting to restart: Stop condition key name does not exist in the CSV file checked')
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
                "====RETURN_BOOL====": "ret_bool",
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

        ephemeral_path = f'/rds/general/user/{self.usr}/ephemeral/'

        try:
            os.mkdir(self.save_path_runID)
            log.info(f'Saving folder created at {self.save_path}')
        except:
            pass

        ### Config file with keys to login to the HPC
        config = configparser.ConfigParser()
        configfile = os.path.join(self.local_path, f'config_{self.usr}.ini')
        config.read(configfile)
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

    ### Post-processing function for two-phase cases extracting relevant outputs from sim's final timestep.

    def post_process(self,log):

        ### Extracting Interfacial Area from CSV
        os.chdir(self.save_path_runID) 
        pvdfiles = glob.glob('VAR_*_time=*.pvd')
        maxpvd_tf = max(float(filename.split('=')[-1].split('.pvd')[0]) for filename in pvdfiles)

        df_csv = pd.read_csv(os.path.join(self.save_path_runID,f'{self.run_name}.csv' if os.path.exists(f'{self.run_name}.csv') else f'HST_{self.run_name}.csv'))
        df_csv['diff'] = abs(df_csv['Time']-maxpvd_tf)
        log.info('Reading data from csv')
        log.info('-'*100)

        tf_row = df_csv.sort_values(by='diff')

        IntA = tf_row.iloc[0]['INTERFACE_SURFACE_AREA']
        log.info('Interfacial area extracted')
        log.info('-'*100)

        os.chdir(self.local_path)

        ### Running pvpython script for Nd and DSD
        script_path = os.path.join(self.local_path,'PV_scripts/PV_ndrop_DSD.py')

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
        except ValueError as e:
            log.info(f'ValueError, Exited with message: {e}')
            df_DSD = None

        return df_DSD, IntA
    
    ### Post-processing function for single-phase cases extracting relevant outputs from sim's final timestep.

    def post_process_SP(self,log):

        ### Attributes not defined in class constructor as they are case-specific
        self.n_ele = self.pset_dict['n_ele']
        self.pipe_radius = self.pset_dict['pipe_radius']
        domain_length = (1 + float(self.n_ele))*float(self.pipe_radius)*2

        ### Running pvpython script for Nd and DSD
        script_path = os.path.join(self.local_path,'PV_scripts/PV_sp_PP.py')

        log.info('-'*100)
        log.info('Executing pvpython script')
        log.info('-'*100)

        try:
            output = subprocess.run(['pvpython', script_path, self.save_path , self.run_name, str(domain_length), str(self.pipe_radius)], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            captured_stdout = output.stdout.decode('utf-8').strip().split('\n')
            outlines= []
            for i, line in enumerate(captured_stdout):
                stripline = line.strip()
                outlines.append(stripline)
                if i < len(captured_stdout) - 1:
                    log.info(stripline)
            
            df_hyd = pd.read_json(outlines[-1], orient='split', dtype=float, precise_float=True)

        except subprocess.CalledProcessError as e:
            log.info(f"Error executing the script with pvpython: {e}")
            return None 
        except FileNotFoundError:
            log.info("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")
            return None
        except ValueError as e:
            log.info(f'ValueError, Exited with message: {e}')
            return None


        return df_hyd

################################################################################################################################################################################

################################################################################### JOB MONITORING ###########################################################################

################################################################################# Author: Paula Pico #########################################################################

################################################################################# General Application for BLUE 12 onwards #####################################################

########################################################################################### CHILD CLASS ############################################################################
class SimMonitoring(SimScheduling):
    
    ### Init function
     
    def __init__(self,pset_dict) -> None:
        
        ### Initialising class attributes
        self.pset_dict = pset_dict
        self.local_path = pset_dict['local_path']
        self.save_path = pset_dict['save_path']
        self.save_path_csv = pset_dict['save_path_csv']
        self.run_path = pset_dict['run_path']
        self.jobID = pset_dict['jobID']
        self.run_name = pset_dict['run_name']
        self.run_ID = pset_dict['run_ID']
        self.usr = pset_dict['user']

        self.main_path = os.path.join(self.run_path,'..')
        self.path = os.path.join(self.run_path)

    ### Local monitoring of existing jobs in HPC and performing overall BLUE workflow
    
    def localmonitor(self,pset_dict):

        ### Logger set-up
        log_filename = f"output_{self.run_name}.txt"
        log = self.set_log(log_filename)
        dict_str = json.dumps(pset_dict, default=self.convert_to_json, ensure_ascii=False)

        HPC_script = 'HPC_run_scheduling.py'

        ##Initial values
        t_wait = 1
        status = 'I'
        jobid = self.jobID

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
            log.info('DOWNLOADING .csv FILE')
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
                log.info(f"Authentication failed: {e}")
                return {}
            
    ### Function to copy the csv file. To be executed at the end of every run

    def copy_csv(self,log):

        ephemeral_path = f'/rds/general/user/{self.usr}/ephemeral/'

        ### Config file with keys to login to the HPC
        config = configparser.ConfigParser()
        configfile = os.path.join(self.local_path, f'config_{self.usr}.ini')
        config.read(configfile)
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
                remote_path = os.path.join(ephemeral_path,self.run_name)
                remote_files = sftp.listdir(remote_path)

                # Trying to Find .csv file in EPHEMERAL
                try:
                    remote_files = sftp.listdir(remote_path)
                    csv_files = [file for file in remote_files if 
                                 file.endswith(f'{self.run_name}.csv' 
                                               if os.path.exists(f'{self.run_name}.csv') else f'HST_{self.run_name}.csv')]

                    # If csv is found. Create a directory named with current date in "temporal", copy the csv there and rename it to: *_{today_date}.csv
                    if csv_files:
                        log.info('-' * 100)
                        log.info(f"*.csv file found in remote directory")
                        log.info('-' * 100)
                        today_date = datetime.now().strftime("%d%m%y")
                        target_directory = os.path.join(self.save_path_csv, today_date)
                        os.makedirs(target_directory, exist_ok=True)
                        log.info(f"Directory {today_date} created")

                        for csv_file in csv_files:
                            new_csv_file_name = f"{os.path.splitext(csv_file)[0]}_{today_date}.csv"
                            remote_file_path = os.path.join(remote_path, csv_file)
                            local_file_path = os.path.join(target_directory, new_csv_file_name)
                            sftp.get(remote_file_path, local_file_path)
                            log.info(f"File {new_csv_file_name} copied and renamed")
                    else:
                        # If no csv file is found. Continue with the job restarting process and issue a warning
                        log.info('-' * 100)
                        log.info("WARNING: No csv files found to copy. Simulation will be restarted but please check")
                        log.info('-' * 100)
                finally:
                    log.info('-' * 100)
                    log.info("Restarting process will begin")
                    log.info('-' * 100)

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

################################################################################### PARAMETRIC STUDY ################################################################################

################################################################################# Author: Fuyue Liang #########################################################################

################################################################################# Tailored for stirred mixer study ###############################################################

########################################################################################### CHILD CLASS ############################################################################

class SVSimScheduling(SimScheduling):

    ### Ini Function ###
    def __init__(self) -> None:
        pass

    ### Constructor function to be initilized through localrun via psweep call ###
    def __construct__(self, pset_dict):
        ### Initialising class attributes ###
        self.pset_dict = pset_dict
        self.case_type = pset_dict['case']
        self.run_ID = pset_dict['run_ID']
        self.local_path = pset_dict['local_path']
        self.save_path = pset_dict['save_path']
        self.run_path = pset_dict['run_path']
        self.run_name = pset_dict['run_name']
        self.usr = pset_dict['user']
        self.vtk_conv_mode = pset_dict['vtk_conv_mode']

        self.save_path_runID = os.path.join(self.save_path,self.run_name)
        self.main_path = os.path.join(self.run_path,'..')
        
    
    def localrun(self, pset_dict):
        ### constructor ###
        self.__construct__(pset_dict)

        ### Logger setup ###
        log_filename = os.path.join(self.local_path,f"output_{self.case_type}/output_{self.run_name}.txt")
        log = self.set_log(log_filename)

        # convert the dictionary to strings for HPC
        dict_str = json.dumps(self.pset_dict, default=self.convert_to_json, ensure_ascii=False)

        ### Exception return mapped by case type, to guarantee correct psweep completion ###
        return_from_casetype = {
            'svsurf': {"Time": 0,"Nd": 0, "DSD": 0, "IntA": 0},
            'svgeom': {"Time": 0,"Nd": 0, "DSD": 0, "IntA": 0},
            'sp_svgeom':{"Time":0,
                        "Height":0,"Q":0,"Pres":0,
                        "Ur": 0, "Uth":0, "Uz":0,
                        "arc_length":0,"Q_over_line":0, 
                        "Ur_over_line":0,"Uz_over_line":0}
        }

        ### First job creation and submission ###

        HPC_script = 'HPC_run_scheduling.py'

        log.info('-' * 100)
        log.info('-' * 100)
        log.info('NEW RUN')
        log.info('-' * 100)
        log.info('-' * 100)

        ### wait time to connect at first, avoiding multiple simultaneuous connection ###
        init_wait_time = np.random.RandomState().randint(0,180)
        sleep(init_wait_time)

        try:
            command = f"python {self.main_path}/{HPC_script} run --pdict \'{dict_str}\'"
            jobid, t_wait, status, _ = self.execute_remote_command(command=command,search=0,log=log)
        except (paramiko.AuthenticationException,paramiko.SSHException) as e:
            log.info(f'SSH EEROR: Authentication failed: {e}')
            return return_from_casetype.get(self.case_type, {})
        except (ValueError, JobStatError, NameError) as e:
            log.info(f'Exited with message: {e}')
            return return_from_casetype.get(self.case_type,{})
        
        ### Job monitor and restart nested loop ###
        ### Checks job status and restarts if needed ###

        restart = True
        while restart:
            ### job monitoring loop ###
            log.info('-' * 100)
            log.info('JOB MONITORING')
            log.info('-' * 100) 

            try:
                self.jobmonitor(t_wait, status, jobid, self.run_ID, HPC_script,log)
            except (ValueError, NameError, ConvergenceError) as e:
                log.info(f'Exited with message: {e}')
                return return_from_casetype.get(self.case_type,{})
            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                log.info(f"SSH ERROR: Authentication failed: {e}")
                return return_from_casetype.get(self.case_type,{})

            ### Job restart execution ###
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

            except (ValueError,FileNotFoundError,NameError,BadTerminationError,JobStatError,TypeError,KeyError) as e:
                log.info(f'Exited with message: {e}')
                return return_from_casetype.get(self.case_type,{})
            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                log.info(f"SSH ERROR: Authentication failed: {e}")
                return return_from_casetype.get(self.case_type,{})

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
            return return_from_casetype.get(self.case_type,{})
        except (FileNotFoundError, JobStatError, ValueError, NameError) as e:
            log.info(f'Exited with message: {e}')
            return return_from_casetype.get(self.case_type,{})
        
        conv_name = 'Convert' + str(self.run_ID)

        ### job convert monitoring loop ###

        log.info('-' * 100)
        log.info('JOB MONITORING')
        log.info('-' * 100)

        try:
            self.jobmonitor(conv_t_wait,conv_status,conv_jobid,conv_name,HPC_script,log=log)
        except (ValueError, NameError) as e:
            log.info(f'Exited with message: {e}')
            return return_from_casetype.get(self.case_type,{})
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"SSH ERROR: Authentication failed: {e}")
            return return_from_casetype.get(self.case_type,{})

        ### Downloading files and local Post-processing

        log.info('-' * 100)
        log.info('DOWNLOADING FILES FROM EPHEMERAL')
        log.info('-' * 100)

        try:
            self.scp_download(log)
            # log.info('Skipping downloading')
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"SSH ERROR: Authentication failed: {e}")
            return return_from_casetype.get(self.case_type,{})

        log.info('-' * 100)
        log.info('PVPYTHON POSTPROCESSING')
        log.info('-' * 100)

        ### csv backup saving file for post-processed variables ###
        csvbkp_file_path = os.path.join(self.local_path,'CSV_BKP',f'{self.case_type}.csv')

        ### checking if a pvpython is operating on another process, if so sleeps ###
        pvpyactive, pid = self.is_pvpython_running()

        while pvpyactive:
            log.info(f'pvpython is active in process ID: {pid}')
            sleep(1800)
            pvpyactive,pid =self.is_pvpython_running()

        ### pvpython execution ###
        if self.vtk_conv_mode == 'last':
            log.info(f'{self.vtk_conv_mode} post-processing is starting.')
            if self.case_type == 'sp_svgeom':
                df_sp, maxtime = self.post_process_lastsp(log)
                if df_sp is not None:
                    df_hyd = pd.DataFrame({'Run':self.run_name,'Time':maxtime,
                                          'Height':df_sp['Height'],'Q':df_sp['Q'],'Pres':df_sp['Pressure'],
                                          'Ur': df_sp['Ur'], 'Uth':df_sp['Uth'], 'Uz':df_sp['Uz'],
                                          'arc_length':df_sp['arc_length'],'Q_over_line':df_sp['Q_over_line'], 
                                          'Ur_over_line':df_sp['Ur_over_line'],'Uz_over_line':df_sp['Uz_over_line']
                    })

                    log.info('-' * 100)
                    log.info('Post processing completed succesfully')
                    log.info('-' * 100)
                    log.info('Extracted flow features')
                    log.info(f'{df_sp}')

                    # check if the CSV file already exits
                    if not os.path.exists(csvbkp_file_path):
                        # If it doesn't exist, create a new CSV with headers #
                        df = pd.DataFrame({'Run':[],'Time':[],
                                          'Height':[],'Q':[],'Pres':[],
                                          'Ur': [], 'Uth':[], 'Uz':[],
                                          'arc_length':[],'Q_over_line':[], 
                                          'Ur_over_line':[],'Uz_over_line':[]
                        })
                        df.to_csv(csvbkp_file_path, index=False)
                    
                    # Append data to csvbkp file
                    df_hyd.to_csv(csvbkp_file_path, mode='a', header= False, index=False)
                    log.info('-' * 100)
                    log.info(f'Saved backup post-process data successfully to {csvbkp_file_path}')
                    log.info('-' * 100)

                    return {"Time":maxtime,
                            "Height":df_sp['Height'],"Q":df_sp['Q'],"Pres":df_sp['Pressure'],
                            "Ur": df_sp['Ur'], "Uth":df_sp['Uth'], "Uz":df_sp['Uz'],
                            "arc_length":df_sp['arc_length'],"Q_over_line":df_sp['Q_over_line'], 
                            "Ur_over_line":df_sp['Ur_over_line'],"Uz_over_line":df_sp['Uz_over_line']
                            }
                
                else:
                    log.info('Pvpython postprocessing failed, returning empty dictionary')
                    return {"Time":0,
                            "Height":0,"Q":0,"Pres":0,
                            "Ur": 0, "Uth":0, "Uz":0,
                            "arc_length":0,"Q_over_line":0, 
                            "Ur_over_line":0,"Uz_over_line":0}

            else: 
                dfDSD, IntA, maxtime = self.post_process_last(log)
                if dfDSD is not None:

                    df_drops = pd.DataFrame({'Run':self.run_name,
                                            'Time': maxtime,'IntA': IntA, 
                                            'Nd': dfDSD['Nd'], 'DSD': dfDSD['Volume']})

                    log.info('-' * 100)
                    log.info('Post processing completed succesfully')
                    log.info('-' * 100)
                    log.info(f'Drop size dist and Nd in this run at time {maxtime}[s]:')
                    log.info(f'{dfDSD}')
                    log.info(f'Interfacial Area : {IntA}')

                    # Check if the CSV file already exists
                    if not os.path.exists(csvbkp_file_path):
                        # If it doesn't exist, create a new CSV file with a header
                        df = pd.DataFrame({'Run': [], 
                                        'Time': [], 'IntA': [], 'Nd': [], 'DSD': []})
                        df.to_csv(csvbkp_file_path, index=False)
                    
                    ### Append data to csvbkp file
                    df_drops.to_csv(csvbkp_file_path, mode='a', header= False, index=False)
                    log.info('-' * 100)
                    log.info(f'Saved backup post-process data successfully to {csvbkp_file_path}')
                    log.info('-' * 100)

                    return {"Time": maxtime, "IntA":IntA, "Nd":dfDSD['Nd'], "DSD":dfDSD['Volume']}
                
                else:
                    log.info('Pvpython postprocessing failed, returning empty dictionary')
                    return{"Time":0, "Nd":0, "DSD":0, "IntA":0}
            
        else:
            dfDSD, IntA, maxtime = self.post_process_last(log)
            if dfDSD is not None:

                df_drops = pd.DataFrame({'Run':self.run_name,
                                        'Time': maxtime,'IntA': IntA, 
                                        'Nd': dfDSD['Nd'], 'DSD': dfDSD['Volume']})

                log.info('-' * 100)
                log.info('Post processing completed succesfully')
                log.info('-' * 100)
                log.info(f'Drop size dist and Nd in this run at time {maxtime}[s]:')
                log.info(f'{dfDSD}')
                log.info(f'Interfacial Area : {IntA}')

                # Check if the CSV file already exists
                if not os.path.exists(csvbkp_file_path):
                    # If it doesn't exist, create a new CSV file with a header
                    df = pd.DataFrame({'Run': [], 
                                    'Time': [], 'IntA': [], 'Nd': [], 'DSD': []})
                    df.to_csv(csvbkp_file_path, index=False)
                
                ### Append data to csvbkp file
                df_drops.to_csv(csvbkp_file_path, mode='a', header= False, index=False)
                log.info('-' * 100)
                log.info(f'Saved backup post-process data successfully to {csvbkp_file_path}')
                log.info('-' * 100)

                return {"Time": maxtime, "IntA":IntA, "Nd":dfDSD['Nd'], "DSD":dfDSD['Volume']}
            
            else:
                log.info('Pvpython postprocessing failed, returning empty dictionary')
                return{"Time":0, "Nd":0, "DSD":0, "IntA":0}
            # df_join = self.post_process_all(log)

            # if df_join is not None:
        
            #     df_drops = pd.DataFrame({'Run':self.run_name, 
            #                              'Time':df_join['Time'], 'IntA':df_join['IntA'], 
            #                              'Nd':df_join['Nd'], 'DSD':df_join['Volumes']
            #                              })
                
            #     log.info('-' * 100)
            #     log.info('Post processing completed succesfully')
            #     log.info('-' * 100)
            #     log.info('Results for the last 10 time steps in this run:')
            #     log.info(f'{df_drops[:10]}')

            # # Check if the CSV file already exists
            #     if not os.path.exists(csvbkp_file_path):
            #         # If it doesn't exist, create a new CSV file
            #         df = pd.DataFrame({'Run':[],
            #                            'Time':[], 'IntA':[], 'Nd':[], 'DSD':[]})
            #         df.to_csv(csvbkp_file_path, index=False)
                
            #     ### Append data to csvbkp file
            #     df_drops.to_csv(csvbkp_file_path, mode='a', header= False, index=False)
            #     log.info('-' * 100)
            #     log.info(f'Saved backup post-process data successfully to {csvbkp_file_path}')
            #     log.info('-' * 100)

            #     return {"Time":df_join['Time'], "IntA":df_join['IntA'], "Nd":df_join['Nd'], "DSD":df_join['Volumes']}
            
            # else:
            #     log.info('Pvpython postprocessing failed, returning empty dictionary')
            #     return {"Time":0, "IntA":0, "Nd":0, "DSD":0}

    def post_process_lastsp(self,log):
        # get the final time #
        os.chdir(self.save_path_runID)
        pvdfiles = glob.glob('VAR_*_time=*.pvd')
        maxpvd_tf = max(float(filename.split('=')[-1].split('.pvd')[0]) for filename in pvdfiles)
        
        os.chdir(self.local_path)
        # Attributes needed for single phase post processing # 
        self.C = self.pset_dict['clearance']

        ### Running pvpython script for single phases ###
        script_path = os.path.join(self.local_path, 'PV_scripts/PV_sv_sp.py')
        log.info('Executing pvpython script')
        log.info('-' * 100)

        try:
            output = subprocess.run(['pvpython', script_path, self.save_path, self.run_name, str(self.C)], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            captured_stdout = output.stdout.decode('utf-8').strip().split('\n')
            outlines= []
            for i, line in enumerate(captured_stdout):
                stripline = line.strip()
                outlines.append(stripline)
                if i < len(captured_stdout) - 1:
                    log.info(stripline)

            df_sp = pd.read_json(outlines[-1], orient='split', dtype=float, precise_float=True)

        except subprocess.CalledProcessError as e:
            log.info(f"Error executing the script with pvpython: {e}")
            df_sp = None
        except FileNotFoundError:
            log.info("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")
            df_sp = None
        except ValueError as e:
            log.info(f'ValueError, Exited with message: {e}')
            df_sp =  None

        return df_sp, maxpvd_tf

    def post_process_last(self, log):
        ### Extracting Interfacial Area from csv###
        os.chdir(self.save_path_runID)
        pvdfiles = glob.glob('VAR_*_time=*.pvd')
        maxpvd_tf = max(float(filename.split('=')[-1].split('.pvd')[0]) for filename in pvdfiles)

        df_csv = pd.read_csv(os.path.join(self.save_path_runID,f'{self.run_name}.csv' if os.path.exists(f'{self.run_name}.csv') else f'HST_{self.run_name}.csv'))
        df_csv['diff'] = abs(df_csv['Time']-maxpvd_tf)
        log.info('Reading data from csv')
        log.info('-'*100)

        tf_row = df_csv.sort_values(by='diff')

        IntA = tf_row.iloc[0]['INTERFACE_SURFACE_AREA']
        log.info('Interfacial area extracted')
        log.info('-'*100)

        os.chdir(self.local_path)
        ### Running pvpython script for Nd and DSD ###
        script_path = os.path.join(self.local_path,'PV_scripts/PV_sv_last.py')

        log.info('Executing pvpython script')
        log.info('-' * 100)

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
        except ValueError as e:
            log.info(f'ValueError, Exited with message: {e}')
            df_DSD = None

        return df_DSD, IntA, maxpvd_tf
    
    def post_process_all(self, log):
        ### Extracting Interfacial Area from CSV ###
        os.chdir(self.save_path_runID)
        
        df_csv = pd.read_csv(os.path.join(self.save_path_runID, f'{self.run_name}.csv'
                                          if os.path.exists(f'{self.run_name}.csv') 
                                          else f'HST_{self.run_name}.csv'))
        pvdfiles = glob.glob('VAR_*_time=*.pvd')
        times = sorted([float(filename.split('=')[-1].split('.pvd')[0]) for filename in pvdfiles])
        maxtime = max(times)

        ints_list = []
        for t in times:
            therow = df_csv[df_csv['Time']==t]
            value_to_add = {'Time': t, 'IntA': therow['INTERFACE_SURFACE_AREA'].values}
            ints_list.append(value_to_add)
        df_ints = pd.DataFrame(ints_list, columns=['Time', 'IntA'])
        log.info(f'Interfacial Area up to {maxtime}[s] extracted.')
        log.info('-' * 100)

        ### Running pvpython script for Nd and DSD ###
        os.chdir(self.local_path)
        script_path = os.path.join(self.local_path,'PV_scripts/PV_sv_all.py')
        log.info('Executing pvpython script')
        log.info('-' * 100)

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
            df_join = pd.merge(df_ints, df_DSD, on='Time', how='left')

        except subprocess.CalledProcessError as e:
            log.info(f"Error executing the script with pvpython: {e}")
            df_join = None
        except FileNotFoundError:
            log.info("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")
            df_join = None
        except ValueError as e:
            log.info(f'ValueError, Exited with message: {e}')
            df_join = None

        return df_join
