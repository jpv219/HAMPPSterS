import configparser

config = configparser.ConfigParser()
config['SSH'] = {
    'username': 'user',
    'password': 'password'
}

with open('config.ini', 'w') as config_file:
    config.write(config_file)