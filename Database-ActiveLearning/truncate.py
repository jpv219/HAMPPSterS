### Stirred_Vessel_Automation_simulation_run, tailored for Paraview 5.10
### Multiphase dispersion metrics post-processing script: Truncate snaps [256,704]
### to be run locally
### Author: Fuyue Liang,
### First commit: Sep, 2023
### Version: 1.0
### Department of Chemical Engineering, Imperial College London
#####################################################################

import sys
import glob
import os


if __name__ == "__main__":

    HDpath = sys.argv[1]#'/media/fl18/Elements/surf_ML/'#
    
    case_name = sys.argv[2]#'truncate_test'#

    path = os.path.join(HDpath,case_name)
    os.chdir(path)

    # define the truncating time range #
    initial = 256

    # list files in the folder #
    vtkfiles = glob.glob('VAR_*.vtk')

    # iteration #
    for filename in vtkfiles:
        try:
            timestep = int(filename.split('_')[-1].split('.vtk')[0])
        except (ValueError, IndexError):
            # skip files that don't follow the expected naming convention
            continue

        if timestep < initial:
            file_path = os.path.join(path, filename)
            os.remove(file_path)
    truned_vtkfiles = glob.glob('VAR_*.vtk')
    timesteps = sorted([int(filename.split('_')[-1].split('.vtk')[0]) for filename in truned_vtkfiles])
    print(f'Currently vtk files lies between snaps: ({timesteps[0]}, {timesteps[-1]}).')

