### Stirred_Vessel_Automation_simulation_run, tailored for Paraview 5.8.1
### Tracking of kinetic energy: ALL time steps
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

def pvpy(HDpath,case_name,rho_l,rho_g):

    path = os.path.join(HDpath,case_name,'postProcessing')
    os.chdir(path)

    ### find the final time steps ###
    pvdfiles = glob.glob('VAR_*_time=*.pvd')
    #pvdfile = f'VAR_{case_name}.pvd'
    pvdfile = 'VAR_case2_full_z.pvd'
    timestep = int(glob.glob('VAR_*_*.vtr')[0].split("_")[-1].split(".")[0])

    case_data = PVDReader(FileName=pvdfile)
    case_data.CellArrays = []
    case_data.PointArrays = ['Interface','Velocity']
    case_data.ColumnArrays = []

    print('Read data')

    rho_g = float(rho_g)
    rho_l = float(rho_l)
    t_ini = 0
    t_fin = 1

    Ek_list = []
    time_list = []

    print('Entering time loop')

    for i in range(t_ini,t_fin+1,1):

        clip1 = Clip(Input=case_data)
        clip1.ClipType = 'Cylinder'
        clip1.HyperTreeGridClipper = 'Cylinder'
        clip1.Scalars = ['POINTS', 'Interface']
        clip1.ClipType.Axis = [0.0, 0.0, 1.0]
        clip1.ClipType.Radius = 6.8

        print('Made cylinder clip')

        UpdatePipeline(time=i, proxy=clip1)

        clip2 = Clip(Input=clip1)
        clip2.ClipType = 'Plane'
        clip2.HyperTreeGridClipper = 'Plane'
        clip2.Scalars = ['POINTS', 'Interface']
        clip2.ClipType.Origin = [7.0155, 7.0155, 7.0155]
        clip2.HyperTreeGridClipper.Origin = [7.0155, 7.0155, 7.0155]
        clip2.Invert = 0

        print('Made plane clip')

        UpdatePipeline(time=i, proxy=clip2)

        # create a new 'Calculator'
        calculator1 = Calculator(Input=clip2)
        calculator1.ResultArrayName = 'H'
        calculator1.Function = '((Interface/abs(Interface))+1)/2'

        print('Calculated H')

        UpdatePipeline(time=i, proxy=calculator1)

        # create a new 'Calculator'
        calculator2 = Calculator(Input=calculator1)
        calculator2.ResultArrayName = 'rho'
        calculator2.Function = f'{rho_g} + ({rho_l} - {rho_g})*H'

        print('Calculated rho')

        UpdatePipeline(time=i, proxy=calculator2)

        # create a new 'Calculator'
        calculator3 = Calculator(Input=calculator2)
        calculator3.ResultArrayName = 'Ek'
        calculator3.Function = '(1/2)*(rho)*(mag(Velocity)^2)'

        print('Calculated Eki')

        UpdatePipeline(time=i, proxy=calculator3)

        animationScene1 = GetAnimationScene()

        # update animation scene based on data timesteps
        animationScene1.UpdateAnimationUsingDataTimeSteps()

        # Properties modified on animationScene1
        animationScene1.AnimationTime = i

        # get the time-keeper
        timeKeeper1 = GetTimeKeeper()

        UpdatePipeline(time=i, proxy=case_data)

        UpdatePipeline(time=i, proxy=calculator3)

        integrateVariables1 = IntegrateVariables(registrationName='IntegrateVariables1', Input=calculator3)
        integrateVariables1.DivideCellDataByVolume = 0
        UpdatePipeline(time=i, proxy=integrateVariables1)
        integrate_object = paraview.servermanager.Fetch(integrateVariables1)
        Ek = np.array(integrate_object.GetPointData().GetArray('Ek'))
        time = np.full((1, 1), i)
        Ek = np.full((1, 1), Ek)
        Ek_list.append(Ek)
        time_list.append(time)
        Ek_list[0] = 0
        time_list[0] = 0
        print('Calculated kinetic energy at time = '+str(i))

    Ek_floats = [float(x) for x in Ek_list]
    time_floats = [float(x) for x in time_list]
    value_to_add = [{'Time':time_floats, 'Ek':Ek_floats}]
    value_json = json.dumps(value_to_add)
        
    return value_json

if __name__ == "__main__":

    HDpath = sys.argv[1]
    case_name = sys.argv[2]
    rho_l = sys.argv[3]
    rho_g = sys.argv[4]

    df_bytes = pvpy(HDpath,case_name,rho_l,rho_g)

    print(df_bytes)












