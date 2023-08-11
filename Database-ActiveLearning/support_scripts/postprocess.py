import subprocess
import pandas as pd
import glob
import os


def post_process():

    script_path = '/home/jpv219/Documents/ML/SMX_DeepLearning/Database-ActiveLearning/PV_ndrop_DSD.py'
    local_path = '/home/jpv219/Documents/ML/SMX_DeepLearning/Database-ActiveLearning/'
    save_path = '/media/jpv219/ML/Runs/'
    run_name = 'run_1'
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

def main():
        dfDSD, IntA = post_process()
        Nd = dfDSD.size

        print('-' * 100)
        print('Post processing completed succesfully')
        print(Nd)
        print(dfDSD)
        print(IntA)

if __name__ == "__main__":
    main()