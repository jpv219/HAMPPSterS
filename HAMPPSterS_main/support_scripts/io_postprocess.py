import subprocess
import pandas as pd
import glob
import os

def post_process_ak0(run_name):

    script_path = '/home/pdp19/Documents/SMX_DeepLearning/HAMPPSterS_main/PV_scripts/PV_io_ak0.py'
    local_path = '/home/pdp19/Documents/SMX_DeepLearning/HAMPPSterS_main/'
    save_path = '/media/pdp19/PPICO3/ML_PROJECT/int_osc_clean/RUNS/'
    save_path_runID = os.path.join(save_path,run_name)
    save_path_runID = os.path.join(save_path,run_name)
    save_path_runID_post = os.path.join(save_path_runID,'postProcessing')

    os.chdir(save_path_runID_post)

    try:
        output = subprocess.run(['pvpython', script_path, save_path , run_name], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        captured_stdout = output.stdout.decode('utf-8').strip().split('\n')

        outlines= []
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

def post_process_ak1(run_name):

    script_path = '/home/pdp19/Documents/SMX_DeepLearning/HAMPPSterS_main/PV_scripts/PV_io_ak1.py'
    local_path = '/home/pdp19/Documents/SMX_DeepLearning/HAMPPSterS_main/'
    save_path = '/media/pdp19/PPICO3/ML_PROJECT/int_osc_clean/RUNS/'
    save_path_runID = os.path.join(save_path,run_name)
    save_path_runID = os.path.join(save_path,run_name)
    save_path_runID_post = os.path.join(save_path_runID,'postProcessing')

    os.chdir(save_path_runID_post)

    try:
        output = subprocess.run(['pvpython', script_path, save_path , run_name], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        captured_stdout = output.stdout.decode('utf-8').strip().split('\n')

        outlines= []
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

def post_process_ak2(run_name):

    script_path = '/home/pdp19/Documents/SMX_DeepLearning/HAMPPSterS_main/PV_scripts/PV_io_ak2.py'
    local_path = '/home/pdp19/Documents/SMX_DeepLearning/HAMPPSterS_main/'
    save_path = '/media/pdp19/PPICO3/ML_PROJECT/int_osc_clean/RUNS/'
    save_path_runID = os.path.join(save_path,run_name)
    save_path_runID = os.path.join(save_path,run_name)
    save_path_runID_post = os.path.join(save_path_runID,'postProcessing')

    os.chdir(save_path_runID_post)

    try:
        output = subprocess.run(['pvpython', script_path, save_path , run_name], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        captured_stdout = output.stdout.decode('utf-8').strip().split('\n')

        outlines= []
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

def post_process_ak3(run_name):

    script_path = '/home/pdp19/Documents/SMX_DeepLearning/HAMPPSterS_main/PV_scripts/PV_io_ak3.py'
    local_path = '/home/pdp19/Documents/SMX_DeepLearning/HAMPPSterS_main/'
    save_path = '/media/pdp19/PPICO3/ML_PROJECT/int_osc_clean/RUNS/'
    save_path_runID = os.path.join(save_path,run_name)
    save_path_runID = os.path.join(save_path,run_name)
    save_path_runID_post = os.path.join(save_path_runID,'postProcessing')

    os.chdir(save_path_runID_post)

    try:
        output = subprocess.run(['pvpython', script_path, save_path , run_name], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        captured_stdout = output.stdout.decode('utf-8').strip().split('\n')

        outlines= []
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

def post_process_int_area(run_name):

    script_path = '/home/pdp19/Documents/SMX_DeepLearning/HAMPPSterS_main/PV_scripts/PV_io_int_area.py'
    local_path = '/home/pdp19/Documents/SMX_DeepLearning/HAMPPSterS_main/'
    save_path = '/media/pdp19/PPICO3/ML_PROJECT/int_osc_clean/RUNS/'
    save_path_runID = os.path.join(save_path,run_name)
    save_path_runID = os.path.join(save_path,run_name)
    save_path_runID_post = os.path.join(save_path_runID,'postProcessing')

    os.chdir(save_path_runID_post)

    try:
        output = subprocess.run(['pvpython', script_path, save_path , run_name], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        captured_stdout = output.stdout.decode('utf-8').strip().split('\n')

        outlines= []
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

def post_process_Ek(run_name):

    script_path = '/home/pdp19/Documents/SMX_DeepLearning/HAMPPSterS_main/PV_scripts/PV_io_Ek.py'
    local_path = '/home/pdp19/Documents/SMX_DeepLearning/HAMPPSterS_main/'
    save_path = '/media/pdp19/PPICO3/ML_PROJECT/int_osc_clean/RUNS/'
    rho_l = '1'
    rho_g = '1e-2'
    save_path_runID = os.path.join(save_path,run_name)
    save_path_runID = os.path.join(save_path,run_name)
    save_path_runID_post = os.path.join(save_path_runID,'postProcessing')

    os.chdir(save_path_runID_post)

    try:
        output = subprocess.run(['pvpython', script_path, save_path , run_name, rho_l, rho_g], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        captured_stdout = output.stdout.decode('utf-8').strip().split('\n')

        outlines= []
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



def main():

    for i in [2]:
        run_name = f'run_osc_clean_{i}'      
        dfak0 = post_process_ak0(run_name)
        dfak1 = post_process_ak1(run_name)
        dfak2 = post_process_ak2(run_name)
        dfak3 = post_process_ak3(run_name)
        dfintarea = post_process_int_area(run_name)
        dfEk = post_process_Ek(run_name)

        if dfak0 is not None and dfak1 is not None and dfak2 is not None and dfintarea is not None:
            df_run = pd.DataFrame({'Run':[run_name]})
            df_run = pd.concat([df_run] * len(dfak0), ignore_index=True)
            df_compiled = pd.concat([df_run,dfak0,dfak1["ak1"],dfak2["ak2"],dfak3["ak3"],dfintarea["Int_area"],dfEk["Ek"]], axis = 1)

            print('-' * 100)
            print(f'Post processing completed succesfully for {run_name}')
            print('-' * 100)

            csvbkp_file_path = '/home/pdp19/Documents/SMX_DeepLearning/HAMPPSterS_main/CSV_BKP/ioclean.csv'

            # Check if the CSV file already exists
            if not os.path.exists(csvbkp_file_path):
                # If it doesn't exist, create a new CSV file with a header
                df = pd.DataFrame({'Run_ID': [], 'Time': [], 'ak0': [], 'ak1': [], 'ak2': [], 'ak3': [], 'Int_area' : [],'Ek_half' : []})
                df.to_csv(csvbkp_file_path, index=False)
            
            ### Append data to csvbkp file
            df_compiled.to_csv(csvbkp_file_path, mode='a', header= False, index=False)
            print('-' * 100)
            print(f'Saved backup post-process data successfully to {csvbkp_file_path}')
            print('-' * 100)
        
        else:
            print(f'Pvpython postprocessing failed for {run_name}.')



if __name__ == "__main__":
    main()
