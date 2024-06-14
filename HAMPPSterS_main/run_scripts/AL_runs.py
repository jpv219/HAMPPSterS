### ALeRT AL sampling runs, tailored for BLUE 12.5.1
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
from LHS_Dataspace import SMX_SP_UR
from logger import configure_logger
import io
import contextlib
import csv
import pickle
import configparser
import os

log = configure_logger("AL_dt")

log.info('-' * 100)
log.info('-' * 100)
log.info('Parametric study launch')
log.info('-' * 100)
log.info('-' * 100)


# read data from config file
config = configparser.ConfigParser()
package_dir = os.path.dirname(os.path.abspath(__file__)) # by tracing the file directory
config.read(os.path.join(package_dir, 'config/nkahouad_config.ini'))

case = "sp_geom"
AL_space = 'dt'
nruns = 15
nruns_list = [str(i+70) for i in range(1, nruns + 1)]
runname_list = ['run_AL_dt_' + item for item in nruns_list]
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

## Parameters to vary in the sample space
AL_dict = {'Bar_Width (mm)': [1,25],'Bar_Thickness (mm)': [4.0,8.77],
            'Radius (mm)': [6.12,11.9],'Nbars':[3,16],
            'Flowrate (m3/s)': [5e-7,1e-2],'Angle':[25,80], 'NElements': [2,6]}

Re_rules = (141, 400)

captured_output = io.StringIO()

LHS_sampler = SMX_SP_UR(AL_dict, nruns, Re_rules)

with contextlib.redirect_stdout(captured_output):
    psdict = LHS_sampler()
    log.info('-' * 100)
    log.info('Modifications to the DOE')
    log.info(captured_output.getvalue())

log.info('-' * 100)
log.info('\n'+ psdict.to_string())
log.info('-' * 100)

### Save LHS dictionary for later

with open(f'../DOE/LHS_{case}_10.pkl', 'wb') as file:
   pickle.dump(psdict, file)

### Termination condition to be written as: check_value --operator-- cond_csv_limit. Once condition is false, stop job
### cond_csv determines which condition to use as stopping criteria from the csv

n0 = 0.0063
ninf = 0.00086
k = 0.4585
m = 0.577

psdict['cond_csv_limit'] = psdict['Re'].apply(lambda Re: (1-Re/500)*ninf + 0.90*((n0-ninf)/(1+(k*Re)**m)))

cond_csv = ps.plist("cond_csv",["Time(s)"])
conditional = ps.plist("conditional",["<"])

bar_width_list = list(map(str,psdict['Bar_Width (mm)'] / 1000))
bar_thickness_list = list(map(str,psdict['Bar_Thickness (mm)'] / 1000))
bar_angle_list = list(map(str,psdict['Angle']))
radius_list = list(map(str,psdict['Radius (mm)'] / 1000))
nbars_list = list(map(str,psdict['Nbars']))
flowrate_list = list(map(str,psdict['Flowrate (m3/s)']))
smx_pos_list = list(map(str,psdict['SMX_pos (mm)'] / 1000))
nele_list = list(map(str,psdict['NElements']))

# Dynamically changing termination condition
cond_csv_limit_list = list(map(str,psdict['cond_csv_limit']))

# Combine the lists
data = list(zip(bar_width_list, bar_thickness_list, 
                bar_angle_list, radius_list, nbars_list, 
                flowrate_list, smx_pos_list,nele_list,
                cond_csv_limit_list))

# Save the combined data into a CSV file
with open(f'../params/parameters_sp_AL_{AL_space}_10.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['bar_width', 'bar_thickness', 'bar_angle', 'radius', 'nbars', 'flowrate', 'smx_pos','NElements','cond_csv_limit'])
    writer.writerows(data)

bar_width = ps.plist("bar_width",bar_width_list)
bar_thickness = ps.plist("bar_thickness",bar_thickness_list)
bar_angle = ps.plist("bar_angle",bar_angle_list)
pipe_radius = ps.plist("pipe_radius",radius_list)
n_bars = ps.plist("n_bars",nbars_list)
flowrate = ps.plist("flowrate",flowrate_list)
smx_pos = ps.plist("smx_pos",smx_pos_list)
n_ele = ps.plist("n_ele",nele_list)
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
