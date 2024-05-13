### ALeRT GSx sampling runs, tailored for BLUE 12.5.1
### Main parametric running script
### to be run locally
### Author: Juan Pablo Valdes,
### First commit: July, 2023
### Version: 6.0
### Department of Chemical Engineering, Imperial College London
#######################################################################################################################################################################################
#######################################################################################################################################################################################

# Local path
import sys
sys.path.append('/home/jpv219/Documents/ML/SMX_DeepLearning/HAMPPSterS_main/')

import psweep as ps
from Mixing_run_scheduling import SMSimScheduling
import pandas as pd
from logger import configure_logger
import math
import configparser
import os

log = configure_logger("AL_gsx")

log.info('-' * 100)
log.info('-' * 100)
log.info('Parametric study launch')
log.info('-' * 100)
log.info('-' * 100)


# read data from config file
config = configparser.ConfigParser()
package_dir = os.path.dirname(os.path.abspath(__file__)) # by tracing the file directory
config.read(os.path.join(package_dir, 'config/nkovalc1_config.ini'))

case = "sp_geom"
AL_space = 'gsx'

log.info('-' * 100)
log.info('Reading GSX runs from Pickle file')
log.info('-' * 100)

GSx_space = pd.read_pickle(os.path.join(package_dir,'GSx/gsx_df.pkl'))

nruns = len(GSx_space)
nruns_list = [str(i) for i in range(1, nruns + 1)]
runname_list = ['run_AL_GSx_' + item for item in nruns_list]
log.info(f'Case {case} studied with {nruns} runs')
user = config['Run']['user']
study_ID = 'SM'

run_path = ps.plist("run_path",[config['Paths']['run_path']])
base_path = ps.plist("base_path",[config['Paths']['base_path']])
convert_path = ps.plist("convert_path",[config['Paths']['convert_path']])

case_type = ps.plist("case",[case])
user_ps = ps.plist("user",[user])
run_ID = ps.plist("run_ID",nruns_list)
run_name = ps.plist("run_name",runname_list)
study_list = ps.plist("study_ID",[study_ID])

local_path = ps.plist("local_path",[config['Paths']['local_path']])
save_path = ps.plist("save_path",[config['Paths']['save_path']])


bar_width = ps.plist("bar_width",GSx_space['Bar_Width (mm)'].tolist())
bar_thickness = ps.plist("bar_thickness",GSx_space['Bar_Thickness (mm)'].tolist())
bar_angle = ps.plist("bar_angle",GSx_space['Angle'].tolist())
pipe_radius = ps.plist("pipe_radius",GSx_space['Radius (mm)'].tolist())
n_bars = ps.plist("n_bars",GSx_space['Nbars'].tolist())
flowrate = ps.plist("flowrate",GSx_space['Flowrate (m3/s)'].tolist())
smx_pos = ps.plist("smx_pos",GSx_space['Radius (mm)'].tolist())
n_ele = ps.plist("n_ele",GSx_space['NElements'].tolist())

### Termination condition to be written as: check_value --operator-- cond_csv_limit. Once condition is false, stop job
### cond_csv determines which condition to use as stopping criteria from the csv

n0 = 0.0063
ninf = 0.00086
k = 0.4585
m = 0.577

# Dynamically changing termination condition
Re_list = [1364*(Q/(math.pi*(R/1000)**2))*((2*R)/1000)/0.615 
           for Q,R in zip(GSx_space['Flowrate (m3/s)'],GSx_space['Radius (mm)'])]

cond_csv_limit_list = [(1-Re/500)*ninf + 0.90*((n0-ninf)/(1+(k*Re)**m)) for Re in Re_list]

cond_csv = ps.plist("cond_csv",["Time(s)"])
conditional = ps.plist("conditional",["<"])

cond_csv_limit = ps.plist("cond_csv_limit",cond_csv_limit_list)

## creates parameter grid (list of dictionarys)
params = ps.pgrid(base_path,run_path,convert_path,case_type,local_path,save_path,
                  cond_csv,conditional,user_ps,study_list,
                  zip(run_ID,run_name,bar_width,bar_thickness,bar_angle,pipe_radius,
                      n_bars,flowrate,smx_pos,n_ele,cond_csv_limit))

######################################################################################################################################################################################
######################################################################################################################################################################################
log.info('-' * 100)
log.info('' * 100)


simulator = SMSimScheduling()

if __name__ == '__main__':
    df = ps.run_local(simulator.localrun, params, poolsize=5,save=True,tmpsave=True,skip_dups=True)   
