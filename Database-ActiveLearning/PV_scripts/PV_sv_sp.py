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
import numpy as np
import os 
import glob

if __name__ == "__main__":

    HDpath = sys.argv[1]#'/media/fl18/Elements/surf_ML/'#
    
    case_name = sys.argv[2]#'run_svtest_3'#

    R = 0.025
    H = 0.051
    C = float(sys.argv[3])

    path = os.path.join(HDpath,case_name)
    os.chdir(path)

    pvdfile = f'VAR_{case_name}_time=0.00000E+00.pvd'
    # timestep = int(glob.glob('VAR_*_*.vtr')[0].split("_")[-1].split(".")[0])
    timestep=23

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
    
    UpdatePipeline(time=timestep, proxy=mergeBlocks)

    ### create a new 'GradientsofUnstructuredDataSet' ###
    gradient = Gradient(Input=mergeBlocks)
    gradient.ScalarArray = ['POINTS', 'Velocity']
    gradient.BoundaryMethod = 'Non-Smoothed'
    gradient.Dimensionality = 'Three'
    gradient.ComputeGradient = 1
    gradient.ResultArrayName = 'dudx'
    gradient.FasterApproximation = 0
    gradient.ComputeDivergence = 0
    gradient.DivergenceArrayName = 'Divergence'
    gradient.ComputeVorticity = 0
    gradient.VorticityArrayName = 'Vorticity'
    gradient.ComputeQCriterion = 0
    gradient.QCriterionArrayName = 'Q Criterion'
    gradient.ContributingCellOption = 'Dataset Max'
    gradient.ReplacementValueOption = 'NaN'

    UpdatePipeline(time=timestep, proxy=gradient)
    
    ### create a new 'Programmable Filter' ###
    programmableFilter = ProgrammableFilter(Input=gradient)
    programmableFilter.OutputDataSetType = 'Same as Input'
    programmableFilter.Script = ''
    programmableFilter.RequestInformationScript = ''
    programmableFilter.RequestUpdateExtentScript = ''
    programmableFilter.CopyArrays = 0
    programmableFilter.PythonPath = ''

    ### properties modified on programmableFilter ###
    programmableFilter.Script = '''
import numpy as np
from numpy import linalg as LA
np.seterr(divide='ignore', invalid='ignore')
grad = inputs[0].PointData['dudx']

U = inputs[0].PointData['Velocity']
P = inputs[0].PointData['Pressure']

D = (grad + np.transpose(grad, axes=(0, 2, 1))) / 2
omega = (grad - np.transpose(grad, axes=(0, 2, 1))) / 2

eig_val, eig_vect = LA.eig(D)
maxeig = np.max(eig_val, axis=1)

DD = (np.sum(np.multiply(D,D),axis=(1,2)))
o2 = (np.sum(np.multiply(omega,omega),axis=(1,2)))

Q = np.divide((DD - o2),(DD + o2))

output.PointData.append(Q, 'Q')
output.PointData.append(P,'Pres')
output.PointData.append(U,'U')
'''

    programmableFilter.RequestInformationScript = ''
    programmableFilter.RequestUpdateExtentScript = ''
    programmableFilter.PythonPath = ''
    
    UpdatePipeline(time=timestep, proxy=programmableFilter)
    
    print('Merge blocks, gradient and programmable filter performed correctly')

    ### create a new 'clip' to only include the cylinder ###
    clip = Clip(Input=programmableFilter)
    clip.ClipType = 'Cylinder'
    clip.HyperTreeGridClipper = 'Cylinder'
    clip.Invert = 1
    clip.ClipType.Axis = [0.0, 0.0, 1.0]
    clip.ClipType.Radius = R

    UpdatePipeline(time=timestep, proxy=clip)

    ### Looping to get hydrodynamics across the height of cylinder ###
    n_slices = 100
    ini = 0.05/n_slices
    H_range = np.linspace(ini,0.05-ini,n_slices)

    # slice to extract cross-sectional hydropdynamic value ###
    slice = Slice(Input=clip)
    slice.SliceType = 'Plane'
    slice.HyperTreeGridSlicer = 'Plane'
    slice.UseDual = 0
    slice.Crinkleslice = 0
    slice.Triangulatetheslice = 1
    slice.Mergeduplicatedpointsintheslice = 1
    slice.SliceOffsetValues = [0.0]

    ###
    slice.SliceType.Origin = [H/2, H/2, ini]
    slice.SliceType.Normal = [0.0, 0.0, 1.0]

    UpdatePipeline(time=timestep, proxy=slice)

    ### Features to be extracted ###
    Q_list = []
    P_list = []
    Ur_list = []
    Uth_list = []
    Uz_list = []
    H_list = []

    for i in H_range:

        ### moving up the slice ###
        slice.SliceType.Origin = [H/2, H/2, i]

        # update change
        UpdatePipeline(time=timestep, proxy=slice)

        ### create a new 'Integrate Varaibles' in slice to extract features ###
        integrateVariables = IntegrateVariables(Input=slice)
        integrateVariables.DivideCellDataByVolume = 1
        UpdatePipeline(time=timestep, proxy=integrateVariables)

        # Extract flow data objects
        flow_object = paraview.servermanager.Fetch(integrateVariables)
        area = flow_object.GetCellData().GetArray('Area').GetValue(0)

        # Extract features: values
        values_to_extract = ['Q', 'Pres']
        values_A = {var: flow_object.GetPointData().GetArray(var).GetValue(0) 
                    for var in values_to_extract}
        # Extract features: tuples
        tuples_to_extract = ['U']
        n_Elements = flow_object.GetPointData().GetArray('U').GetNumberOfComponents()
        tuples_A = {'U': [flow_object.GetPointData().GetArray('U').GetValue(i)
                    for i in range(n_Elements)]
                    }
        
        # compute the area average value
        Q = values_A['Q']/area
        P = values_A['Pres']/area
        Ur = tuples_A['U'][0]/area
        Uth = tuples_A['U'][1]/area
        Uz = tuples_A['U'][2]/area

        # save to list
        H_list.append(i)
        Q_list.append(Q)
        P_list.append(P)
        Ur_list.append(Ur)
        Uth_list.append(Uth)
        Uz_list.append(Uz)

    print('Flow features extracted correctly from vertical slices.')

    ### get the velocity field along a line one the slice ###
    # create a new 'slice' at the center of the impeller #
    slice_c = Slice(Input=clip)
    slice_c.SliceType = 'Plane'
    slice_c.HyperTreeGridSlicer = 'Plane'
    slice_c.UseDual = 0
    slice_c.Crinkleslice = 0
    slice_c.Triangulatetheslice = 1
    slice_c.Mergeduplicatedpointsintheslice = 1
    slice_c.SliceOffsetValues = [0.0]
    ### impeller center = Clearance
    slice_pos = C
    n_samples = 100
    slice_c.SliceType.Origin = [H/2, H/2, slice_pos]
    slice_c.SliceType.Normal = [0.0, 0.0, 1.0]

    # create a new 'plot over line' to get the data along the center line of cylinder #
    plotOverLine1 = PlotOverLine(Input=slice_c)
    plotOverLine1.Point1 = [H/2, H/2, slice_pos]
    plotOverLine1.Point2 = [H/2+0.025, H/2, slice_pos]
    plotOverLine1.SamplingPattern = 'Sample Uniformly'
    plotOverLine1.Resolution = n_samples
    plotOverLine1.PassPartialArrays = 1
    plotOverLine1.PassCellArrays = 0
    plotOverLine1.PassPointArrays = 0
    plotOverLine1.PassFieldArrays = 1
    UpdatePipeline(time=timestep, proxy=plotOverLine1)

    line_object = paraview.servermanager.Fetch(plotOverLine1)

    # Extract features
    arc_list = []
    Q_line_list = []
    Ur_line_list = []
    Uz_line_list = []
    for i in range(n_samples):
        arc_sample = line_object.GetPointData().GetArray('arc_length').GetValue(i)
        Q_line_sample = line_object.GetPointData().GetArray('Q').GetValue(i)

        Ur_line_sample = line_object.GetPointData().GetVectors('U').GetComponent(i, 0)#(index, component)
        Uz_line_sample = line_object.GetPointData().GetVectors('U').GetComponent(i, 2)
        
        # save to list
        arc_list.append(arc_sample)
        Q_line_list.append(Q_line_sample)
        Ur_line_list.append(Ur_line_sample)
        Uz_line_list.append(Uz_line_sample)

    print('Flow features extracted correctly over line.')

    data = [{'Height': H_list, 
        'Q':Q_list, 'Pressure': P_list, 'Ur': Ur_list,'Uth':Uth_list,'Uz':Uz_list,
        'arc_length': arc_list,'Q_over_line': Q_line_list,
        'Ur_over_line':Ur_line_list, 'Uz_over_line': Uz_line_list}]



    df_sp = pd.DataFrame(data, columns=['Height', 'Q', 'Pressure', 'Ur', 'Uth', 'Uz',
                                     'arc_length', 'Q_over_line', 'Ur_over_line', 'Uz_over_line'])
    df_jason = df_sp.to_json(orient='split', double_precision=15)

    print(df_jason)

