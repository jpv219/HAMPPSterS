import paramiko
import configparser
import warnings


 ### Read SSH configuration from config file
config = configparser.ConfigParser()
config.read('../configjp.ini')
#config.read('confignk.ini')
user = config.get('SSH', 'username')
key = config.get('SSH', 'password')
try_logins = ['login.hpc.ic.ac.uk','login-a.hpc.ic.ac.uk','login-b.hpc.ic.ac.uk','login-c.hpc.ic.ac.uk']

for login in try_logins:

    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    warnings.filterwarnings("ignore", category=ResourceWarning)

    try:

        ssh.connect(login, username=user, password=key)

        command = "echo 'SSH connection test'"

        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8').strip()

        print(output)
        print(stdin)
        print(login)

        if stdin is not None:
            break

    except (paramiko.AuthenticationException, paramiko.SSHException) as e:
        if login == try_logins[-1]:
            raise e
        else:
            print(f'SSH connection failed with login {login}, trying again ...')
            continue

    finally:
        if 'stdin' in locals():
            stdin.close()
        if 'stdout' in locals():
            stdout.close()
        if 'stderr' in locals():
            stderr.close()
        ssh.close()

