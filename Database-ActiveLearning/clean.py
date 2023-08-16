import os

try:
    os.system('rm -r __pycache__')
except:
    pass
try:
    os.system('rm output_geom/output*')
    os.system('rm output_surf/output*')
except:
    pass
os.system('rm params/*csv')
os.system('rm DOE/*pkl')
