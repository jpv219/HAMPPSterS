### SMX_Automation_simulation_run, tailored for BLUE 12.5.1
### LHS DOE Sample experiments generator
### to be run locally in psweep script
### Author: Juan Pablo Valdes,
### First commit: July, 2023
### Department of Chemical Engineering, Imperial College London

from doepy import build
import math

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

def runSurfDOE(Surf_dict,samples):

    SurfDOE = build.space_filling_lhs(Surf_dict, num_samples=samples)

    return SurfDOE

