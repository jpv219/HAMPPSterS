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
# Local path
import sys
#sys.path.append('/home/fl18/Desktop/automatework/ML_auto/SMX_DeepLearning/HAMPPSterS_main')
sys.path.append('/home/jpv219/Documents/ML/SMX_DeepLearning/HAMPPSterS_main/')

import psweep as ps
from Mixing_run_scheduling import SVSimScheduling
from LHS_Dataspace import SV_Surf
from logger import configure_logger
import io
import contextlib
import csv
import pickle
import math

if __name__ == '__main__':

    log = configure_logger("svsurf")

    log.info('-' * 100)
    log.info('-' * 100)
    log.info('Parametric study launch')
    log.info('-' * 100)
    log.info('-' * 100)

    case = "svsurf"
    nruns = 20
    nruns_list = [str(i+38) for i in range(1, nruns + 1)]
    runname_list = ['run_svsurf_' + item for item in nruns_list]
    log.info(f'Case {case} studied with {nruns} runs')
    re_run = False
    user = 'fl18'

    run_path = ps.plist("run_path",["/rds/general/user/fl18/home/BLUE-12.5.1/project/ACTIVE_LEARNING/RUNS"])
    base_path = ps.plist("base_path",["/rds/general/user/fl18/home/BLUE-12.5.1/project/ACTIVE_LEARNING/BASE"])
    convert_path = ps.plist("convert_path",["/rds/general/user/fl18/home/F_ALLCONVERT"])

    case_type = ps.plist("case",[case])
    user_ps = ps.plist("user",[user])
    run_ID = ps.plist("run_ID",nruns_list)
    run_name = ps.plist("run_name",runname_list)

    local_path = ps.plist("local_path",["/home/fl18/Desktop/automatework/ML_auto/SMX_DeepLearning/HAMPPSterS_main"])
    save_path = ps.plist("save_path",["/media/fl18/Elements/surf_ML"])

    ### Termination condition to be written as: check_value --operator-- cond_csv_limit. Once condition is false, stop job
    ### cond_csv determines which condition to use as stopping criteria from the csv
    cond_csv = ps.plist("cond_csv",["Time"])
    conditional = ps.plist("conditional",["<"])
    cond_csv_limit = ps.plist("cond_csv_limit",["4.5"])
    ### convert vtk to vtr: last or all ###
    vtk_conv_mode = ps.plist("vtk_conv_mode", ["all"])

    ## Parameters to vary in the sample space
    Surf_dict = {'Bulk Diffusivity (m2/s)': [1e-8,1e-4],'Adsorption Coeff (m3/mol s)': [0.1,1e3],
                'Desorption Coeff (1/s)': [1e-3,10],'Maximum packing conc (mol/ m2)':[1e-6,1e-4],
                'Initial surface conc (mol/m2)': [1e-6,1e-4],'Surface diffusivity (m2/s)':[1e-8,1e-4],
                'Elasticity Coeff':[0.2,0.7] # [0.05,0.95]
                }

    captured_output = io.StringIO()

    LHS_sampler = SV_Surf(Surf_dict, nruns)

    with contextlib.redirect_stdout(captured_output):
        psdict = LHS_sampler()
        log.info('-' * 100)
        log.info('Modifications to the DOE')
        log.info(captured_output.getvalue())


    dict_print = psdict.iloc[:,7:]

    log.info('-' * 100)
    log.info('\n'+ dict_print.to_string())

    ### Save LHS dictionary for later

    with open('../DOE/LHS_SVSurf.pkl', 'wb') as file:
        pickle.dump(psdict, file)

    ## Surfactant parameters

    if not re_run:

        diff2_list = list(map(str,psdict["Bulk Diffusivity (m2/s)"]))
        ka_list = list(map(str,psdict["Adsorption Coeff (m3/mol s)"]))
        kd_list = list(map(str,psdict["Desorption Coeff (1/s)"]))
        ginf_list = list(map(str,psdict["Maximum packing conc (mol/ m2)"]))
        gini_list = list(map(str,psdict["Initial surface conc (mol/m2)"]))
        diffs_list = list(map(str,psdict["Surface diffusivity (m2/s)"]))
        beta_list = list(map(str,psdict["Elasticity Coeff"]))

        # Combine the lists
        data = list(zip(diff2_list, ka_list, kd_list, ginf_list, gini_list, diffs_list, beta_list))

        # Save the combined data into a CSV file
        with open('../params/parameters_svsurf.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["D_b", "ka", "kd", "ginf", "gini", "D_s", "beta"])
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
        with open('../params/parameters_svsurf.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                diff2_list.append(row["D_b"])
                ka_list.append(row["ka"])
                kd_list.append(row["kd"])
                ginf_list.append(row["ginf"])
                gini_list.append(row["gini"])
                diffs_list.append(row["D_s"])
                beta_list.append(row["beta"])
    

    diff1 = ps.plist("D_d",["1.0"])
    diff2 = ps.plist("D_b",diff2_list)
    ka = ps.plist("ka",ka_list)
    kd = ps.plist("kd",kd_list)
    ginf = ps.plist("ginf",ginf_list)
    gini = ps.plist("gini",gini_list)
    diffs = ps.plist("D_s",diffs_list)
    beta = ps.plist("beta",beta_list)

    #creates parameter grid (list of dictionarys)
    params = ps.pgrid(base_path,run_path,convert_path,case_type,local_path,
                    save_path,cond_csv,conditional,cond_csv_limit,vtk_conv_mode,
                    diff1,user_ps,
                    zip(run_ID,run_name,diff2,ka,kd,ginf,gini,diffs,beta))
        

    ######################################################################################################################################################################################
    ######################################################################################################################################################################################
    log.info('-' * 100)
    log.info('-' * 100)

    simulator = SVSimScheduling()

    df = ps.run_local(simulator.localrun, params, poolsize=5,save=True,tmpsave=True,skip_dups=True)    
