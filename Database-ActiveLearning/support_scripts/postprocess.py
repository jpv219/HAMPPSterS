import csv
import subprocess
import pandas as pd


script_path = '/Users/mfgmember/Documents/Juan_Static_Mixer/ML/SMX_DeepLearning/Database-ActiveLearning/PV_ndrop_DSD.py'

save_path = '/Volumes/ML/Runs/'

case_name = 'smx_ml'


try:
    output = subprocess.run(['pvpython', script_path, save_path ,case_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    captured_stdout = output.stdout.decode('utf-8')
    
    df_DSD = pd.read_json(captured_stdout, orient='split', dtype=float, precise_float=True)

    print(df_DSD)


except subprocess.CalledProcessError as e:
    print(f"Error executing the script with pvpython: {e}")
except FileNotFoundError:
    print("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")