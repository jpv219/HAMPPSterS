import paramiko

ssh = paramiko.SSHClient()

ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

with open('../keys.txt', 'r') as file:
    lines = file.readlines()
    user = lines[2].strip()
    key = lines[3].strip()

try:
    ssh.connect('login.hpc.ic.ac.uk', username=user, password=key)

    stdin, stdout, stderr = ssh.exec_command('ls -l')

    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')

    print("Command Output:")
    print(output)
finally:
    ssh.close()