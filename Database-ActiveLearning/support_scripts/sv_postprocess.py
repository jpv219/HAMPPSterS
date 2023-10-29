import subprocess
import pandas as pd
import glob
import os


def post_process_lastsp(run_name):

    script_path = '/home/fl18/Desktop/automatework/ML_auto/SMX_DeepLearning/Database-ActiveLearning/PV_scripts/PV_sv_sp.py'
    local_path = '/home/fl18/Desktop/automatework/ML_auto/SMX_DeepLearning/Database-ActiveLearning/'
    save_path = '/media/fl18/Elements/spgeom_ML/'
    C_path = os.path.join(local_path,'DOE/finished_sp_svgeom/LHS_sp_svgeom_1.pkl')
    save_path_runID = os.path.join(save_path,run_name)

    os.chdir(save_path_runID)
    pvdfiles = glob.glob('VAR_*_time=*.pvd')
    maxpvd_tf = max(float(filename.split('=')[-1].split('.pvd')[0]) for filename in pvdfiles)
    
    os.chdir(local_path)
    C_num = int(run_name.split('_')[-1])
    df = pd.read_pickle(C_path)
    C = df['Clearance (m)'][C_num-1]
    print(C)

    print('Executing pvpython script')
    print('-'*100)

    try:
        output = subprocess.run(['pvpython', script_path, save_path , run_name, str(C)], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        captured_stdout = output.stdout.decode('utf-8').strip().split('\n')
        outlines= []
        for i, line in enumerate(captured_stdout):
            stripline = line.strip()
            outlines.append(stripline)
            if i < len(captured_stdout) - 1:
                print(stripline)
        
        df_sp = pd.read_json(outlines[-1], orient='split', dtype=float, precise_float=True)

    except subprocess.CalledProcessError as e:
        print(f"Error executing the script with pvpython: {e}")
        df_sp = None
    except FileNotFoundError:
        print("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")
        df_sp = None
    except ValueError as e:
        print(f'ValueError, Exited with message: {e}')
        df_sp = None

    return df_sp, maxpvd_tf

def post_process_last(run_name):

    script_path = '/home/fl18/Desktop/automatework/ML_auto/SMX_DeepLearning/Database-ActiveLearning/PV_scripts/PV_sv_last.py'
    local_path = '/home/fl18/Desktop/automatework/ML_auto/SMX_DeepLearning/Database-ActiveLearning/'
    save_path = '/media/fl18/Elements/surf_ML/'
    save_path_runID = os.path.join(save_path,run_name)

    os.chdir(save_path_runID)
    pvdfiles = glob.glob('VAR_*_time=*.pvd')
    maxpvd_tf = max(float(filename.split('=')[-1].split('.pvd')[0]) for filename in pvdfiles)

    df_csv = pd.read_csv(os.path.join(save_path_runID,f'{run_name}.csv' if os.path.exists(f'{run_name}.csv') else f'HST_{run_name}.csv'))
    df_csv['diff'] = abs(df_csv['Time']-maxpvd_tf)
    print('Reading data from csv')
    print('-'*100)

    tf_row = df_csv.sort_values(by='diff')

    IntA = tf_row.iloc[0]['INTERFACE_SURFACE_AREA']
    print('Interfacaial area extracted.')
    print('-'*100)

    os.chdir(local_path)
    print('Executing pvpython script.')
    print('-'*100)

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
        
        df_DSD = pd.read_json(outlines[-1], orient='split', dtype=float, precise_float=True)

    except subprocess.CalledProcessError as e:
        print(f"Error executing the script with pvpython: {e}")
        df_DSD = None
    except FileNotFoundError:
        print("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")
        df_DSD = None
    except ValueError as e:
        print(f'ValueError, Exited with message: {e}')
        df_DSD = None

    return df_DSD, IntA, maxpvd_tf

def post_process_all(run_name):

    script_path = '/home/fl18/Desktop/automatework/ML_auto/SMX_DeepLearning/Database-ActiveLearning/PV_scripts/PV_sv_sp.py'
    local_path = '/home/fl18/Desktop/automatework/ML_auto/SMX_DeepLearning/Database-ActiveLearning/'
    save_path = '/media/fl18/Elements/surf_ML/'
    save_path_runID = os.path.join(save_path,run_name)

    os.chdir(save_path_runID)

    df_csv = pd.read_csv(os.path.join(save_path_runID, f'{run_name}.csv'
                                          if os.path.exists(f'{run_name}.csv') 
                                          else f'HST_{run_name}.csv'))
    pvdfiles = glob.glob('VAR_*_time=*.pvd')
    times = sorted([float(filename.split('=')[-1].split('.pvd')[0]) for filename in pvdfiles])
    maxtime = max(times)

    ints_list = []
    for t in times:
        therow = df_csv[df_csv['Time']==t]
        value_to_add = {'Time': t, 'IntA': therow['INTERFACE_SURFACE_AREA'].values}
        ints_list.append(value_to_add)
    df_ints = pd.DataFrame(ints_list, columns=['Time', 'IntA'])
    print(f'Interfacial Area up to {maxtime}[s] extracted.')
    print('-' * 100)

    ### Running pvpython script for Nd and DSD ###
    os.chdir(local_path)
    script_path = os.path.join(local_path,'PV_scripts/PV_sv_all.py')
    print('Executing pvpython script')
    print('-' * 100)

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

        df_DSD = pd.read_json(outlines[-1], orient='split', dtype=float, precise_float=True)
        df_join = pd.merge(df_ints, df_DSD, on='Time', how='left')

    except subprocess.CalledProcessError as e:
        print(f"Error executing the script with pvpython: {e}")
        df_join = None
    except FileNotFoundError:
        print("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")
        df_join = None
    except ValueError as e:
        print(f'ValueError, Exited with message: {e}')
        df_join = None

    return df_join

def main():
    for i in [16,17]:
        run_name = f'run_svsurf_{i}'         
    # ### pvpython execution
    #########################
    ### single phase last ###
    #########################
        # df_sp, maxtime = post_process_lastsp(run_name)

        # if df_sp is not None:

        #     df_hyd = pd.DataFrame({'Run':run_name,'Time':maxtime,
        #                                     'Height':df_sp['Height'],'Q':df_sp['Q'],'Pres':df_sp['Pressure'],
        #                                     'Ur': df_sp['Ur'], 'Uth':df_sp['Uth'], 'Uz':df_sp['Uz'],
        #                                     'arc_length':df_sp['arc_length'],'Q_over_line':df_sp['Q_over_line'], 
        #                                     'Ur_over_line':df_sp['Ur_over_line'],'Uz_over_line':df_sp['Uz_over_line']
        #                 })

        #     print('-' * 100)
        #     print(f'Post processing completed succesfully for {run_name}.')
        #     print('-' * 100)
        #     print('Extracted flow features')
        #     print(f'{df_sp}')

        #     csvbkp_file_path = '/home/fl18/Desktop/automatework/ML_auto/SMX_DeepLearning/Database-ActiveLearning/CSV_BKP/finished_sp_svgeom/sp_svgeom_1.csv'


        #     # Check if the CSV file already exists
        #     if not os.path.exists(csvbkp_file_path):
        #         # If it doesn't exist, create a new CSV file with a header
        #         df = pd.DataFrame({'Run':[],'Time':[],
        #                                     'Height':[],'Q':[],'Pres':[],
        #                                     'Ur': [], 'Uth':[], 'Uz':[],
        #                                     'arc_length':[],'Q_over_line':[], 
        #                                     'Ur_over_line':[],'Uz_over_line':[]
        #                     })
        #         df.to_csv(csvbkp_file_path, index=False)
            
        #     ### Append data to csvbkp file
        #     df_hyd.to_csv(csvbkp_file_path, mode='a', header= False, index=False)
        #     print('-' * 100)
        #     print(f'Saved backup post-process data successfully to {csvbkp_file_path}')
        #     print('-' * 100)

        # else:
        #     print('pvpython post-processing failed, returning empty')
        

    ### pvpython execution
    ########################
    ### two phases LAST ####
    ########################
        
        dfDSD, IntA, maxtime = post_process_last(run_name)

        if dfDSD is not None:
            df_drops = pd.DataFrame({'Run':run_name,
                                            'Time': maxtime,'IntA': IntA, 
                                            'Nd': dfDSD['Nd'], 'DSD': dfDSD['Volume']})

            print('-' * 100)
            print(f'Post processing completed succesfully for {run_name}')
            print('-' * 100)
            print(f'Drop size dist and Nd in this run at time {maxtime}[s]:')
            print(f'{dfDSD}')
            print(f'Interfacial Area : {IntA}')

            csvbkp_file_path = '/home/fl18/Desktop/automatework/ML_auto/SMX_DeepLearning/Database-ActiveLearning/CSV_BKP/svsurf.csv'

            # Check if the CSV file already exists
            if not os.path.exists(csvbkp_file_path):
                # If it doesn't exist, create a new CSV file with a header
                df = pd.DataFrame({'Run': [], 
                                'Time': [], 'IntA': [], 'Nd': [], 'DSD': []})
                df.to_csv(csvbkp_file_path, index=False)

            ### Append data to csvbkp file
            df_drops.to_csv(csvbkp_file_path, mode='a', header= False, index=False)
            print('-' * 100)
            print(f'Saved backup post-process data successfully to {csvbkp_file_path}')
            print('-' * 100)
        
        else:
            print(f'Pvpython postprocessing failed for {run_name}.')

### pvpython execution
    ########################
    ### two phases ALL ####
    ########################
        # df_join = post_process_all(run_name)

        # if df_join is not None:
        #     df_drops = pd.DataFrame({'Run':run_name, 
        #                              'Time':df_join['Time'], 'IntA':df_join['IntA'], 
        #                              'Nd':df_join['Nd'], 'DSD':df_join['Volumes']
        #                              })
        #     print('-' * 100)
        #     print(f'Post processing completed succesfully for {run_name}')
        #     print('-' * 100)
        #     print('Results for the last 10 time steps in this run:')
        #     print(f'{df_drops[:10]}')

        #     csvbkp_file_path = '/home/fl18/Desktop/automatework/ML_auto/SMX_DeepLearning/Database-ActiveLearning/CSV_BKP/svsurf.csv'

        #     # Check if the CSV file already exists
        #     if not os.path.exists(csvbkp_file_path):
        #         # If it doesn't exist, create a new CSV file
        #         df = pd.DataFrame({'Run':[],
        #                             'Time':[], 'IntA':[], 'Nd':[], 'DSD':[]})
        #         df.to_csv(csvbkp_file_path, index=False)
            
        #     ### Append data to csvbkp file
        #     df_drops.to_csv(csvbkp_file_path, mode='a', header= False, index=False)
        #     print('-' * 100)
        #     print(f'Saved backup post-process data successfully to {csvbkp_file_path}')
        #     print('-' * 100)
        
        # else:
        #     print(f'Pvpython postprocessing failed for {run_name}.')


if __name__ == "__main__":
    main()
