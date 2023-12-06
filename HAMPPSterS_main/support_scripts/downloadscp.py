import paramiko
import configparser
import warnings
import os

save_path = '/media/jpv219/ML/Runs'
run_ID = 1
run_name = "run_"+str(run_ID)

###Create run local directory to store data
save_path_runID = os.path.join(save_path,run_name)
ephemeral_path = '/rds/general/user/jpv219/ephemeral/'
#ephemeral_path = '/rds/general/user/nkahouad/ephemeral/'
try:
    os.mkdir(save_path_runID)
except:
    pass

### Config faile with keys to login to the HPC
config = configparser.ConfigParser()
config.read('../configjp.ini')
#config.read('confignk.ini')
user = config.get('SSH', 'username')
key = config.get('SSH', 'password')
try_logins = ['login-d.hpc.ic.ac.uk','login-a.hpc.ic.ac.uk','login-b.hpc.ic.ac.uk','login-c.hpc.ic.ac.uk']

for login in try_logins:

    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    warnings.filterwarnings("ignore", category=ResourceWarning)

    try:
        ssh.connect(login, username=user, password=key)
        stdin, _, _ = ssh.exec_command("echo 'SSH connection test'")
        transport = ssh.get_transport()
        sftp = paramiko.SFTPClient.from_transport(transport)

        remote_path = os.path.join(ephemeral_path,run_name)
        remote_files = sftp.listdir_attr(remote_path)

        for file_attr in remote_files:
            remote_file_path = os.path.join(remote_path, file_attr.filename)
            local_file_path = os.path.join(save_path_runID, file_attr.filename)

            # Check if it's a regular file before copying
            if file_attr.st_mode & 0o100000:
                sftp.get(remote_file_path, local_file_path)

        
        print(f'Files successfully copied at {save_path_runID}')

        if stdin is not None:
            break
        
    except (paramiko.AuthenticationException, paramiko.SSHException) as e:
        if login == try_logins[-1]:
            raise e
        else:
            print(f'SSH connection failed with login {login}, trying again ...')
            continue
        

    ### closing HPC session
    finally:
        if 'sftp' in locals():
            sftp.close()
        if 'ssh' in locals():
            ssh.close()