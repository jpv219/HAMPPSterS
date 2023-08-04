import paramiko
import configparser
import warnings
import os

save_path = '/Volumes/ML/Runs'
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

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
warnings.filterwarnings("ignore", category=ResourceWarning)

config = configparser.ConfigParser()
config.read('../configjp.ini')
#config.read('../confignk.ini')
user = config.get('SSH', 'username')
key = config.get('SSH', 'password')

try:
    ssh.connect('login-a.hpc.ic.ac.uk', username=user, password=key)
    transport = ssh.get_transport()
    sftp = paramiko.SFTPClient.from_transport(transport)

    remote_path = os.path.join(ephemeral_path,run_name,'RESULTS')

    remote_files = sftp.listdir_attr(remote_path)

    for file_attr in remote_files:
        remote_file_path = os.path.join(remote_path, file_attr.filename)
        local_file_path = os.path.join(save_path_runID, file_attr.filename)

        # Check if it's a regular file before copying
        if file_attr.st_mode & 0o100000:
            sftp.get(remote_file_path, local_file_path)
            print(f'Copied file {file_attr.filename}')
    

### closing HPC session
finally:
    if 'sftp' in locals():
        sftp.close()
    if 'ssh' in locals():
        ssh.close()