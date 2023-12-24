### Interfacial_Oscillations_Automation_simulation_run, tailored for Paraview 5.8.1
### Tracking of wave oscillations: ALL time steps
### to be run locally
### Author: Paula Pico,
### First commit: Dec, 2023
### Version: 5.0
### Department of Chemical Engineering, Imperial College London
#####################################################################

from paraview.simple import *
import numpy as np
import os 
import glob
import shutil
import json

def pvpy(HDpath,case_name):

    path = os.path.join(HDpath,case_name,'postProcessing')
    os.chdir(path)

    pvdfiles = glob.glob('VAR_*_time=*.pvd')
    pvdfile = f'VAR_{case_name}.pvd'

    case_data = PVDReader(FileName=pvdfile)
    case_data.CellArrays = []
    case_data.PointArrays = ['Interface']
    case_data.ColumnArrays = []

    print('Read data')

    contour1 = Contour(Input=case_data)
    contour1.ContourBy = ['POINTS', 'Interface']
    contour1.Isosurfaces = [0.0]
    contour1.PointMergeMethod = 'Uniform Binning'

    print('Made contour')

    clip1 = Clip(Input=contour1)
    clip1.ClipType = 'Plane'
    clip1.HyperTreeGridClipper = 'Plane'
    clip1.Scalars = ['POINTS', 'Interface']
    clip1.ClipType.Origin = [10.52325, 7.0155, 7.0155]
    clip1.HyperTreeGridClipper.Origin = [7.0155, 7.0155, 7.0155]
    clip1.Invert = 0

    print('Made clip')

    slice1 = Slice(Input=clip1)
    slice1.SliceType = 'Plane'
    slice1.HyperTreeGridSlicer = 'Plane'
    slice1.SliceOffsetValues = [0.0]
    slice1.SliceType.Origin = [7.0155, 7.0155, 7.0155]
    slice1.HyperTreeGridSlicer.Origin = [7.0155, 7.0155, 7.0155]
    slice1.SliceType.Normal = [0.0, 1.0, 0.0]

    print('Made slice')

    mergeBlocks = MergeBlocks(Input=slice1)
    mergeBlocks.OutputDataSetType = 'Unstructured Grid'
    mergeBlocks.MergePoints = 1
    mergeBlocks.Tolerance = 0.0
    mergeBlocks.ToleranceIsAbsolute = 0

    print('Merged blocks')

    t_ini = 0
    t_fin = 2

    z_list = []
    time_list = []

    print('Entering time loop')

    for i in range(t_ini,t_fin+1,1):

        animationScene1 = GetAnimationScene()

        # update animation scene based on data timesteps
        animationScene1.UpdateAnimationUsingDataTimeSteps()

        # Properties modified on animationScene1
        animationScene1.AnimationTime = i

        # get the time-keeper
        timeKeeper1 = GetTimeKeeper()

        UpdatePipeline(time=i, proxy=case_data)

        UpdatePipeline(time=i, proxy=mergeBlocks)

        list = paraview.servermanager.Fetch(mergeBlocks)
        points = np.array(list.GetPoints().GetData())

        selected_rows = points[points[:, 0] == 10.52325]
        selected_y_values = selected_rows[:, 1]
        selected_z_values = selected_rows[:, 2]    
        max_z_value = np.max(selected_z_values)
        z_list.append(max_z_value)
        time_list.append(i)
        print('Calculated ak2 at time = '+str(i))

    z_floats = [float(x) for x in z_list]
    time_floats = [float(x) for x in time_list]
    value_to_add = [{'Time':time_floats, 'ak2':z_floats}]
    value_json = json.dumps(value_to_add)
        
    return value_json

if __name__ == "__main__":

    HDpath = sys.argv[1]
    
    case_name = sys.argv[2]

    df_bytes = pvpy(HDpath,case_name)

    print(df_bytes)












