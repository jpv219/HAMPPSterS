### Mixing_Automation_simulation_run, tailored for BLUE 12.5.1
### CFD scheduling, monitoring and post-processing script
### to be run locally
### Author: Juan Pablo Valdes,
### Contributors: Fuyue Liang
### Version: 6.0
### First commit: February, 2024
### Department of Chemical Engineering, Imperial College London
#######################################################################################################################################################################################
#######################################################################################################################################################################################

import os
from time import sleep
import pandas as pd
import subprocess
import paramiko
import json
import numpy as np
import glob
from CFD_run_scheduling import SimScheduling as SS


################################################################################### PARAMETRIC STUDY ################################################################################

################################################################################# Author: Juan Pablo Valdes #########################################################################

################################################################################# Tailored for static mixer study ###############################################################

########################################################################################### CHILD CLASS ############################################################################

class SMSimScheduling(SS):
        
    ### Init function
    def __init__(self) -> None:
        pass

    ### local run assigning parametric study to HPC handling script and performing overall BLUE workflow
    def localrun(self,pset_dict):

        ### constructor from parent class SimScheduling ###
        super().__init__(pset_dict)

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
            command = f'python {self.main_path}/{HPC_script} run --pdict \'{dict_str}\' --study \'{str(self.study_ID)}\''
            jobid, t_wait, status, _ = self.execute_remote_command(command=command,search=0,log=log)
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"SSH ERROR: Authentication failed: {e}")
            return return_from_casetype.get(self.case_type,{})
        except (ValueError, SS.JobStatError, NameError) as e:
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
            except (ValueError, NameError, SS.ConvergenceError) as e:
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
                command = f'python {self.main_path}/{HPC_script} job_restart --pdict \'{dict_str}\' --study \'{str(self.study_ID)}\''
                new_jobID, new_t_wait, new_status, ret_bool = self.execute_remote_command(
                    command=command, search=2, log=log
                    )

                log.info('-' * 100)

                ### updating
                jobid = new_jobID
                t_wait = new_t_wait
                status = new_status
                restart = eval(ret_bool)

            except (ValueError,FileNotFoundError,NameError,SS.BadTerminationError,SS.JobStatError,TypeError,KeyError) as e:
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
            command = f'python {self.main_path}/{HPC_script} vtk_convert --pdict \'{dict_str}\' --study \'{str(self.study_ID)}\''
            conv_jobid, conv_t_wait, conv_status, _ = self.execute_remote_command(
                command=command,search=0,log=log
                )
            log.info('-' * 100)
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"SSH ERROR: Authentication failed: {e}")
            return return_from_casetype.get(self.case_type,{})
        except (FileNotFoundError, SS.JobStatError, ValueError, NameError) as e:
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

################################################################################### PARAMETRIC STUDY ################################################################################

################################################################################# Author: Fuyue Liang #########################################################################

################################################################################# Tailored for stirred mixer study ###############################################################

########################################################################################### CHILD CLASS ############################################################################

class SVSimScheduling(SS):

    ### Ini Function ###
    def __init__(self) -> None:
        pass        
    
    def localrun(self, pset_dict):
        
        ## Study specific attrbiuted to be constructed
        vtk_conv_mode = pset_dict['vtk_conv_mode']
        
        ### constructor from parent class SimScheduling ###
        super().__init__(pset_dict,vtk_conv_mode = vtk_conv_mode)

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
            command = f"python {self.main_path}/{HPC_script} run --pdict \'{dict_str}\' --study \'{str(self.study_ID)}\'"
            jobid, t_wait, status, _ = self.execute_remote_command(command=command,search=0,log=log)
        except (paramiko.AuthenticationException,paramiko.SSHException) as e:
            log.info(f'SSH EEROR: Authentication failed: {e}')
            return return_from_casetype.get(self.case_type, {})
        except (ValueError, SS.JobStatError, NameError) as e:
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
            except (ValueError, NameError, SS.ConvergenceError) as e:
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
                command = f'python {self.main_path}/{HPC_script} job_restart --pdict \'{dict_str}\' --study \'{str(self.study_ID)}\''
                new_jobID, new_t_wait, new_status, ret_bool = self.execute_remote_command(
                    command=command, search=2, log=log
                    )

                log.info('-' * 100)

                ### updating
                jobid = new_jobID
                t_wait = new_t_wait
                status = new_status
                restart = eval(ret_bool)

            except (ValueError,FileNotFoundError,NameError,SS.BadTerminationError,SS.JobStatError,TypeError,KeyError) as e:
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
            command = f'python {self.main_path}/{HPC_script} vtk_convert --pdict \'{dict_str}\' --study \'{str(self.study_ID)}\''
            conv_jobid, conv_t_wait, conv_status, _ = self.execute_remote_command(
                command=command,search=0,log=log
                )
            log.info('-' * 100)
        except (paramiko.AuthenticationException, paramiko.SSHException) as e:
            log.info(f"SSH ERROR: Authentication failed: {e}")
            return return_from_casetype.get(self.case_type,{})
        except (FileNotFoundError, SS.JobStatError, ValueError, NameError) as e:
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
