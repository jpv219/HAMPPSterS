import os

try:
    os.system('rm -r __pycache__')
except:
    pass
try:
    os.system('rm output_geom/output*')
    os.system('rm output_surf/output*')
    os.system('rm output_sp_geom/output*')
    os.system('rm output_svgeom/output*')
    os.system('rm output_svsurf/output*')

except:
    pass
os.system('rm params/*csv')
os.system('rm DOE/*pkl')
os.system('rm surf_output.txt')
os.system('rm sp_geom_output.txt')
os.system('rm svsurf_output.txt')
os.system('rm svgeom_output.txt')
