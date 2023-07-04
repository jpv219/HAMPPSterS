import numpy as np
import pandas as pd
import Clean_CSV
import csv
import sys

arg1 = sys.argv[1:]

directory = '/Users/mfgmember/Documents/Juan_Static_Mixer/ML/SMX_DeepLearning/LSTM-RNN/RawData/'

for case in arg1:

    path = 'RawData/' + case + '_GVol.csv'

    input = pd.read_csv(path)
    df_input = Clean_CSV.clean_csv(input,list(input.columns.values)[1:3])

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