import numpy as np
import pandas as pd
import csv
import sys
import os, os.path

np.set_printoptions(threshold=sys.maxsize)

arg1 = sys.argv[1:]

directory = '/Users/mfgmember/Documents/Juan_Static_Mixer/ML/SMX_DeepLearning/LSTM-RNN/RawData/Clean_Data/'

Excl3d = [90,98,104,110,124,131,138]

ExclPM = [7,19,2,28,34,39,44,64,68,72,79,83,87,91,95,99,102,109,113,117,121]

for case in arg1:
    num_files = len([name for name in os.listdir(directory + str(case) + '/')]) - 1
    if str(case) == '3_drop':
        num_files_corr = [elem for elem in range(num_files) if elem not in Excl3d]
    else:
        num_files_corr = [elem for elem in range(num_files) if elem not in ExclPM]

    df = pd.DataFrame({"Time": [0], "Volume": [0]},dtype = object)

    times = [0.005*k for k in range(len(num_files_corr))]
    
    for i in range(len(num_files_corr)):

        vol = np.genfromtxt(directory +  str(case) + '/' + str(case) + '_' + str(num_files_corr[i]) + '.csv',delimiter=',')

        df.iloc[0,0] = times[i]
        df.iloc[0,1] = vol
        
        if i == 0:
            df.to_csv(directory.replace('Clean_Data/','') + str(case) +  '_Vol.csv',index=False, header=True)
        else:
            df.to_csv(directory.replace('Clean_Data/','') + str(case) + '_Vol.csv',mode='a', index =False,header=False)