### Interfacial_Oscillations_Automation_simulation_run, tailored for Paraview 5.8.1
### Tracking of insterfacial area: ALL time steps
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

    timestep = int(glob.glob('VAR_*_*.vtr')[0].split("_")[-1].split(".")[0])

    case_data = PVDReader(FileName=pvdfile)
    case_data.CellArrays = []
    case_data.PointArrays = ['Interface']
    case_data.ColumnArrays = []

    print('Read data')

    t_ini = 0
    t_fin = 100

    area_list = []
    time_list = []

    print('Entering time loop')

    for i in range(t_ini,t_fin+1,1):

        contour1 = Contour(Input=case_data)
        contour1.ContourBy = ['POINTS', 'Interface']
        contour1.Isosurfaces = [0.0]
        contour1.PointMergeMethod = 'Uniform Binning'

        print('Made contour')

        UpdatePipeline(time=i, proxy=contour1)

        clip1 = Clip(Input=contour1)
        clip1.ClipType = 'Cylinder'
        clip1.HyperTreeGridClipper = 'Cylinder'
        clip1.Scalars = ['POINTS', 'Interface']
        clip1.ClipType.Axis = [0.0, 0.0, 1.0]
        clip1.ClipType.Radius = 6.8

        print('Made clip')

        UpdatePipeline(time=i, proxy=clip1)

        cellSize1 = CellSize(Input=clip1)

        print('Calculated cell sizes')

        UpdatePipeline(time=timestep, proxy=cellSize1)

        animationScene1 = GetAnimationScene()

        # update animation scene based on data timesteps
        animationScene1.UpdateAnimationUsingDataTimeSteps()

        # Properties modified on animationScene1
        animationScene1.AnimationTime = i

        # get the time-keeper
        timeKeeper1 = GetTimeKeeper()

        UpdatePipeline(time=i, proxy=case_data)

        UpdatePipeline(time=i, proxy=cellSize1)

        integrateVariables1 = IntegrateVariables(registrationName='IntegrateVariables1', Input=cellSize1)
        integrateVariables1.DivideCellDataByVolume = 0
        UpdatePipeline(time=i, proxy=integrateVariables1)
        integrate_object = paraview.servermanager.Fetch(integrateVariables1)
        area = integrate_object.GetCellData().GetArray('Area').GetValue(0)
        time = np.full((1, 1), i)
        area = np.full((1, 1), area)
        area_list.append(area)
        time_list.append(time)
        print('Calculated interfacial area at time = '+str(i))

    area_floats = [float(x) for x in area_list]
    time_floats = [float(x) for x in time_list]
    value_to_add = [{'Time':time_floats, 'Int_area':area_floats}]
    value_json = json.dumps(value_to_add)
        
    return value_json

if __name__ == "__main__":

    HDpath = sys.argv[1]
    
    case_name = sys.argv[2]

    df_bytes = pvpy(HDpath,case_name)

    print(df_bytes)












