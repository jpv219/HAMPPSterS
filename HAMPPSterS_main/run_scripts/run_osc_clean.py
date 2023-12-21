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
from LHS_Dataspace import runIODOE
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
nruns = 2
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
save_path = ps.plist("save_path",["/media/pdp19/PPICO3/ML_PROJECT/int_osc_clean/RUNS/"])

## Parameters to vary in the sample space
osc_dict = {'epsilon': [1,1.01],'Wave_number (1/m)': [1,1.01],'Surf_tension (N/m)': [1,1.01],'Density_l (kg/m3)': [1,1.01],
            'Density_g (kg/m3)': [1e-2,1.01e-2],'Viscosity_l (Pa*s)':[1e-2,1.01e-2], 'Viscosity_g (Pa*s)':[1e-4,1.1e-4],'Gravity (m/s2)': [10,10.01]}

captured_output = io.StringIO()

with contextlib.redirect_stdout(captured_output):
    psdict = runIODOE(osc_dict,nruns)
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

# psdict['cond_csv_limit'] = psdict['t_final (s)'].apply(lambda w: w)
psdict['cond_csv_limit'] = 0.05

cond_csv = ps.plist("cond_csv",["Time"])
conditional = ps.plist("conditional",["<"])

epsilon_list = list(map(str,psdict['epsilon']))
k_list = list(map(str,psdict['Wave_number (1/m)']))
sigma_s_list = list(map(str,psdict['Surf_tension (N/m)']))
rho_l_list = list(map(str,psdict['Density_l (kg/m3)']))
rho_g_list = list(map(str,psdict['Density_g (kg/m3)']))
mu_l_list = list(map(str,psdict['Viscosity_l (Pa*s)']))
mu_g_list = list(map(str,psdict['Viscosity_g (Pa*s)']))
gravity_list = list(map(str,psdict['Gravity (m/s2)']))
a0_list = list(map(str,psdict['a0']))
rho_r_list = list(map(str,psdict['Density_ratio']))
mu_r_list = list(map(str,psdict['Viscosity_ratio']))
La_g_list = list(map(str,psdict['La_g']))
La_l_list = list(map(str,psdict['La_l']))
Ga_g_list = list(map(str,psdict['Ga_g']))
Ga_l_list = list(map(str,psdict['Ga_l']))
Bo_l_list = list(map(str,psdict['Bo_l']))
omega_list = list(map(str,psdict['omega']))
T_list = list(map(str,psdict['T (s)']))
t_final_list = list(map(str,psdict['t_final (s)']))
delta_t_sn_list = list(map(str,psdict['delta_t_sn (s)']))


# Dynamically changing termination condition
cond_csv_limit_list = list(map(str,psdict['cond_csv_limit']))

# Combine the lists
data = list(zip(epsilon_list,k_list,sigma_s_list,rho_l_list,rho_g_list,mu_l_list,mu_g_list,gravity_list,cond_csv_limit_list,
                a0_list,rho_r_list,mu_r_list,La_g_list,La_l_list,Ga_g_list,Ga_l_list,Bo_l_list,omega_list,T_list,t_final_list,delta_t_sn_list))

# Save the combined data into a CSV file
with open('../params/parameters_osc_clean_1.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['epsilon','k','sigma_s','rho_l','rho_g','mu_l','mu_g','gravity','cond_csv_limit',
                     'a0','rho_r','mu_r','La_g','La_l','Ga_g','Ga_l','Bo_l','omega','T','t_final','delta_t_sn'])
    writer.writerows(data)


epsilon = ps.plist("epsilon",epsilon_list)
k = ps.plist("k",k_list)
t_final = ps.plist("t_final",t_final_list)
sigma_s = ps.plist("sigma_s",sigma_s_list)
rho_l = ps.plist("rho_l",rho_l_list)
rho_g = ps.plist("rho_g",rho_g_list)
mu_l = ps.plist("mu_l",mu_l_list)
mu_g = ps.plist("mu_g",mu_g_list)
gravity = ps.plist("gravity",gravity_list)
delta_t_sn = ps.plist("delta_t_sn",delta_t_sn_list)
cond_csv_limit = ps.plist("cond_csv_limit",cond_csv_limit_list)

params = ps.pgrid(base_path,run_path,convert_path,case_type,local_path,save_path,
                  cond_csv,conditional,user_ps,zip(run_ID, run_name, epsilon, k, t_final, sigma_s,
                                                    rho_l, rho_g, mu_l, mu_g, gravity, delta_t_sn, cond_csv_limit))

######################################################################################################################################################################################
######################################################################################################################################################################################
log.info('-' * 100)
log.info('' * 100)


simulator = IOSimScheduling()

if __name__ == '__main__':
    df = ps.run_local(simulator.localrun, params, poolsize=2,save=True,tmpsave=True,skip_dups=True)
