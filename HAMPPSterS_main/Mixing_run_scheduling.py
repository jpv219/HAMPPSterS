### Mixing_Automation_simulation_run, tailored for BLUE 12.5.1
### CFD scheduling, monitoring and post-processing script
### to be run locally
### Author: Juan Pablo Valdes,
### Contributors: Fuyue Liang
### Version: 5.0
### First commit: February, 2024
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
import glob
from datetime import datetime
from CFD_run_scheduling import SimScheduling


################################################################################### PARAMETRIC STUDY ################################################################################

################################################################################# Author: Juan Pablo Valdes #########################################################################

################################################################################# Tailored for static mixer study ###############################################################

########################################################################################### CHILD CLASS ############################################################################

class SMSimScheduling(SimScheduling):
        
    ### Init function
    def __init__(self) -> None:
        pass


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
