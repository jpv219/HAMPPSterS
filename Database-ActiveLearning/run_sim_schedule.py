### SMX_Automation_simulation_run, tailored for BLUE 12.5.1
### Main parametric running script
### to be run locally
### Author: Juan Pablo Valdes,
### First commit: July, 2023
### Department of Chemical Engineering, Imperial College London

import psweep as ps
from CFD_run_scheduling import SimScheduling
from LHS_Dataspace import runDOE
from logger import log
import io
import contextlib
import csv
import pickle

log.info('-' * 100)
log.info('-' * 100)
log.info('Parametric study launch')
log.info('-' * 100)
log.info('-' * 100)

case = "Geom"
nruns = 32
nruns_list = [str(i) for i in range(1, nruns + 1)]
log.info(f'Case {case} studied with {nruns} runs')
re_run = False

run_path = ps.plist("run_path",["/rds/general/user/jpv219/home/BLUE-12.5.1/project/ACTIVE_LEARNING/RUNS"])
base_path = ps.plist("base_path",["/rds/general/user/jpv219/home/BLUE-12.5.1/project/ACTIVE_LEARNING/BASE"])
convert_path = ps.plist("convert_path",["/rds/general/user/jpv219/home/F_CONVERT"])

case_type = ps.plist("case",[case])
run_ID = ps.plist("run_ID",nruns_list)

local_path = ps.plist("local_path",["/home/jpv219/Documents/ML/SMX_DeepLearning/Database-ActiveLearning"])
save_path = ps.plist("save_path",["/media/jpv219/ML/Runs"])

## Parameters to vary in the sample space
max_diameter = 0.02
SMX_dict = {'Bar_Width (mm)': [1,20],'Bar_Thickness (mm)': [1,5],'Radius (mm)': [5,max_diameter*1000/2],'Nbars':[3,16],'Flowrate (m3/s)': [1e-6,1e-4],'Angle':[20,80]}

captured_output = io.StringIO()

with contextlib.redirect_stdout(captured_output):
    psdict = runDOE(SMX_dict,nruns)
    log.info('-' * 100)
    log.info('Modifications to the DOE')
    log.info(captured_output.getvalue())

log.info('-' * 100)
log.info('\n'+ psdict.to_string())

## Geometry parameters

if not re_run:

if not re_run:

    bar_width_list = list(map(str,psdict['Bar_Width (mm)'] / 1000))
    bar_thickness_list = list(map(str,psdict['Bar_Thickness (mm)'] / 1000))
    bar_angle_list = list(map(str,psdict['Angle']))
    radius_list = list(map(str,psdict['Radius (mm)'] / 1000))
    nbars_list = list(map(str,psdict['Nbars']))
    flowrate_list = list(map(str,psdict['Flowrate (m3/s)']))
    smx_pos_list = list(map(str,psdict['SMX_pos (mm)'] / 1000))


    # Combine the lists
    data = list(zip(bar_width_list, bar_thickness_list, bar_angle_list, radius_list, nbars_list, flowrate_list, smx_pos_list))

    # Save the combined data into a CSV file
    with open('parameters.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['bar_width', 'bar_thickness', 'bar_angle', 'radius', 'nbars', 'flowrate', 'smx_pos'])
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

    # Load data from CSV file
    with open('parameters.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            bar_width_list.append(row['bar_width'])
            bar_thickness_list.append(row['bar_thickness'])
            bar_angle_list.append(row['bar_angle'])
            radius_list.append(row['radius'])
            nbars_list.append(row['nbars'])
            flowrate_list.append(row['flowrate'])
            smx_pos_list.append(row['smx_pos'])


bar_width = ps.plist("bar_width",bar_width_list)
bar_thickness = ps.plist("bar_thickness",bar_thickness_list)
bar_angle = ps.plist("bar_angle",bar_angle_list)
pipe_radius = ps.plist("pipe_radius",radius_list)
max_diameter = ps.plist("max_diameter",[max_diameter])
n_bars = ps.plist("n_bars",nbars_list)
flowrate = ps.plist("flowrate",flowrate_list)
d_per_level = ps.plist("d_per_level",["6"])
n_levels = ps.plist("n_levels",["2"])
d_radius = ps.plist("d_radius",["[0.0005,0.0003]"])
smx_pos = ps.plist("smx_pos",smx_pos_list)


## creates parameter grid (list of dictionarys)
params = ps.pgrid(base_path,run_path,convert_path,case_type,local_path,save_path,zip(run_ID,bar_width,bar_thickness,bar_angle,pipe_radius,n_bars,flowrate,smx_pos),max_diameter,d_per_level,n_levels,d_radius)


if not re_run:
    ### Saving params in a csv in case re-runs are needed
    log.info('Saving parametric run in csv')
    log.info('-' * 100)
    with open('params.csv', "w", newline="") as csv_file:
        fieldnames = params[0].keys()
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(params)

loaded_params = []
with open('params.csv', newline="") as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        loaded_params.append(row)


######################################################################################################################################################################################
######################################################################################################################################################################################
log.info('-' * 100)
log.info('' * 100)


simulator = SimScheduling()

if __name__ == '__main__':
    df = ps.run_local(simulator.localrun, params, poolsize=4,save=True,skip_dups=False)   


