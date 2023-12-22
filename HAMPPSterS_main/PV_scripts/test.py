### Stirred_Vessel_Automation_simulation_run, tailored for Paraview 5.8.1
### Tracking of wave oscillations: ALL time steps
### to be run locally
### Author: Paula Pico,
### First commit: Dec, 2023
### Version: 5.0
### Department of Chemical Engineering, Imperial College London
#####################################################################

import sys
if '--virtual-env' in sys.argv:
  virtualEnvPath = sys.argv[sys.argv.index('--virtual-env') + 1]
  # Linux
  virtualEnv = virtualEnvPath + '/bin/activate_this.py'
  # Windows
  # virtualEnv = virtualEnvPath + '/Scripts/activate_this.py'
  if sys.version_info.major < 3:
    execfile(virtualEnv, dict(__file__=virtualEnv))
  else:
    exec(open(virtualEnv).read(), {'__file__': virtualEnv})


import pandas as pd
import numpy as np
import os 
import glob
import shutil
from paraview.simple import *

print(2)