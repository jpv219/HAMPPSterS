from paraview.simple import *
import os
import glob
import pandas as pd
import sys
import numpy as np

np.set_printoptions(threshold=sys.maxsize)


def pvspPP(HDpath,case_name,len,rad):

    # find source, modify PVD file to be read and set it to last timestep saved as vtr.
    path = os.path.join(HDpath,case_name)  
    os.chdir(path)

    R = float(rad)
    L = float(len)

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

    # create a new 'Merge Blocks'
    mergeBlocks1 = MergeBlocks(registrationName='MergeBlocks1', Input=case_data)
    mergeBlocks1.OutputDataSetType = 'Unstructured Grid'
    mergeBlocks1.MergePartitionsOnly = 0
    mergeBlocks1.MergePoints = 1
    mergeBlocks1.Tolerance = 0.0
    mergeBlocks1.ToleranceIsAbsolute = 0

    UpdatePipeline(time=timestep, proxy=mergeBlocks1)

    # create a new 'Gradient'
    gradient1 = Gradient(registrationName='Gradient1', Input=mergeBlocks1)
    gradient1.ScalarArray = ['POINTS', 'Velocity']
    gradient1.BoundaryMethod = 'Non-Smoothed'
    gradient1.Dimensionality = 'Three'
    gradient1.ComputeGradient = 1
    gradient1.ResultArrayName = 'dudx'
    gradient1.FasterApproximation = 0
    gradient1.ComputeDivergence = 0
    gradient1.DivergenceArrayName = 'Divergence'
    gradient1.ComputeVorticity = 0
    gradient1.VorticityArrayName = 'Vorticity'
    gradient1.ComputeQCriterion = 0
    gradient1.QCriterionArrayName = 'Q Criterion'
    gradient1.ContributingCellOption = 'Dataset Max'
    gradient1.ReplacementValueOption = 'NaN'


    UpdatePipeline(time=timestep, proxy=gradient1)

    # create a new 'Programmable Filter'
    programmableFilter1 = ProgrammableFilter(registrationName='ProgrammableFilter1', Input=gradient1)
    programmableFilter1.OutputDataSetType = 'Same as Input'
    programmableFilter1.Script = ''
    programmableFilter1.RequestInformationScript = ''
    programmableFilter1.RequestUpdateExtentScript = ''
    programmableFilter1.CopyArrays = 0
    programmableFilter1.PythonPath = ''

    # Properties modified on programmableFilter1
    programmableFilter1.Script = """import numpy as np
from numpy import linalg as LA
np.seterr(divide='ignore', invalid='ignore')
grad = inputs[0].PointData['dudx']

u = inputs[0].PointData['Velocity']
P = inputs[0].PointData['Pressure']

D = (grad + np.transpose(grad, axes=(0, 2, 1))) / 2
omega = (grad - np.transpose(grad, axes=(0, 2, 1))) / 2

eig_val, eig_vect = LA.eig(D)
maxeig = np.max(eig_val, axis=1)

DD = (np.sum(np.multiply(D,D),axis=(1,2)))
o2 = (np.sum(np.multiply(omega,omega),axis=(1,2)))

gamma = np.sqrt(2*DD)
e_dis = 2*(0.615/1364)*DD
emax = np.divide(maxeig,np.sqrt(DD))

Q = np.divide((DD - o2),(DD + o2))

output.PointData.append(gamma, 'Gamma')
output.PointData.append(e_dis, 'Ediss')
output.PointData.append(emax, 'emax')
output.PointData.append(Q, 'Q')
output.PointData.append(P,'Pres')
output.PointData.append(u,'u')"""

    programmableFilter1.RequestInformationScript = ''
    programmableFilter1.RequestUpdateExtentScript = ''
    programmableFilter1.PythonPath = ''


    UpdatePipeline(time=timestep, proxy=programmableFilter1)

    print('Merge blocks, gradient and programmable filter performed correctly')

    # create a new 'Clip' to remove outer domain and leave the inner pipe only
    clip1 = Clip(registrationName='Clip1', Input=programmableFilter1)
    clip1.ClipType = 'Cylinder'
    clip1.HyperTreeGridClipper = 'Cylinder'
    clip1.Invert = 1
    clip1.Crinkleclip = 0
    clip1.Exact = 0
    clip1.ClipType.Axis = [1.0, 0.0, 0.0]
    clip1.ClipType.Radius = R

    UpdatePipeline(time=timestep, proxy=clip1)

    # create a new 'Threshold' to remove domain occupied by solids
    threshold1 = Threshold(registrationName='Threshold1', Input=clip1)
    threshold1.Scalars = ['POINTS', 'Q']
    threshold1.LowerThreshold = -1.0
    threshold1.UpperThreshold = 1.0
    threshold1.ThresholdMethod = 'Between'
    threshold1.AllScalars = 1
    threshold1.UseContinuousCellRange = 0
    threshold1.Invert = 0

    UpdatePipeline(time=timestep, proxy=threshold1)
    
    ### LOOPING TO CALCULATE HYDRODYNAMICS ACROSS THE LENGTH OF THE MIXER

    n_datap = 100
    ini = L/n_datap
    L_range = np.linspace(ini,L-ini,n_datap)

    # Slice 1 to extract cross-sectional hydrodynamic values
    slice1 = Slice(registrationName='Slice1', Input=threshold1)
    slice1.SliceType = 'Plane'
    slice1.HyperTreeGridSlicer = 'Plane'
    slice1.UseDual = 0
    slice1.Crinkleslice = 0
    slice1.Triangulatetheslice = 1
    slice1.Mergeduplicatedpointsintheslice = 1
    slice1.SliceOffsetValues = [0.0]

    ### 
    slice1.SliceType.Origin = [ini, R, R]
    slice1.SliceType.Normal = [1.0, 0.0, 0.0]
    slice1.SliceType.Offset = 0.0

    UpdatePipeline(time=timestep, proxy=slice1)


    # Features to be extracted
    emax_list = []
    Q_list = []
    ediss_list = []
    gamma_list = []
    P_list = []
    u_list = []
    L_list = []

    ### Looping data extraction for n_datap points across the mixer's length
    for i in L_range:

        # Advance the slice across the mixer
        slice1.SliceType.Origin = [i, R, R]

        # Update changes
        UpdatePipeline(time=timestep, proxy=slice1)

        # create a new 'Integrate Variables' in slice 1 to extract cross-sectional average hydrodynamical features
        integrateVariables1 = IntegrateVariables(registrationName='IntegrateVariables1', Input=slice1)
        integrateVariables1.DivideCellDataByVolume = 1
        UpdatePipeline(time=timestep, proxy=integrateVariables1)

        # Extract flow data objects
        flow_object = paraview.servermanager.Fetch(integrateVariables1)
        area = flow_object.GetCellData().GetArray('Area').GetValue(0)
        
        # Extract features
        variables_to_extract = ['emax', 'Q', 
                                'Ediss', 
                                'Gamma', 'Pres', 'u']
        values_A = {var: flow_object.GetPointData().GetArray(var).GetValue(0) 
                    for var in variables_to_extract}

        # Compute area averaged value
        emax = values_A['emax']/area
        Q = values_A['Q']/area
        ediss = values_A['Ediss']/area
        gamma = values_A['Gamma']/area
        P = values_A['Pres']/area
        u = values_A['u']/area

        # Save to list
        emax_list.append(emax)
        Q_list.append(Q)
        ediss_list.append(ediss)
        gamma_list.append(gamma)
        P_list.append(P)
        u_list.append(u)
        L_list.append(i)

    data = {'Length': L_list, 'e_max':emax_list, 
            'Q': Q_list, 'E_diss':ediss_list, 'Gamma': gamma_list, 
            'Pressure': P_list, 'Velocity': u_list}
    
    df = pd.DataFrame(data)

    print('Flow features extracted correctly from integrate variables')


    df_json = df.to_json(orient='split', double_precision=15)

    return df_json
        
if __name__ == "__main__":

    HDpath = sys.argv[1]
    
    case_name = sys.argv[2]

    L = sys.argv[3]

    R = sys.argv[4]

    df_bytes = pvspPP(HDpath,case_name, L, R)

    print(df_bytes)
