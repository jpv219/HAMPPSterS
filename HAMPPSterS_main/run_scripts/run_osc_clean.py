### SMX_Automation_simulation_run, tailored for BLUE 12.5.1
### Main parametric running script
### to be run locally
### Author: Paula Pico,
### First commit: July, 2023
### Version: 5.0
### Department of Chemical Engineering, Imperial College London
#######################################################################################################################################################################################
#######################################################################################################################################################################################
# Local path
import sys
sys.path.append('/home/pdp19/Documents/SMX_DeepLearning/HAMPPSterS_main')

import psweep as ps
from CFD_run_scheduling import IOSimScheduling
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

case = "osc_clean"
nruns = 3
nruns_list = [str(i) for i in range(1, nruns + 1)]
runname_list = ['run_osc_clean_' + item for item in nruns_list]
log.info(f'Case {case} studied with {nruns} runs')
user = 'pdp19'

run_path = ps.plist("run_path",["/rds/general/user/pdp19/home/BLUE-14.0.1/project/INT_OSC/RUNS"])
base_path = ps.plist("base_path",["/rds/general/user/pdp19/home/BLUE-14.0.1/project/INT_OSC/BASE"])
convert_path = ps.plist("convert_path",["/rds/general/user/pdp19/home/F_CONVERT"])

case_type = ps.plist("case",[case])
user_ps = ps.plist("user",[user])
run_ID = ps.plist("run_ID",nruns_list)
run_name = ps.plist("run_name",runname_list)

local_path = ps.plist("local_path",["/home/pdp19/Documents/SMX_DeepLearning/HAMPPSterS_main/"])
save_path = ps.plist("save_path",["/media/pdp19/PPICO3/ML_PROJECT/int_osc_clean"])

## Parameters to vary in the sample space
osc_dict = {'epsilon': [0.1,4],'Density_ratio': [1,5],'Viscosity_ratio': [5,1000/2],'Ga':[3,16],'La': [1e-6,1e-4]}

captured_output = io.StringIO()

with contextlib.redirect_stdout(captured_output):
    psdict = runDOE(osc_dict,nruns)
    log.info('-' * 100)
    log.info('Modifications to the DOE')
    log.info(captured_output.getvalue())

log.info('-' * 100)
log.info('\n'+ psdict.to_string())
log.info('-' * 100)

### Save LHS dictionary for later

with open('../DOE/LHS_osc_clean_1.pkl', 'wb') as file:
    pickle.dump(psdict, file)

### Termination condition to be written as: check_value --operator-- cond_csv_limit. Once condition is false, stop job
### cond_csv determines which condition to use as stopping criteria from the csv

psdict['cond_csv_limit'] = psdict['w'].apply(lambda w: w*10)

cond_csv = ps.plist("cond_csv",["Time"])
conditional = ps.plist("conditional",["<"])


epsilon_list = list(map(str,psdict['epsilon']))
rho_l_list = list(map(str,psdict['rho_l']))
mu_l_list = list(map(str,psdict['mu_l']))

# Dynamically changing termination condition
cond_csv_limit_list = list(map(str,psdict['cond_csv_limit']))

# Combine the lists
data = list(zip(epsilon_list,rho_l_list,mu_l_list,cond_csv_limit_list))

# Save the combined data into a CSV file
with open('../params/parameters_osc_clean_1.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['epsilon','rho_l','mu_l'])
    writer.writerows(data)


epsilon = ps.plist("epsilon",epsilon_list)
mu_l = ps.plist("mu_l",mu_l_list)
cond_csv_limit = ps.plist("cond_csv_limit",cond_csv_limit_list)

params = ps.pgrid(base_path,run_path,convert_path,case_type,local_path,save_path,
                  cond_csv,conditional,user_ps,zip(run_ID, run_name, epsilon, mu_l,cond_csv_limit))

######################################################################################################################################################################################
######################################################################################################################################################################################
log.info('-' * 100)
log.info('' * 100)


simulator = IOSimScheduling()

if __name__ == '__main__':
    df = ps.run_local(simulator.localrun, params, poolsize=5,save=True,tmpsave=True,skip_dups=True)
