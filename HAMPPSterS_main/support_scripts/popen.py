from subprocess import Popen, PIPE
import subprocess
import datetime
import sys

job_id = sys.argv[1]

def popen(job_id):

    try:
        p = Popen(['qstat', '-a',f"{job_id}"],stdout=PIPE, stderr=PIPE)
        output, error = p.communicate()

        if p.returncode != 0:
            raise subprocess.CalledProcessError(p.returncode, p.args)
        
        ## formatted to Imperial HPC 
        jobstatus = str(output,'utf-8').split()[-3:]

        if not jobstatus:
            raise ValueError('Existing job but doesnt belong to this account')
        
        if jobstatus[1] == 'Q' or jobstatus[1] == 'H':
            print('Queing')
        elif jobstatus[1] == 'R':
            time_format = '%H:%M'
            wall_time = datetime.datetime.strptime(jobstatus[0], time_format).time()
            elap_time = datetime.datetime.strptime(jobstatus[2], time_format).time()
            delta = datetime.datetime.combine(datetime.date.min, wall_time)-datetime.datetime.combine(datetime.date.min, elap_time)
            remaining = delta.total_seconds()+120
            print(remaining)

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        raise RuntimeError("Job cannot be located through qstat")
    
    except ValueError as e:
        print(f"Error: {e}")
        raise ValueError('Existing job but doesnt belong to this account')
    
try:
    popen(job_id)
except RuntimeError as e:
    print(f"Error: {e}")
except ValueError as e:
    print(f"Error: {e}")

