import paramiko
import configparser
import warnings

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
warnings.filterwarnings("ignore", category=ResourceWarning)

config = configparser.ConfigParser()
config.read('configjp.ini')
#config.read('confignk.ini')
user = config.get('SSH', 'username')
key = config.get('SSH', 'password')

try:
    ssh.connect('login.hpc.ic.ac.uk', username=user, password=key)

    # List of script paths to execute in sequence
    script_paths = [
        '/rds/general/user/jpv219/home/BLUE-12.5.1/project/TRIALS/f90_mod.py',
        '/rds/general/user/jpv219/home/BLUE-12.5.1/project/TRIALS/jobsh_mod.py',
        '/rds/general/user/jpv219/home/BLUE-12.5.1/project/TRIALS/restart.py',
        # Add more script paths as needed
    ]

    for script_path in script_paths:
        command = f'python {script_path}'
        stdin, stdout, stderr = ssh.exec_command(command)
        stdin.close()

        # Read and print the output of the script execution on the remote server
        print("Output:")
        for line in stdout.readlines():
            print(line.strip())

        # Read and print any error messages (if any) from the script execution
        print("\nError messages:")
        for line in stderr.readlines():
            print(line.strip())
    
finally:
    ssh.close()