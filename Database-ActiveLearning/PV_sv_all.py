### Stirred_Vessel_Automation_simulation_run, tailored for Paraview 5.10
### Multiphase dispersion metrics post-processing script: ALL time steps
### to be run locally
### Author: Fuyue Liang,
### First commit: Sep, 2023
### Version: 1.0
### Department of Chemical Engineering, Imperial College London
#####################################################################
from paraview.simple import *
import sys
import pandas as pd
import numpy as np
import os 
import glob
import shutil

if __name__ == "__main__":

    HDpath = sys.argv[1]#'/media/fl18/Elements/surf_ML/'#
    
    case_name = sys.argv[2]#'run_svtest_2'#

    path = os.path.join(HDpath,case_name)
    os.chdir(path)

    ### find the final time steps ###
    pvdfiles = glob.glob('VAR_*_time=*.pvd')
    times = sorted([float(filename.split('=')[-1].split('.pvd')[0]) for filename in pvdfiles])
    
    pvdfile0 = f'VAR_{case_name}_time=0.00000E+00.pvd'
    shutil.copy(pvdfile0, f'VAR_DSD_{case_name}.pvd')
    pvdfile = f'VAR_DSD_{case_name}.pvd'

    DSD_list = []
    for t_idx,t in enumerate(times):

        if t_idx < 256:
            value_to_add = {'Time': t, 'Volumes': [], 'Nd': 0}

        else:
            old_suf = "_0.vtr"
            new_suf = f"_{t_idx}.vtr"

            with open(pvdfile0,"r") as input_file:
                lines = input_file.readlines()

            ### modify a pvdfile with the new time step ###
            updated_lines = []
            for line in lines:
                if old_suf in line:
                    updated_line = line.replace(old_suf, new_suf)
                    updated_lines.append(updated_line)
                else:
                    updated_lines.append(line)

            with open(pvdfile, "w") as output_file:
                output_file.writelines(updated_lines)
            
            if t_idx % 100 == 0:
                print(f'{t_idx}: PVD file modified correctly.') 

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

            volume_list = []
            for i in range(lower_bound, upper_bound+1):
                # select individual droplet
                threshold.ThresholdRange = [i, i]

                # collect data
                data_object = paraview.servermanager.Fetch(integral)
                volume = data_object.GetCellData().GetArray('Volume').GetValue(0)
                volume_list.append(volume)    
            # volume_list = [1e-9, 6.7e-11, 5.8e-10]
            volume_floats = [float(x) for x in volume_list]
            volume_count = len(volume_list)
            value_to_add = {'Time': t, 'Volumes': volume_floats, 'Nd': volume_count}

            if t_idx % 100 == 0:
                print(f'Volumes at snaps {t_idx} extracted.')
            
        DSD_list.append(value_to_add)

        Disconnect()
        Connect()
    
    print('Volume for all time steps extracted correctly from integrate variables.')
    df_DSD = pd.DataFrame(DSD_list, columns=['Time','Volumes', 'Nd'])
    df_json = df_DSD.to_json(orient='split', double_precision=15)
        
    print(df_json)

