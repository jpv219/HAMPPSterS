### Stirred_Vessel_Automation_simulation_run, tailored for Paraview 5.10
### Multiphase dispersion metrics post-processing script
### to be run locally
### Author: Fuyue Liang,
### First commit: Sep, 2023
### Version: 1.0
### Department of Chemical Engineering, Imperial College London
#####################################################################
from paraview.simple import *
import csv
import numpy as np
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

    threshold = Threshold(Input=calculator1)
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
            


items = [
        'Bi0001','Bi0002',
        'Bi0004',
        'Bi001','Bi1'
        ]

for item in items:
    initial = 256
    stop = 320
    n=1
    work_dir = '/media/fl18/7fdd513c-7661-4b00-9133-33feed844edf/SMX/Surf_Emu/emu_New_'+str(item)
#     save_dir = '/media/fl18/7fdd513c-7661-4b00-9133-33feed844edf/SMX/Surf_Emu/Pyplots/datas/RNN'
    
    # Create a csv file
    headerlist = ['Time','DropVolume','Gammatilde']
    with open(str(item)+'_0.csv', 'w') as file:
        dw = csv.DictWriter(file, delimiter=',', fieldnames=headerlist)
        dw.writeheader()
        
    # Create a VAR_DSD.pvd
    source_destn = str(work_dir)+'/VAR_DSD_'+str(item)+'.pvd'

    with open('VAR_DSD.pvd', 'r') as file:
        filedata = file.read()
    filedata = filedata.replace('5hz_B05', 'New_'+str(item))
    filedata = filedata.replace('_num', '_'+str(initial))
    with open(str(source_destn), 'w') as file:
        file.write(filedata)
    
#    stop = len(glob.glob1(str(work_dir), 'VAR_emu_New_'+str(item)+'_0_*'))

    for i in range(initial, stop, n):
        #################################
        ### VAR_DSD
        #################################
        # Read in the file
        with open(str(work_dir)+'/VAR_DSD_'+str(item)+'.pvd', 'r') as file :
            filedata = file.read()

        # Replace the target string
        filedata = filedata.replace('_' +str(initial)+ '.vtr', '_' +str(i)+ '.vtr')

        # Write the file out again
        with open(str(work_dir)+'/VAR_DSD_'+str(item)+'.pvd', 'w') as file:
            file.write(filedata)
            
        ##################################
        ### detection.py
        ###################################
        fname = str(work_dir)+'/VAR_DSD_'+str(item)+'.pvd'

        data = PVDReader(FileName=fname)
        mergeBlocks = MergeBlocks(Input=data)

        clip = Clip(Input=mergeBlocks)
        clip.Scalars = ['POINTS', 'Interface']
        clip.ClipType = 'Scalar'
        clip.Value = 0.0
        clip.Invert = 1

        # tag droplets as connected regions
        connectivity = Connectivity(Input=clip)
        connectivity.RegionIdAssignmentMode = 'Cell Count Descending'
    #     UpdatePipeline(time=i, proxy=data)
       
        # create a new 'Calculator'
        calculator1 = Calculator(registrationName='Calculator1', Input=connectivity)
        calculator1.AttributeType = 'Point Data'
        calculator1.CoordinateResults = 0
        calculator1.ResultNormals = 0
        calculator1.ResultTCoords = 0
        calculator1.ResultArrayName = 'Result'
        calculator1.Function = ''
        calculator1.ReplaceInvalidResults = 1
        calculator1.ReplacementValue = 0.0
        calculator1.ResultArrayType = 'Double'
        
        # Properties modified on calculator1
        calculator1.ResultArrayName = 'gammatilde'
        calculator1.Function = 'InterfaceSurfactantConcentration/(1e-5)'

        # find lower and upper bound indices of droplet list
        region = paraview.servermanager.Fetch(connectivity)
        region_range = region.GetCellData().GetArray('RegionId').GetRange()

        threshold = Threshold(Input=calculator1)
        threshold.Scalars = ['POINTS', 'RegionId']
        
        # create new IntegrateVariables
        integral = IntegrateVariables(Input=threshold)

        lower_bound = int(region_range[0]+1)
        upper_bound = int(region_range[1])
        print(region_range, lower_bound)

        volume_list = []
        gammatilde_list = []

        for j in range(lower_bound, upper_bound+1):

            # select individual droplet
            #tolerance = 0.1
            threshold.ThresholdRange = [j, j]

            # collect data
            data_object = paraview.servermanager.Fetch(integral)
            volume = data_object.GetCellData().GetArray('Volume').GetValue(0)
            gammatilde_vol = data_object.GetPointData().GetArray('gammatilde').GetValue(0)
            gammatilde = gammatilde_vol/volume
          #  print "INFO: collecting droplet {}, volume =  m^3".format(i, volume)
            volume_list.append(volume)
            gammatilde_list.append(gammatilde)
            
            print(str(item)+'_'+str(j)+' done')
            

        thelist = [i/32/5, np.array(volume_list), np.array(gammatilde_list)]
        with open (str(item)+'_0.csv', 'a') as file:
            writer = csv.writer(file)
            writer.writerow(thelist)

        Disconnect()
        Connect()

        print(str(item) + '_' +str(i)+' is created' )
        initial = i
        i= i + n

