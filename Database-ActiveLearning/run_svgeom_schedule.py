### Stirred_Vessel_Automation_simulation_run, tailored for BLUE 12.5.1
### Main parametric running script
### to be run locally
### Author: Fuyue Liang,
### Adapted from SMX_automation by Juan Pablo Valdes
### First commit: Sep, 2023
### Version: 1.0
### Department of Chemical Engineering, Imperial College London
#######################################################################################################################################################################################
#######################################################################################################################################################################################

import psweep as ps
from CFD_run_scheduling import SimScheduling
from LHS_Dataspace import runSVDOE
from logger import configure_logger
import io
import contextlib
import csv
import pickle
import math

log = configure_logger("svgeom")

log.info('-' * 100)
log.info('-' * 100)
log.info('Parametric study launch')
log.info('-' * 100)
log.info('-' * 100)

case = "svgeom"
nruns = 32
nruns_list = [str(i) for i in range(1, nruns + 1)]
runname_list = ['run_svgeom_' + item for item in nruns_list]
log.info(f'Case {case} studied with {nruns} runs')
re_run = False
user = 'fl18'

run_path = ps.plist("run_path",["/rds/general/user/fl18/home/BLUE-12.5.1/project/ACTIVE_LEARNING/RUNS"])
base_path = ps.plist("base_path",["/rds/general/user/fl18/home/BLUE-12.5.1/project/ACTIVE_LEARNING/BASE"])
convert_path = ps.plist("convert_path",["/rds/general/user/fl18/home/F_CONVERT"])

case_type = ps.plist("case",[case])
user_ps = ps.plist("user",[user])
run_ID = ps.plist("run_ID",nruns_list)
run_name = ps.plist("run_name",runname_list)

local_path = ps.plist("local_path",["/home/fl18/Desktop/automatework/ML_auto/SMX_DeepLearning/Database-ActiveLearning"])
save_path = ps.plist("save_path",["/media/fl18/Elements/emu_ML"])

### Termination condition to be written as: check_value --operator-- cond_csv_limit. Once condition is false, stop job
### cond_csv determines which condition to use as stopping criteria from the csv
cond_csv = ps.plist("cond_csv",["Time"])
conditional = ps.plist("conditional",["<"])
cond_csv_limit = ps.plist("cond_csv_limit",["4.5"])


## Parameters to vary in the sample space
tank_diameter = 0.05 # (m)
SV_dict = {'Impeller_Diameter (m)': [0.15*tank_diameter,0.85*tank_diameter],
            'Frequency (1/s)': [5,8],
            'Clearance (m)': [0.15*tank_diameter,0.85*tank_diameter],
            'Blade_width (m)':[0.001, 0.036], # [0.1D, 0.9D], D=[0.2T, 0.8T]
            'Balde_thickness (m)': [0.001,0.005],
            'Nblades':[1,6],
            'Inclination': [0,180]
            }

captured_output = io.StringIO()

with contextlib.redirect_stdout(captured_output):
    psdict = runSVDOE(SV_dict,nruns)
    log.info('-' * 100)
    log.info('Modifications to the DOE')
    log.info(captured_output.getvalue())

log.info('-' * 100)
log.info('\n'+ psdict.to_string())
log.info('-' * 100)

### Save LHS dictionary for later

with open('DOE/LHS_SVGeom.pkl', 'wb') as file:
    pickle.dump(psdict, file)

## Geometry parameters

if not re_run:

    impeller_d_list = list(map(str,psdict['Impeller_Diameter (m)']))
    frequency_list = list(map(str,psdict['Frequency (1/s)']))
    clearance_list = list(map(str,psdict['Clearance (m)']))
    blade_width_list = list(map(str,psdict['Blade_width (m)']))
    blade_thick_list = list(map(str,psdict['Blade_thickness (m)']))
    nblades_list = list(map(str,psdict['Nblades']))
    inclination_list = list(map(str,psdict['Inclination']))

    # Combine the lists
    data = list(zip(impeller_d_list, frequency_list, clearance_list, 
                    blade_width_list, blade_thick_list, nblades_list, inclination_list))

    # Save the combined data into a CSV file
    with open('params/parameters_svgeom.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['impeller_d', 'frequency', 'clearance', 'blade_width', 'blade_thick', 
                         'nblades', 'inclination'])
        writer.writerows(data)

else:
    # Initialize empty lists for each parameter
    impeller_d_list = []
    frequency_list = []
    clearance_list = []
    blade_width_list = []
    blade_thick_list = []
    nblades_list = []
    inclination_list = []

    # Load data from CSV file
    with open('params/parameters_svgeom.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            impeller_d_list.append(row['impeller_d'])
            frequency_list.append(row['frequency'])
            clearance_list.append(row['clearance'])
            blade_width_list.append(row['blade_width'])
            blade_thick_list.append(row['blade_thick'])
            nblades_list.append(row['nblades'])
            inclination_list.append(row['inclination'])


impeller_d = ps.plist("impeller_d",impeller_d_list)
frequency = ps.plist("frequency",frequency_list)
clearance = ps.plist("clearance",clearance_list)
blade_width = ps.plist("blade_width",blade_width_list)
blade_thick = ps.plist("blade_thick",blade_thick_list)
nblades = ps.plist("nblades",nblades_list)
inclination = ps.plist("inclination",inclination_list)

## creates parameter grid (list of dictionarys)
params = ps.pgrid(base_path,run_path,convert_path,case_type,local_path,save_path,
                  cond_csv,conditional,user_ps,
                  zip(run_ID,run_name,impeller_d,frequency,clearance,blade_width,
                      blade_thick,nblades,inclination))

######################################################################################################################################################################################
######################################################################################################################################################################################
log.info('-' * 100)
log.info('' * 100)


simulator = SimScheduling()

if __name__ == '__main__':
    df = ps.run_local(simulator.localrun, params, poolsize=4,save=True,tmpsave=True,skip_dups=True)   


