import os
import re
import math
import sys
import pandas as pd

run_path = '/rds/general/user/jpv219/home/BLUE-12.5.1/project/TRIALS/run_54/'
run_name = 'smxalt3'
ephemeral_path = os.path.join(os.environ['EPHEMERAL'],run_name)
pipe_radius = 0.016
out = 'SMX_ML2'
job = 'run_54'

os.chdir(ephemeral_path)

ptxEast_f = pd.read_csv(f'{run_name}.csv').iloc[:,63].iloc[-1]
domain_x = math.ceil(4*pipe_radius*1000)/1000
min_lim = 0.001*domain_x

if ptxEast_f > min_lim:
    os.chdir(run_path)
    line_with_pattern = None

    with open(f"{out}.out", 'r') as file:
        lines = file.readlines()
        pattern = 'writing restart file'
        for line in reversed(lines):
            if pattern in line:
                line_with_pattern = line.strip()
                break
    if line_with_pattern is not None:
        ### searching with re a sequence of 1 or more digits '\d+' in between two word boundaries '\b'
        match = re.search(r"\b\d+\b", line_with_pattern)
        if match is not None:
            restart_num = int(match.group())
        else:
            print('No restart number match found')
        ### Modifying .sh file accordingly
        with open(f"job_{job}.sh", 'r+') as file:
            lines = file.readlines()
            restart_line = lines[384]
            modified_restart = re.sub('FALSE', 'TRUE', restart_line)
            ### modifying the restart number by searching dynamically with f-strings. 
            modified_restart = re.sub(r'{}=\d+'.format('input_file_index'), '{}={}'.format('input_file_index', restart_num), modified_restart)
            lines[384] = modified_restart
            file.seek(0)
            file.writelines(lines)
            file.truncate()

    else:
        print("Pattern not found in the file.")
        
