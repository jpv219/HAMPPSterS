### SMX_Automation_simulation_run, tailored for BLUE 12.5.1
### Main parametric running script
### to be run locally
### Author: Juan Pablo Valdes,
### First commit: July, 2023
### Version: 2.0
### Department of Chemical Engineering, Imperial College London

import psweep as ps
from CFD_run_scheduling import SimScheduling
from LHS_Dataspace import runDOE
from logger import configure_logger
import io
import contextlib
import csv
import pickle
import math

log = configure_logger("geom")

log.info('-' * 100)
log.info('-' * 100)
log.info('Parametric study launch')
log.info('-' * 100)
log.info('-' * 100)

case = "geom"
nruns = 32
nruns_list = [str(i) for i in range(1, nruns + 1)]
runname_list = ['run_geom_' + item for item in nruns_list]
log.info(f'Case {case} studied with {nruns} runs')
re_run = False
user = 'jpv219'

run_path = ps.plist("run_path",["/rds/general/user/jpv219/home/BLUE-12.5.1/project/ACTIVE_LEARNING/RUNS"])
base_path = ps.plist("base_path",["/rds/general/user/jpv219/home/BLUE-12.5.1/project/ACTIVE_LEARNING/BASE"])
convert_path = ps.plist("convert_path",["/rds/general/user/jpv219/home/F_CONVERT"])

case_type = ps.plist("case",[case])
user_ps = ps.plist("user",[user])
run_ID = ps.plist("run_ID",nruns_list)
run_name = ps.plist("run_name",runname_list)

local_path = ps.plist("local_path",["/home/jpv219/Documents/ML/SMX_DeepLearning/Database-ActiveLearning"])
save_path = ps.plist("save_path",["/media/jpv219/ML/Runs"])

## Parameters to vary in the sample space
max_diameter = 0.03
SMX_dict = {'Bar_Width (mm)': [1,20],'Bar_Thickness (mm)': [1,5],'Radius (mm)': [5,max_diameter*1000/2],'Nbars':[3,16],'Flowrate (m3/s)': [1e-6,1e-4],'Angle':[20,80]}

captured_output = io.StringIO()

with contextlib.redirect_stdout(captured_output):
    psdict = runDOE(SMX_dict,nruns)
    log.info('-' * 100)
    log.info('Modifications to the DOE')
    log.info(captured_output.getvalue())

log.info('-' * 100)
log.info('\n'+ psdict.to_string())
log.info('-' * 100)

### Save LHS dictionary for later

with open('DOE/LHS_Geom.pkl', 'wb') as file:
    pickle.dump(psdict, file)


### Termination condition to be written as: check_value --operator-- cond_csv_limit. Once condition is false, stop job
### cond_csv determines which condition to use as stopping criteria from the csv

psdict['cond_csv_limit'] = psdict['Radius (mm)'].apply(lambda radius: math.ceil(4 * radius * 1000) / 1000)

cond_csv = ps.plist("cond_csv",["ptx(EAST) "])
conditional = ps.plist("conditional",["<"])


## Geometry parameters

if not re_run:

    bar_width_list = list(map(str,psdict['Bar_Width (mm)'] / 1000))
    bar_thickness_list = list(map(str,psdict['Bar_Thickness (mm)'] / 1000))
    bar_angle_list = list(map(str,psdict['Angle']))
    radius_list = list(map(str,psdict['Radius (mm)'] / 1000))
    nbars_list = list(map(str,psdict['Nbars']))
    flowrate_list = list(map(str,psdict['Flowrate (m3/s)']))
    smx_pos_list = list(map(str,psdict['SMX_pos (mm)'] / 1000))

    # Dynamically changing termination condition
    cond_csv_limit_list = list(map(str,psdict['cond_csv_limit']*0.9/1000))

    # Combine the lists
    data = list(zip(bar_width_list, bar_thickness_list, bar_angle_list, 
                    radius_list, nbars_list, flowrate_list, smx_pos_list, 
                    cond_csv_limit_list))

    # Save the combined data into a CSV file
    with open('params/parameters.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['bar_width', 'bar_thickness', 'bar_angle', 'radius', 'nbars', 'flowrate', 'smx_pos','cond_csv_limit'])
        writer.writerows(data)

else:
    # Initialize empty lists for each parameter
    bar_width_list = []
    bar_thickness_list = []
    bar_angle_list = []
    radius_list = []
    nbars_list = []
    flowrate_list = []
    smx_pos_list = []
    cond_csv_limit_list = []

    # Load data from CSV file
    with open('params/parameters_geom.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            bar_width_list.append(row['bar_width'])
            bar_thickness_list.append(row['bar_thickness'])
            bar_angle_list.append(row['bar_angle'])
            radius_list.append(row['radius'])
            nbars_list.append(row['nbars'])
            flowrate_list.append(row['flowrate'])
            smx_pos_list.append(row['smx_pos'])
            cond_csv_limit_list.append(row['cond_csv_limit'])


bar_width = ps.plist("bar_width",bar_width_list)
bar_thickness = ps.plist("bar_thickness",bar_thickness_list)
bar_angle = ps.plist("bar_angle",bar_angle_list)
pipe_radius = ps.plist("pipe_radius",radius_list)
n_bars = ps.plist("n_bars",nbars_list)
flowrate = ps.plist("flowrate",flowrate_list)
d_per_level = ps.plist("d_per_level",["6"])
n_levels = ps.plist("n_levels",["2"])
d_radius = ps.plist("d_radius",["[0.0005,0.0003]"])
smx_pos = ps.plist("smx_pos",smx_pos_list)
cond_csv_limit = ps.plist("cond_csv_limit",cond_csv_limit_list)

## creates parameter grid (list of dictionarys)
params = ps.pgrid(base_path,run_path,convert_path,case_type,local_path,save_path,
                  cond_csv,conditional,user_ps,
                  zip(run_ID,run_name,bar_width,bar_thickness,bar_angle,pipe_radius,
                      n_bars,flowrate,smx_pos,cond_csv_limit),d_per_level,n_levels,d_radius)

######################################################################################################################################################################################
######################################################################################################################################################################################
log.info('-' * 100)
log.info('' * 100)


simulator = SimScheduling()

if __name__ == '__main__':
    df = ps.run_local(simulator.localrun, params, poolsize=4,save=True,tmpsave=True,skip_dups=True)   


