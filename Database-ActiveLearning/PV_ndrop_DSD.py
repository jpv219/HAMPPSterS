from paraview.simple import *
import os
import glob
import pandas as pd
import sys


def pvdropDSD(case_name):

    HDpath = '/Volumes/ML/Runs'

    path = os.path.join(HDpath,case_name,'RESULTS')
    
    os.chdir(path)

    pvdfile = glob.glob('*.pvd')[0]

    timestep = int(glob.glob('VAR_*_*.vtr')[0].split("_")[-1].split(".")[0])

    case_data = PVDReader(FileName=pvdfile)
    case_data.CellArrays = []
    case_data.PointArrays = ['Velocity', 'Interface', 'X_Velocity', 'Y_Velocity', 'Z_Velocity', 'Pressure']
    case_data.ColumnArrays = []

    # get animation scene
    animationScene1 = GetAnimationScene()

    # update animation scene based on data timesteps
    animationScene1.UpdateAnimationUsingDataTimeSteps()

    # Properties modified on animationScene1
    animationScene1.AnimationTime = timestep

    # get the time-keeper
    timeKeeper1 = GetTimeKeeper()

    case_data.UpdatePipeline()

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

    UpdatePipeline(time=timestep, proxy=case_data)

    UpdatePipeline(time=timestep, proxy=connectivity)

    UpdatePipeline(time=timestep, proxy=threshold1)

    # find lower and upper bound indices of droplet list
    region_range = connectivity.CellData.GetArray(0).GetRange()

    lower_bound = int(region_range[0])
    upper_bound = int(region_range[1])


    volume_list = []

    for j in range(lower_bound, upper_bound+1):

        threshold1.UpperThreshold = j
        threshold1.LowerThreshold = j

        # create a new 'Integrate Variables'
        integrateVariables1 = IntegrateVariables(registrationName='IntegrateVariables1', Input=threshold1)
        integrateVariables1.DivideCellDataByVolume = 0

        UpdatePipeline(time=timestep, proxy=integrateVariables1)

        volume_object = paraview.servermanager.Fetch(integrateVariables1)
        volume = volume_object.GetCellData().GetArray('Volume').GetValue(0)
        volume_list.append(volume)

    volume_floats = [float(x) for x in volume_list]

    volume_df = pd.DataFrame(volume_floats, columns=['Volume'])
   
    df_json = volume_df.to_json(orient='split', double_precision=15)

    return df_json

if __name__ == "__main__":

    case_name = sys.argv[1]

    df_bytes = pvdropDSD(case_name)

    print(df_bytes)



