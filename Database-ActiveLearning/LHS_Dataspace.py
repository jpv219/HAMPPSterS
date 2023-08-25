### SMX_Automation_simulation_run, tailored for BLUE 12.5.1
### LHS DOE Sample experiments generator
### to be run locally in psweep script
### Author: Juan Pablo Valdes,
### Version: 1.0
### First commit: July, 2023
### Department of Chemical Engineering, Imperial College London

from doepy import build
import math
import numpy as np

                      ############################# GEOMETRY FEATURES - LHS #########################

## Function applying restrictions

def apply_restrictions(DOE):
    #Loading features
    for i in range(DOE.shape[0]):
        W = DOE.loc[i,'Bar_Width (mm)']
        R = DOE.loc[i,'Radius (mm)']
        N = round(DOE.loc[i,'Nbars'])
        Q = DOE.loc[i,'Flowrate (m3/s)']
        #W- N -D considerations
        OldW = W
        OldQ = Q

        Max_W = 2*R/N
            
        W = min(W,Max_W)

        if W != OldW:
            print('W in row ' + str(i) + ' modified from ' + str(OldW) + ' to ' + str(W))

        Re = 1364*(4*Q/((math.pi*((2*R)/1000))**2))*((2*R)/1000)/0.615

        if Re >50:
            Q = ((0.615*50/1364)/(4*((2*R)/1000)))*((math.pi*((2*R)/1000))**2)
            print('Q in row ' + str(i) + ' modified from ' + str(OldQ) + ' to ' + str(Q))

        DOE.loc[i,'Bar_Width (mm)'] = W
        DOE.loc[i,'Flowrate (m3/s)']  = Q
        DOE.loc[i,'Nbars'] = N

    return DOE

def calcRe(row):
    return 1364*(4*row['Flowrate (m3/s)']/((math.pi*2*(row['Radius (mm)']/1000))**2))*(2*row['Radius (mm)']/1000)/0.615

def calcPos(row):
    return row['Radius (mm)']

def runDOE(SMX_dict,numsamples):

    ## Initial LHS with no restrictions
    LHS_DOE = build.space_filling_lhs(SMX_dict,num_samples = numsamples) 

    modifiedLHS = apply_restrictions(LHS_DOE)

    modifiedLHS['Re'] = modifiedLHS.apply(lambda row: calcRe(row), axis = 1)
    modifiedLHS['SMX_pos (mm)'] = modifiedLHS.apply(lambda row: calcPos(row), axis = 1)
    
    return modifiedLHS


                 ############################# SURFACTANT PROPERTIES - LHS #########################

def surf_restriction(DOE):
    for i in range(DOE.shape[0]):
        ginf = DOE.loc[i,'Maximum packing conc (mol/ m2)']
        gini = DOE.loc[i,'Initial surface conc (mol/m2)']

        old_gini = gini

        if gini>=ginf:
            random_float = np.random.uniform(low=0.05, high=0.95)  
            random_float = round(random_float, 2) 
            gini = random_float*ginf
            print('G_ini (mol/m2) in row ' + str(i) + ' modified from ' + str(old_gini) + ' to ' + str(gini))
        DOE.loc[i,'Initial surface conc (mol/m2)'] = gini

    return DOE

def gamma_ratio(row):
    return (row['Initial surface conc (mol/m2)']/row['Maximum packing conc (mol/ m2)'])
def PeS(row):
    return (0.159*0.008/row['Surface diffusivity (m2/s)'])
def PeB(row):
    return (0.159*0.008/row['Bulk Diffusivity (m2/s)'])
def Bi(row):
    return (row['Desorption Coeff (1/s)']*0.008/0.159)
def Cinf(row):
    return ((row['Desorption Coeff (1/s)']*row['Initial surface conc (mol/m2)'])/
            (row['Adsorption Coeff (m3/mol s)']*(row['Maximum packing conc (mol/ m2)']-row['Initial surface conc (mol/m2)'])))
def Da(row):
    return (row['Maximum packing conc (mol/ m2)']/(row['Cinf']*0.008))
def K(row):
    return (row['Adsorption Coeff (m3/mol s)']*row['Cinf']/row['Desorption Coeff (1/s)'])

def runSurfDOE(Surf_dict,samples):

    SurfDOE = build.space_filling_lhs(Surf_dict, num_samples=samples)
    #### Adding dimensionless parameter calculation for easier post processing
    Modified_SurfDOE = surf_restriction(SurfDOE)
    Modified_SurfDOE['G0/Ginf'] = Modified_SurfDOE.apply(lambda row: gamma_ratio(row), axis = 1)
    Modified_SurfDOE['PeS'] = Modified_SurfDOE.apply(lambda row: PeS(row), axis = 1)
    Modified_SurfDOE['PeB'] = Modified_SurfDOE.apply(lambda row: PeB(row), axis = 1)
    Modified_SurfDOE['Bi'] = Modified_SurfDOE.apply(lambda row: Bi(row), axis = 1)
    Modified_SurfDOE['Cinf'] = Modified_SurfDOE.apply(lambda row: Cinf(row), axis = 1)
    Modified_SurfDOE['Da'] = Modified_SurfDOE.apply(lambda row: Da(row), axis = 1)
    Modified_SurfDOE['K'] = Modified_SurfDOE.apply(lambda row: K(row), axis = 1)


    return Modified_SurfDOE

