import csv
import subprocess
import pickle


script_path = '/Users/mfgmember/Documents/Juan_Static_Mixer/ML/SMX_DeepLearning/Database-ActiveLearning/PV_ndrop_DSD.py'

case_name = 'smx_ml'

try:
    output_bytes = subprocess.check_output(['pvpython', script_path, case_name])

    df_DSD = pickle.loads(output_bytes)

    print(df_DSD)


except subprocess.CalledProcessError as e:
    print(f"Error executing the script with pvpython: {e}")
except FileNotFoundError:
    print("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")