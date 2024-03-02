### SMX_Automation_simulation_run, tailored for Paraview 5.10
### Multiphase dispersion metrics post-processing script
### to be run locally
### Author: Juan Pablo Valdes,
### First commit: July, 2023
### Version: 6.0
### Department of Chemical Engineering, Imperial College London
#######################################################################################################################################################################################
#######################################################################################################################################################################################

from paraview.simple import *
import os
import glob
import pandas as pd
import sys


def pvdropDSD(HDpath,case_name):

    path = os.path.join(HDpath,case_name)
    
    os.chdir(path)

    pvdfile = f'VAR_{case_name}_time=0.00000E+00.pvd'

    timestep = int(glob.glob('VAR_*_*.vtr')[0].split("_")[-1].split(".")[0])

    old_suf = "_0.vtr"
    new_suf = f"_{timestep}.vtr"

    with open(pvdfile, "r") as input_file:
        lines = input_file.readlines()

    updated_lines = []
    for line in lines:
        if old_suf in line:
            updated_line = line.replace(old_suf, new_suf)
            updated_lines.append(updated_line)
        else:
            updated_lines.append(line)

    with open(pvdfile, "w") as output_file:
        output_file.writelines(updated_lines)

    print('PVD file modified correctly')

    case_data = PVDReader(FileName=pvdfile)
    case_data.CellArrays = []
    case_data.PointArrays = ['Velocity', 'Interface', 'X_Velocity', 'Y_Velocity', 'Z_Velocity', 'Pressure']
    case_data.ColumnArrays = []

    mergeBlocks = MergeBlocks(Input=case_data)
    mergeBlocks.OutputDataSetType = 'Unstructured Grid'
    mergeBlocks.MergePartitionsOnly = 0
    mergeBlocks.MergePoints = 1
    mergeBlocks.Tolerance = 0.0
    mergeBlocks.ToleranceIsAbsolute = 0

    clip = Clip(Input=mergeBlocks)
    clip.Scalars = ['POINTS', 'Interface']
    clip.ClipType = 'Scalar'
    clip.Invert = 0

    # tag droplets as connected regions
    connectivity = Connectivity(Input=clip)
    connectivity.ExtractionMode = 'Extract All Regions'
    connectivity.ColorRegions = 1
    connectivity.RegionIdAssignmentMode = 'Unspecified'
    connectivity.ClosestPoint = [0.0, 0.0, 0.0]

    # create a new 'Threshold'
    threshold1 = Threshold(registrationName='Threshold1', Input=connectivity)
    threshold1.Scalars = ['POINTS', 'RegionId']

    # find lower and upper bound indices of droplet list
    region_range = connectivity.CellData.GetArray(0).GetRange()

    print('Merge blocks, clip and connectivity performed correctly')

    lower_bound = int(region_range[0])
    upper_bound = int(region_range[1])


    volume_list = []

    for j in range(lower_bound, upper_bound+1):

        threshold1.UpperThreshold = j
        threshold1.LowerThreshold = j

        # create a new 'Integrate Variables'
        integrateVariables1 = IntegrateVariables(registrationName='IntegrateVariables1', Input=threshold1)
        integrateVariables1.DivideCellDataByVolume = 0

        volume_object = paraview.servermanager.Fetch(integrateVariables1)
        volume = volume_object.GetCellData().GetArray('Volume').GetValue(0)
        volume_list.append(volume)

    volume_floats = [float(x) for x in volume_list]

    volume_df = pd.DataFrame(volume_floats, columns=['Volume'])

    print('Volumes extracted correctly from integrate variables')

   
    df_json = volume_df.to_json(orient='split', double_precision=15)

    return df_json

if __name__ == "__main__":

    HDpath = sys.argv[1]
    
    case_name = sys.argv[2]

    df_bytes = pvdropDSD(HDpath,case_name)

    print(df_bytes)



