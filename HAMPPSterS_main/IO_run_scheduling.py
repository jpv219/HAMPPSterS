### IO_Automation_simulation_run, tailored for BLUE 14.0.1
### CFD scheduling, monitoring and post-processing script
### to be run locally
### Author: Paula Pico,
### Contributors: Juan Pablo Valdes, Fuyue Liang
### Version: 5.0
### First commit: December, 2023
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
from CFD_run_scheduling import SimScheduling

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

################################################################################# Author: Paula Pico #########################################################################

################################################################################# Tailored for interfacial oscilations ###############################################################

########################################################################################### CHILD CLASS ############################################################################

class IOSimScheduling(SimScheduling):

    ### Init Function ###
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

        self.save_path_runID = os.path.join(self.save_path,self.run_name)
        self.save_path_runID_post = os.path.join(self.save_path_runID,'postProcessing')
        self.main_path = os.path.join(self.run_path,'..')

    ### Download final converted data to local processing machine. Creates an internal directory, 'postProcessing', where data files are stored locally
        
    def scp_download(self,log):

        ephemeral_path = f'/rds/general/user/{self.usr}/ephemeral/'

        try:
            os.mkdir(self.save_path_runID)
            os.mkdir(self.save_path_runID_post)
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
                    local_file_path = os.path.join(self.save_path_runID_post, file_attr.filename)

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

    def localrun(self,pset_dict):

        ### constructor ###
        self.__construct__(pset_dict)

        ### Logger setup ###
        log_filename = os.path.join(self.local_path,f"output_{self.case_type}/output_{self.run_name}.txt")
        log = self.set_log(log_filename)

        # convert the dictionary to strings for HPC
        dict_str = json.dumps(self.pset_dict, default=self.convert_to_json, ensure_ascii=False)

        ### First job creation and submission ###

        HPC_script = 'HPC_run_scheduling.py'

        log.info('-' * 100)
        log.info('-' * 100)
        log.info('NEW RUN')
        log.info('-' * 100)
        log.info('-' * 100)

        ### wait time to connect at first, avoiding multiple simultaneuous connection ###
        #init_wait_time = np.random.RandomState().randint(0,180)
        #sleep(init_wait_time)

        try:
            command = f"python {self.main_path}/{HPC_script} run --pdict \'{dict_str}\'"
            jobid, t_wait, status, _ = self.execute_remote_command(command=command,search=0,log=log)
        except (paramiko.AuthenticationException,paramiko.SSHException) as e:
            log.info(f'SSH EEROR: Authentication failed: {e}')
            return {}
        except (ValueError, JobStatError, NameError) as e:
            log.info(f'Exited with message: {e}')
            return {}
        
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
                return {}
            except (paramiko.AuthenticationException, paramiko.SSHException) as e:
                log.info(f"SSH ERROR: Authentication failed: {e}")
                return {}

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
        except (FileNotFoundError, JobStatError, ValueError, NameError) as e:
            log.info(f'Exited with message: {e}')
            return {}
        
        conv_name = 'Convert' + str(self.run_ID)

        ### job convert monitoring loop ###

        log.info('-' * 100)
        log.info('JOB MONITORING')
        log.info('-' * 100)

        try:
            self.jobmonitor(conv_t_wait,conv_status,conv_jobid,conv_name,HPC_script,log=log)
        except (ValueError, NameError) as e:
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
            # log.info('Skipping downloading')
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"SSH ERROR: Authentication failed: {e}")
            return {}
    
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

        ### Exectuing post-processing instructions depending on clean or surfactant case type
        if self.case_type == 'osc_clean':

            ### pvpython execution
            dfak0 = self.post_process_ak0(log)
            dfak1 = self.post_process_ak1(log)
            dfak2 = self.post_process_ak2(log)
            dfak3 = self.post_process_ak3(log)
            dfintarea = self.post_process_int_area(log)
            dfEk = self.post_process_Ek(log)

            if dfak0 is not None and dfak1 is not None and dfak2 is not None and dfintarea is not None and dfEk is not None:
                df_run = pd.DataFrame({'Run':[self.run_name]})
                df_run = pd.concat([df_run] * len(dfak0), ignore_index=True)
                df_compiled = pd.concat([df_run,dfak0,dfak1["ak1"],dfak2["ak2"],dfak3["ak3"],dfintarea["Int_area"],dfEk["Ek"]], axis = 1)

                log.info('-' * 100)
                log.info('Post processing completed succesfully')
                log.info('-' * 100)
                log.info('Extracted relevant hydrodynamic data')

                # Check if the CSV file already exists
                if not os.path.exists(csvbkp_file_path):
                    # If it doesn't exist, create a new CSV file with a header
                    df = pd.DataFrame({'Run_ID': [], 'Time': [], 'ak0': [], 'ak1': [], 'ak2': [], 'ak3': [], 'Int_area' : [], 'Ek_half' : []})
                    df.to_csv(csvbkp_file_path, index=False)

                ### Append data to csvbkp file
                df_compiled.to_csv(csvbkp_file_path, mode='a', header= False, index=False)
                print('-' * 100)
                print(f'Saved backup post-process data successfully to {csvbkp_file_path}')
                print('-' * 100)
            
            else:
                print(f'Pvpython postprocessing failed for {self.run_name}.')
                return {}
                
        return {}

    def post_process_ak0(self,log):

        script_path = os.path.join(self.local_path,'PV_scripts/PV_io_ak0.py')
        log.info('Executing pvpython script to calculate ak0')
        log.info('-' * 100)

        try:
            output = subprocess.run(['pvpython', script_path, self.save_path , self.run_name], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            captured_stdout = output.stdout.decode('utf-8').strip().split('\n')

            outlines = []
            
            for i, line in enumerate(captured_stdout):
                stripline = line.strip()
                outlines.append(stripline)
                if i < len(captured_stdout) - 1:
                    print(stripline)

            df = pd.read_json(outlines[-1], dtype=float, precise_float=True)
            df_expanded = df.apply(pd.Series.explode)
            df_expanded = df_expanded.reset_index(drop=True)

        except subprocess.CalledProcessError as e:
            print(f"Error executing the script with pvpython: {e}")
            df_expanded = None
        except FileNotFoundError:
            print("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")
            df_expanded = None
        except ValueError as e:
            print(f'ValueError, Exited with message: {e}')
            df_expanded = None

        return df_expanded
    
    def post_process_ak1(self,log):

        script_path = os.path.join(self.local_path,'PV_scripts/PV_io_ak1.py')
        log.info('Executing pvpython script to calculate ak1')
        log.info('-' * 100)

        try:
            output = subprocess.run(['pvpython', script_path, self.save_path , self.run_name], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            captured_stdout = output.stdout.decode('utf-8').strip().split('\n')

            outlines = []
            
            for i, line in enumerate(captured_stdout):
                stripline = line.strip()
                outlines.append(stripline)
                if i < len(captured_stdout) - 1:
                    print(stripline)

            df = pd.read_json(outlines[-1], dtype=float, precise_float=True)
            df_expanded = df.apply(pd.Series.explode)
            df_expanded = df_expanded.reset_index(drop=True)

        except subprocess.CalledProcessError as e:
            print(f"Error executing the script with pvpython: {e}")
            df_expanded = None
        except FileNotFoundError:
            print("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")
            df_expanded = None
        except ValueError as e:
            print(f'ValueError, Exited with message: {e}')
            df_expanded = None

        return df_expanded

    def post_process_ak2(self,log):

        script_path = os.path.join(self.local_path,'PV_scripts/PV_io_ak2.py')
        log.info('Executing pvpython script to calculate ak2')
        log.info('-' * 100)

        try:
            output = subprocess.run(['pvpython', script_path, self.save_path , self.run_name], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            captured_stdout = output.stdout.decode('utf-8').strip().split('\n')

            outlines = []
            
            for i, line in enumerate(captured_stdout):
                stripline = line.strip()
                outlines.append(stripline)
                if i < len(captured_stdout) - 1:
                    print(stripline)

            df = pd.read_json(outlines[-1], dtype=float, precise_float=True)
            df_expanded = df.apply(pd.Series.explode)
            df_expanded = df_expanded.reset_index(drop=True)

        except subprocess.CalledProcessError as e:
            print(f"Error executing the script with pvpython: {e}")
            df_expanded = None
        except FileNotFoundError:
            print("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")
            df_expanded = None
        except ValueError as e:
            print(f'ValueError, Exited with message: {e}')
            df_expanded = None

        return df_expanded

    def post_process_ak3(self,log):

        script_path = os.path.join(self.local_path,'PV_scripts/PV_io_ak3.py')
        log.info('Executing pvpython script to calculate ak1')
        log.info('-' * 100)

        try:
            output = subprocess.run(['pvpython', script_path, self.save_path , self.run_name], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            captured_stdout = output.stdout.decode('utf-8').strip().split('\n')

            outlines = []
            
            for i, line in enumerate(captured_stdout):
                stripline = line.strip()
                outlines.append(stripline)
                if i < len(captured_stdout) - 1:
                    print(stripline)

            df = pd.read_json(outlines[-1], dtype=float, precise_float=True)
            df_expanded = df.apply(pd.Series.explode)
            df_expanded = df_expanded.reset_index(drop=True)

        except subprocess.CalledProcessError as e:
            print(f"Error executing the script with pvpython: {e}")
            df_expanded = None
        except FileNotFoundError:
            print("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")
            df_expanded = None
        except ValueError as e:
            print(f'ValueError, Exited with message: {e}')
            df_expanded = None

        return df_expanded
    
    def post_process_int_area(self,log):

        script_path = os.path.join(self.local_path,'PV_scripts/PV_io_int_area.py')
        log.info('Executing pvpython script to calculate Int_area')
        log.info('-' * 100)

        try:
            output = subprocess.run(['pvpython', script_path, self.save_path , self.run_name], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            captured_stdout = output.stdout.decode('utf-8').strip().split('\n')

            outlines = []
            
            for i, line in enumerate(captured_stdout):
                stripline = line.strip()
                outlines.append(stripline)
                if i < len(captured_stdout) - 1:
                    print(stripline)

            df = pd.read_json(outlines[-1], dtype=float, precise_float=True)
            df_expanded = df.apply(pd.Series.explode)
            df_expanded = df_expanded.reset_index(drop=True)

        except subprocess.CalledProcessError as e:
            print(f"Error executing the script with pvpython: {e}")
            df_expanded = None
        except FileNotFoundError:
            print("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")
            df_expanded = None
        except ValueError as e:
            print(f'ValueError, Exited with message: {e}')
            df_expanded = None

        return df_expanded

    def post_process_Ek(self,log):

        ### Attributes not defined in class constructor as they are case-specific
        self.rho_l = self.pset_dict['rho_l']
        self.rho_g = self.pset_dict['rho_g']

        script_path = os.path.join(self.local_path,'PV_scripts/PV_io_Ek.py')
        log.info('Executing pvpython script to calculate Ek')
        log.info('-' * 100)

        try:
            output = subprocess.run(['pvpython', script_path, self.save_path , self.run_name, str(self.rho_l),str(self.rho_g)], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            captured_stdout = output.stdout.decode('utf-8').strip().split('\n')

            outlines = []
            
            for i, line in enumerate(captured_stdout):
                stripline = line.strip()
                outlines.append(stripline)
                if i < len(captured_stdout) - 1:
                    print(stripline)

            df = pd.read_json(outlines[-1], dtype=float, precise_float=True)
            df_expanded = df.apply(pd.Series.explode)
            df_expanded = df_expanded.reset_index(drop=True)

        except subprocess.CalledProcessError as e:
            print(f"Error executing the script with pvpython: {e}")
            df_expanded = None
        except FileNotFoundError:
            print("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")
            df_expanded = None
        except ValueError as e:
            print(f'ValueError, Exited with message: {e}')
            df_expanded = None

        return df_expanded
    