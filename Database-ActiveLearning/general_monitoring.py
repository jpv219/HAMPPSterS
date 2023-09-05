### Tailored for Imperial College's HPC
### General monitoring and restarting for BLUE jobs. Copying csv files before every simulation restart
### to be run locally
### Author: Paula Pico
### First commit: Aug, 2023
### Department of Chemical Engineering, Imperial College London

from CFD_run_scheduling import SimMonitoring
from logger import configure_logger
import io
import contextlib
import operator
import json
import os

log = configure_logger("gen")

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
    pset_dict = {}
    with open('/home/pdp19/Documents/SMX_DeepLearning/Database-ActiveLearning/pinchoff_test/setup_pinchoff_test.txt') as f:
        data = f.read()
    pset_dict = json.loads(data)
    simulator = SimMonitoring(pset_dict)

    if pset_dict['conditional'] in operator_map:
        comparison_func = operator_map[pset_dict['conditional']]
        simulator.localmonitor(pset_dict)

    else:
        raise ValueError("Invalid operator. Please provide a correct operator (<,>,<=,>=,==,!=)")

if __name__ == '__main__':
    main()