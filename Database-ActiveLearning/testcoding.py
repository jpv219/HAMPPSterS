### test codes ###
import glob
import os
import pandas as pd

os.chdir('/media/fl18/Elements/emu_ML/testref9MRNS')#('calc')#

df_csv = pd.read_csv('emu_testref9MRNS_layer.csv')
print(df_csv[-5:])

pvdfiles = glob.glob('VAR_*_time=*.pvd')
vtrfiles = glob.glob('VAR_*_0_*.vtr')
timestep = [float(filename.split('=')[-1].split('.pvd')[0]) for filename in pvdfiles]

print(len(timestep), len(vtrfiles))
print(f'after sorted:{sorted(timestep)}')

### Find the interfacial area ###
findrow = df_csv[df_csv['Time']==timestep[52]]
findtime = findrow['Time'].values
findint = findrow['INTERFACE_SURFACE_AREA'].values
print(f'found {findint}')
print(f'want time step: {timestep[52]}, and it found as {findtime}')