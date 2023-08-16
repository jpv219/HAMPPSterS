### SMX_Automation_simulation_run, tailored for BLUE 12.5.1
### Main parametric running script
### to be run locally
### Author: Juan Pablo Valdes,
### First commit: July, 2023
### Department of Chemical Engineering, Imperial College London

import psweep as ps
from CFD_run_scheduling import SimScheduling
from LHS_Dataspace import runSurfDOE
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

case = "Surf"
nruns = 32
nruns_list = [str(i)+'S' for i in range(1, nruns + 1)]
log.info(f'Case {case} studied with {nruns} runs')
re_run = False

run_path = ps.plist("run_path",["/rds/general/user/nkahouad/home/BLUE-12.5.1/project/ACTIVE_LEARNING/RUNS"])
base_path = ps.plist("base_path",["/rds/general/user/nkahouad/home/BLUE-12.5.1/project/ACTIVE_LEARNING/BASE"])
convert_path = ps.plist("convert_path",["/rds/general/user/nkahouad/home/F_CONVERT"])

case_type = ps.plist("case",[case])
run_ID = ps.plist("run_ID",nruns_list)

local_path = ps.plist("local_path",["/home/jpv219/Documents/ML/SMX_DeepLearning/Database-ActiveLearning"])
save_path = ps.plist("save_path",["/media/jpv219/ML/Surf_Runs"])

## Parameters to vary in the sample space
Surf_dict = {'Bulk Diffusivity (m2/s)': [1e-4,1e-8],'Adsorption Coeff (m3/mol s)': [1,1e4],
             'Desorption Coeff (1/s)': [1e-3,10],'Maximum packing conc (mol/ m2)':[1e-6,1e-4],
             'Initial surface conc (mol/m2)': [1e-6,1e-4],'Surface diffusivity (m2/s)':[1e-4,1e-8],'Elasticity Coeff':[0.05,0.95]}

captured_output = io.StringIO()

with contextlib.redirect_stdout(captured_output):
    psdict = runSurfDOE(Surf_dict,nruns)
    log.info('-' * 100)
    log.info('Modifications to the DOE')
    log.info(captured_output.getvalue())

dict_print = psdict.iloc[:,5:13]

log.info('-' * 100)
log.info('\n'+ dict_print.to_string())

### Save LHS dictionary for later

with open('LHS_Surf.pkl', 'wb') as file:
    pickle.dump(psdict, file)

## Surfactant parameters

if not re_run:

    diff2_list = list(map(str,psdict['Bulk Diffusivity (m2/s)']))
    ka_list = list(map(str,psdict['Adsorption Coeff (m3/mol s)']))
    kd_list = list(map(str,psdict['Desorption Coeff (1/s)']))
    ginf_list = list(map(str,psdict['Maximum packing conc (mol/ m2)']))
    gini_list = list(map(str,psdict['Initial surface conc (mol/m2)']))
    diffs_list = list(map(str,psdict['Surface diffusivity (m2/s)']))
    beta_list = list(map(str,psdict['Elasticity Coeff']))

    # Combine the lists
    data = list(zip(diff2_list, ka_list, kd_list, ginf_list, gini_list, diffs_list, beta_list))

    # Save the combined data into a CSV file
    with open('parameters_surf.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['D_b', 'ka', 'kd', 'ginf', 'gini', 'D_s', 'beta'])
        writer.writerows(data)
else:
    diff2_list = []
    ka_list = []
    kd_list = []
    ginf_list = []
    gini_list = []
    diffs_list = []
    beta_list = []

    # Load data from CSV file
    with open('parameters_surf.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            diff2_list.append(row['D_b'])
            ka_list.append(row['ka'])
            kd_list.append(row['kd'])
            ginf_list.append(row['ginf'])
            gini_list.append(row['gini'])
            diffs_list.append(row['D_s'])
            beta_list.append(row['beta'])
 


diff1 = ps.plist('D_d',["1.0"])
diff2 = ps.plist('D_b',diff2_list)
ka = ps.plist('ka',ka_list)
kd = ps.plist('kd',kd_list)
ginf = ps.plist('ginf',ginf_list)
gini = ps.plist('gini',gini_list)
diffs = ps.plist('D_s',diffs_list)
beta = ps.plist('beta',beta_list)

#creates parameter grid (list of dictionarys)
params = ps.pgrid(base_path,run_path,convert_path,case_type,local_path,save_path,diff1,zip(run_ID,diff2,ka,kd,ginf,gini,diffs,beta))

######################################################################################################################################################################################
######################################################################################################################################################################################
log.info('-' * 100)
log.info('' * 100)


simulator = SimScheduling()

if __name__ == '__main__':
    df = ps.run_local(simulator.localrun, params, poolsize=4,save=True,skip_dups=False)   

