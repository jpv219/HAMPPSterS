import subprocess
import pandas as pd


def post_process():
    script_path = '/home/jpv219/Documents/ML/SMX_DeepLearning/Database-ActiveLearning/PV_ndrop_DSD.py'
    save_path = '/media/jpv219/ML/Runs/'
    run_name = 'run_1'

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

        return df_DSD

    except subprocess.CalledProcessError as e:
        print(f"Error executing the script with pvpython: {e}")
    except FileNotFoundError:
        print("pvpython command not found. Make sure Paraview is installed and accessible in your environment.")

def main():
        dfDSD = post_process()
        Nd = dfDSD.size

        print('-' * 100)
        print('Post processing completed succesfully')
        print(Nd)
        print(dfDSD)

if __name__ == "__main__":
    main()