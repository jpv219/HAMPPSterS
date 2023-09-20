import subprocess
import pandas as pd
import glob
import os


def post_process():

    script_path = '/home/jpv219/Documents/ML/SMX_DeepLearning/Database-ActiveLearning/PV_ndrop_DSD.py'
    local_path = '/home/jpv219/Documents/ML/SMX_DeepLearning/Database-ActiveLearning/'
    save_path = '/media/jpv219/ML/test_pp'
    run_name = 'run_2'
    save_path_runID = os.path.join(save_path,run_name)

    os.chdir(save_path_runID)
    pvdfiles = glob.glob('VAR_*_time=*.pvd')
    maxpvd_tf = max(float(filename.split('=')[-1].split('.pvd')[0]) for filename in pvdfiles)

    df_csv = pd.read_csv(os.path.join(save_path_runID,f'{run_name}.csv'))
    df_csv['diff'] = abs(df_csv['Time']-maxpvd_tf)

    tf_row = df_csv.sort_values(by='diff')

    IntA = tf_row.iloc[0]['INTERFACE_SURFACE_AREA']

    os.chdir(local_path)

    print('Executing pvpython script')
    print('-'*100)

    try:
        output = subprocess.run(['pvpython', script_path, save_path , run_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        captured_stdout = output.stdout.decode('utf-8').strip().split('\n')
        outlines= []
        for i, line in enumerate(captured_stdout):
            stripline = line.strip()
            outlines.append(stripline)
            if i < len(captured_stdout) - 1:
                print(stripline)
        
        df_DSD = pd.read_json(outlines[-1], orient='split', dtype=float, precise_float=True)

    except subprocess.CalledProcessError as e:
        print(f"Error executing the script with pvpython: {e}")
        df_DSD = None
    except FileNotFoundError:
        print("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")
        df_DSD = None

    return df_DSD, IntA

def post_process_SP():

    script_path = '/home/jpv219/Documents/ML/SMX_DeepLearning/Database-ActiveLearning/PV_sp_PP.py'
    local_path = '/home/jpv219/Documents/ML/SMX_DeepLearning/Database-ActiveLearning/'
    save_path = '/media/jpv219/ML/SP_Runs'
    run_name = 'run_sp_9'

    os.chdir(local_path)

    n_ele = 5
    pipe_radius = 0.01467741935483871
    domain_length = (1 + float(n_ele))*float(pipe_radius)*2

    ### Running pvpython script for Nd and DSD

    print('-'*100)
    print('Executing pvpython script')
    print('-'*100)

    try:
        output = subprocess.run(['pvpython', script_path, save_path , run_name, str(domain_length), str(pipe_radius)], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        captured_stdout = output.stdout.decode('utf-8').strip().split('\n')
        outlines= []
        for i, line in enumerate(captured_stdout):
            stripline = line.strip()
            outlines.append(stripline)
            if i < len(captured_stdout) - 1:
                print(stripline)
        
        df_hyd = pd.read_json(outlines[-1], orient='split', dtype=float, precise_float=True)

    except subprocess.CalledProcessError as e:
        print(f"Error executing the script with pvpython: {e}")
        return None 
    except FileNotFoundError:
        print("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")
        return None
    except ValueError as e:
        print(f'ValueError, Exited with message: {e}')
        return None

    return df_hyd

def main():

    run_name = 'run_2'          
### pvpython execution

    dfDSD, IntA = post_process()

    if dfDSD is not None:

        Nd = dfDSD.size

        df_scalar = pd.DataFrame({'Run':[run_name],'IA': [IntA], 'Nd': [Nd]})
        df_drops = pd.concat([df_scalar,dfDSD], axis = 1)

        print('-' * 100)
        print('Post processing completed succesfully')
        print('-' * 100)
        print(f'Number of drops in this run: {Nd}')
        print(f'Drop size dist. {dfDSD}')
        print(f'Interfacial Area : {IntA}')

        csvbkp_file_path = f'/media/jpv219/ML/geom.csv'


        # Check if the CSV file already exists
        if not os.path.exists(csvbkp_file_path):
            # If it doesn't exist, create a new CSV file with a header
            df = pd.DataFrame({'Run_ID': [], 'Interfacial Area': [], 'Number of Drops': [], 
                                'DSD': []})
            df.to_csv(csvbkp_file_path, index=False)
        
        ### Append data to csvbkp file
        df_drops.to_csv(csvbkp_file_path, mode='a', header= False, index=False)
        print('-' * 100)
        print(f'Saved backup post-process data successfully to {csvbkp_file_path}')
        print('-' * 100)

    else:
        print('pvpython post-rocessing failed, returning empty')


        ### pvpython execution
        
    # df_hyd = post_process_SP()

    # if df_hyd is not None:
    #     L = df_hyd['Length']
    #     emax = df_hyd['e_max']
    #     Q = df_hyd['Q']
    #     ediss =  df_hyd['E_diss']
    #     gamma = df_hyd['Gamma']
    #     P = df_hyd['Pressure']
    #     u = df_hyd['Velocity']

    #     print('-' * 100)
    #     print('Post processing completed succesfully')
    #     print('-' * 100)
    #     print('Extracted relevant hydrodynamic data')

    #     df_hyd.insert(0,'Run', run_name)

    #     csvbkp_file_path = f'/home/jpv219/Documents/ML/SMX_DeepLearning/Database-ActiveLearning/CSV_BKP/sp_geom.csv'

    #     # Check if the CSV file already exists
    #     if not os.path.exists(csvbkp_file_path):
    #         # If it doesn't exist, create a new CSV file with a header
    #         df = pd.DataFrame({'Run_ID': [], 'Length': [], 'E_max': [], 
    #                             'Q': [], 'E_diss': [], 'Gamma': [], 'Pressure': [], 'Velocity':[]})
    #         df.to_csv(csvbkp_file_path, index=False)
        
    #     ### Append data to csvbkp file
    #     df_hyd.to_csv(csvbkp_file_path, mode='a', header= False, index=False)
    #     print('-' * 100)
    #     print(f'Saved backup post-process data successfully to {csvbkp_file_path}')
    #     print('-' * 100)
    # else:
    #     print('Pvpython postprocessing failed')


if __name__ == "__main__":
    main()
