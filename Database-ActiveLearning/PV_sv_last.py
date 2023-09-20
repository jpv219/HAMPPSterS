### Stirred_Vessel_Automation_simulation_run, tailored for Paraview 5.10
### Multiphase dispersion metrics post-processing script: LAST time steps
### to be run locally
### Author: Fuyue Liang,
### First commit: Sep, 2023
### Version: 1.0
### Department of Chemical Engineering, Imperial College London
#####################################################################
from paraview.simple import *
import sys
import pandas as pd
import os 
import glob

def pvdropDSD(HDpath, case_name):
    path = os.path.join(HDpath,case_name)
    os.chdir(path)

    pvdfile = f'VAR_{case_name}_time=0.00000E+00.pvd'
    timestep = int(glob.glob('VAR_*_*.vtr')[0].split("_")[-1].split(".")[0])

    old_suf = "_0.vtr"
    new_suf = f"_{timestep}.vtr"

    with open(pvdfile,"r") as input_file:
        lines = input_file.readlines()

    ### modify a pvdfile with the last time step ###
    updated_lines = []
    for line in lines:
        if old_suf in line:
            updated_line = line.replace(old_suf, new_suf)
            updated_lines.append(updated_line)
        else:
            updated_lines.append(line)

    with open(pvdfile, "w") as output_file:
        output_file.writelines(updated_lines)

    print('PVD file modified correctly.') 

    ### paraview onwards ###
    case_data = PVDReader(FileName=pvdfile)
    mergeBlocks = MergeBlocks(Input=case_data)

    clip = Clip(Input=mergeBlocks)
    clip.Scalars = ['POINTS', 'Interface']
    clip.ClipType = 'Scalar'
    clip.Value = 0.0
    clip.Invert = 1   

    # tag droplets as connected regions
    connectivity = Connectivity(Input=clip)
    connectivity.RegionIdAssignmentMode = 'Cell Count Descending'

    # find lower and upper bound indices of droplet list
    region = paraview.servermanager.Fetch(connectivity)
    region_range = region.GetCellData().GetArray('RegionId').GetRange()

    threshold = Threshold(Input=connectivity)
    threshold.Scalars = ['POINTS', 'RegionId']
    
    # create new IntegrateVariables
    integral = IntegrateVariables(Input=threshold)

    lower_bound = int(region_range[0]+1)
    upper_bound = int(region_range[1])
    print(region_range, lower_bound)

    volume_list = []

    for i in range(lower_bound, upper_bound+1):
        # select individual droplet
        threshold.ThresholdRange = [i, i]

        # collect data
        data_object = paraview.servermanager.Fetch(integral)
        volume = data_object.GetCellData().GetArray('Volume').GetValue(0)
        volume_list.append(volume)    

    volume_floats = [float(x) for x in volume_list]
    volume_df = pd.DataFrame(volume_floats, columns=['Volume'])

    print('Volumes extracted correctly from integrate variables')

    df_jason = volume_df.to_json(orient='split', double_precision=15)

    return df_jason

if __name__ == "__main__":

    HDpath = sys.argv[1]
    
    case_name = sys.argv[2]

    df_bytes = pvdropDSD(HDpath,case_name)

    print(df_bytes)

