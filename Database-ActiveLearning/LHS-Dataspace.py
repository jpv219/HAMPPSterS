from doepy import build
import math
import sys

## Function applying restrictions

arg1 = sys.argv[1]

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

## Parameters to vary in the sample space
SMX_dict = {'Bar_Width (mm)': [1,20],'Bar_Thickness (mm)': [1,5],'Radius (mm)': [5,30],'Nbars':[3,16],'Flowrate (m3/s)': [1e-6,1e-3],'Angle':[20,80]}

## Initial LHS with no restrictions

LHS_DOE = build.space_filling_lhs(SMX_dict,num_samples = int(arg1))

print(LHS_DOE)

modifiedLHS = apply_restrictions(LHS_DOE)

def calcRe(row):
    return 1364*(4*row['Flowrate (m3/s)']/((math.pi*2*(row['Radius (mm)']/1000))**2))*(2*row['Radius (mm)']/1000)/0.615

modifiedLHS['Re'] = modifiedLHS.apply(lambda row: calcRe(row), axis = 1 )

print(modifiedLHS)
