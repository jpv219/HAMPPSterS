### Tailored for Imperial College's HPC
### General monitoring and restarting for BLUE jobs
### to be run locally
### Author: Paula D. Pico
### First commit: Aug, 2023
### Department of Chemical Engineering, Imperial College London

from CFD_run_scheduling import SimScheduling
from logger import log
import io
import contextlib
import operator

log.info('General job monitoring launch')
log.info('-' * 100)
log.info('-' * 100)

operator_map = {
    "<": operator.lt,
    ">": operator.gt,
    "<=": operator.le,
    ">=": operator.ge,
    "==": operator.eq,
    "!=": operator.ne
}

def main():
    simulator = SimScheduling()
    pset_dict = {}
    pset_dict['run_path'] = "/rds/general/user/pdp19/home/BLUE-13.2.0/project/Trials_monitor/pinchoff_test"
    pset_dict['convert_path'] = "/rds/general/user/pdp19/home/F_CONVERT"
    pset_dict['case_name'] = "pinchoff_test"
    pset_dict['run_ID'] = "1"
    pset_dict['local_path'] = "/home/pdp19/Documents/SMX_DeepLearning/Database-ActiveLearning"
    pset_dict['save_path'] = "/media/pdp19/PPICO/Pinchoff_ligament/pinchoff_test"
    pset_dict['init_jobID'] = "8150117"
    pset_dict['cond_csv'] = "Time"
    pset_dict['conditional'] = "<"
    pset_dict['cond_csv_limit'] = "100000000"
    pset_dict['user'] = "pdp19"

    if pset_dict['conditional'] in operator_map:
        comparison_func = operator_map[pset_dict['conditional']]
        simulator.localmonitor(pset_dict)

    else:
        raise ValueError("Invalid operator. Please provide a correct operator (<,>,<=,>=,==,!=)")

if __name__ == '__main__':
    main()