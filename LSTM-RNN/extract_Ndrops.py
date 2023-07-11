import numpy as np
import pandas as pd
import Load_Clean_DF
import csv
import sys

arg1 = sys.argv[1:]

directory = '/Users/mfgmember/Documents/Juan_Static_Mixer/ML/SMX_DeepLearning/LSTM-RNN/RawData/'

for case in arg1:

    df_input = Load_Clean_DF.extract_GVol(case)

    volume = df_input['Volume'].values.tolist()

    ncount = []

    for n in volume:
        d = n.shape[0]
        ncount.append(d)

    f = open(str(directory) + case + '_' + 'dnum.csv', 'w')
    with f:
        writer = csv.writer(f)
        writer.writerow(ncount)
    print(str(directory) + case + '_' + 'dnum.csv' + 'was created')