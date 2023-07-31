import paramiko
import configparser
import warnings

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
warnings.filterwarnings("ignore", category=ResourceWarning)

try:
    config = configparser.ConfigParser()
    config.read('../configjp.ini')
    #config.read('confignk.ini')
    user = config.get('SSH', 'username')
    key = config.get('SSH', 'password')

    ssh.connect('login-a.hpc.ic.ac.uk', username=user, password=key)

    command = f'python /rds/general/user/jpv219/home/BLUE-12.5.1/project/ACTIVE_LEARNING/test.py test --arg_str hola'

    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8').strip()

    print(output)

finally:
    stdin.close()
    stdout.close()
    stderr.close()
    ssh.close()

