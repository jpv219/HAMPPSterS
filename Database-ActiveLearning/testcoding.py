### test codes ###
import glob
import os
import pandas as pd

os.chdir('/media/fl18/Elements/emu_ML/testref9MRNS')

df_csv = pd.read_csv('emu_testref9MRNS_layer_2.csv')
pvdfiles = glob.glob('VAR_*_time=*.pvd')
maxpvd_tf = max(float(filename.split('=')[-1].split('.pvd')[0]) for filename in pvdfiles)
abs(df_csv['Time']-maxpvd_tf)

print(maxpvd_tf)