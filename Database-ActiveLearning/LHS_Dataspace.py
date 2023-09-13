### SMX_Automation_simulation_run, tailored for BLUE 12.5.1
### LHS DOE Sample experiments generator
### to be run locally in psweep script
### Author: Juan Pablo Valdes,
### First commit: July, 2023
### Version: 3.0
### Department of Chemical Engineering, Imperial College London
#######################################################################################################################################################################################
#######################################################################################################################################################################################

from doepy import build
import math
import numpy as np

####################################################################################### GEOMETRY FEATURES - LHS ###################################################################################

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

        ## Maintaining consistent width with the number of bars and the pipe diameter
        if W != OldW:
            print('W in row ' + str(i) + ' modified from ' + str(OldW) + ' to ' + str(W))

        Re = 1364*(Q/(math.pi*(R/1000)**2))*((2*R)/1000)/0.615
        We = 1364*((Q/(math.pi*(R/1000)**2))**2)*((2*R)/1000)/0.036

        ### Keeping laminar conditions
        if Re > 50:
            Q = (50*0.615/1364)*((math.pi*(R/1000)**2)/((2*R)/1000))
            print('Re modification')
            print('Q in row ' + str(i) + ' modified from ' + str(OldQ) + ' to ' + str(Q))

        ## Avoiding high Weber that slows down BLUE
        if We > 10:
            Q = math.sqrt(((10*0.036/1364)*(1/((2*R)/1000))))*(math.pi*(R/1000)**2)
            print('We modification')
            print('Q in row ' + str(i) + ' modified from ' + str(OldQ) + ' to ' + str(Q))

        DOE.loc[i,'Bar_Width (mm)'] = W
        DOE.loc[i,'Flowrate (m3/s)']  = Q
        DOE.loc[i,'Nbars'] = N

    return DOE

def apply_rest_sp(DOE):
    #Loading features
    for i in range(DOE.shape[0]):
        W = DOE.loc[i,'Bar_Width (mm)']
        R = DOE.loc[i,'Radius (mm)']
        N = round(DOE.loc[i,'Nbars'])
        Q = DOE.loc[i,'Flowrate (m3/s)']
        N_ele = round(DOE.loc[i,'NElements'])
        #W- N -D considerations
        OldW = W
        OldQ = Q

        Max_W = 2*R/N
            
        W = min(W,Max_W)

        ## Maintaining consistent width with the number of bars and the pipe diameter
        if W != OldW:
            print('W in row ' + str(i) + ' modified from ' + str(OldW) + ' to ' + str(W))

        Re = 1364*(Q/(math.pi*(R/1000)**2))*((2*R)/1000)/0.615

        ### Keeping laminar conditions
        if Re > 500:
            Q = (np.random.uniform(5,500)*0.615/1364)*((math.pi*(R/1000)**2)/((2*R)/1000))
            print('Re modification')
            print('Q in row ' + str(i) + ' modified from ' + str(OldQ) + ' to ' + str(Q))

        DOE.loc[i,'Bar_Width (mm)'] = W
        DOE.loc[i,'Flowrate (m3/s)']  = Q
        DOE.loc[i,'Nbars'] = N
        DOE.loc[i,'NElements'] = N_ele

    return DOE

def calcRe(row):
    return 1364*(row['Flowrate (m3/s)']/(math.pi*(row['Radius (mm)']/1000)**2))*(2*row['Radius (mm)']/1000)/0.615

def calcPos(row):
    return row['Radius (mm)']

def calcWe(row):
    return 1364*((row['Flowrate (m3/s)']/(math.pi*(row['Radius (mm)']/1000)**2))**2)*(2*row['Radius (mm)']/1000)/0.036

def runDOE(SMX_dict,numsamples):

    ## Initial LHS with no restrictions
    LHS_DOE = build.space_filling_lhs(SMX_dict,num_samples = numsamples) 

    modifiedLHS = apply_restrictions(LHS_DOE)

    modifiedLHS['Re'] = modifiedLHS.apply(lambda row: calcRe(row), axis = 1)
    modifiedLHS['SMX_pos (mm)'] = modifiedLHS.apply(lambda row: calcPos(row), axis = 1)
    modifiedLHS['We'] = modifiedLHS.apply(lambda row: calcWe(row), axis = 1)
    
    return modifiedLHS

def runDOESP(SMX_dict,numsamples):

    ## Initial LHS with no restrictions
    LHS_DOE = build.space_filling_lhs(SMX_dict,num_samples = numsamples) 

    modifiedLHS = apply_rest_sp(LHS_DOE)

    modifiedLHS['Re'] = modifiedLHS.apply(lambda row: calcRe(row), axis = 1)
    modifiedLHS['SMX_pos (mm)'] = modifiedLHS.apply(lambda row: calcPos(row), axis = 1)
    
    return modifiedLHS


####################################################################################### SURFACTANT PROPERTIES - LHS ###################################################################################

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


####################################################################################
# # STIRRED VESSEL GEOMETRY FEATURES - LHS #
# ##################################################################################

## Function applying restrictions

def svgeom_restrictions(DOE):
    for i in range(DOE.shape[0]):
        # make sure blade number is an integer
        N = round(DOE.loc[i,'Nblades'])
        DOE.loc[i,'Nblades'] = N

        # make sure Re > 500
        F = round(DOE.loc[i, 'Frequency (1/s)'],2)
        D = DOE.loc[i,'Impeller_Diameter (m)']
        oldF = F

        Re = (998*F*D**2)/1e-3

        if Re < 500:
            F = round((500*1e-3)/(998*D**2),2)
            print('Re modification')
            print(f'Frequency (1/s) in row {i} is modified from {oldF} to {F}.')
        DOE.loc[i,'Frequency (1/s)'] = F

    return DOE


def calcsvRe(row):
    return (998*row['Frequency (1/s)']*row['Impeller_Diameter (m)']**2)/1e-3

def calcsvWe(row):
    return (998* row['Frequency (1/s)']**2 * row['Impeller_Diameter (m)']**3)/0.035

def runSVDOE(SV_dict,numsamples):

    ## Initial LHS with no restrictions
    LHS_DOE = build.space_filling_lhs(SV_dict,num_samples = numsamples) 

    modifiedLHS = svgeom_restrictions(LHS_DOE)

    modifiedLHS['Re'] = modifiedLHS.apply(lambda row: calcsvRe(row), axis = 1)
    modifiedLHS['We'] = modifiedLHS.apply(lambda row: calcsvWe(row), axis = 1)
    
    return modifiedLHS


####################################################################################
# STIRRED VESSEL SURFACTANT PROPERTIES - LHS #
# ##################################################################################
def svsurf_restriction(DOE):
    for i in range(DOE.shape[0]):
        # make sure ginf > gini
        ginf = DOE.loc[i,'Maximum packing conc (mol/ m2)']
        gini = DOE.loc[i,'Initial surface conc (mol/m2)']

        old_gini = gini

        if gini>=ginf:
            random_float = np.random.uniform(low=0.05, high=0.95)  
            random_float = round(random_float, 2) 
            gini = random_float*ginf
            print(f'G_ini (mol/m2) in row {i} is modified from {old_gini} to {gini}')
        DOE.loc[i,'Initial surface conc (mol/m2)'] = gini

        # make sure Bi <= 1 or BiPeBh < 1 by modifying Bi < 1
        kd = DOE.loc[i, 'Desorption Coeff (1/s)']
        Db = DOE.loc[i, 'Bulk Diffusivity (m2/s)']
        
        Bi = kd/5
        C0 = ginf/0.02125
        BiPeBh = (kd*ginf)/(Db*C0)
        
        old_kd = kd

        if Bi>1 and BiPeBh>1:
            random_float = np.random.uniform(low=0.05, high=0.95)
            random_float = round(random_float, 2)
            kd = random_float*5
            print(f'kd (1/s) in row {i} is modified from {old_kd} to {kd}')
        DOE.loc[i,'Desorption Coeff (1/s)'] = kd

    return DOE

def svgamma_ratio(row):
    return (row['Initial surface conc (mol/m2)']/row['Maximum packing conc (mol/ m2)'])
def svPeS(row):
    return (5*0.00180625/row['Surface diffusivity (m2/s)'])
def svPeB(row):
    return (5*0.00180625/row['Bulk Diffusivity (m2/s)'])
def svBi(row):
    return (row['Desorption Coeff (1/s)']/5)
def svC0(row):
    return (row['Maximum packing conc (mol/ m2)']/0.02125)
def svh(row):
    return (row['Maximum packing conc (mol/ m2)']/(0.0425*row['C0']))
def svK(row):
    return (row['Adsorption Coeff (m3/mol s)']*row['C0']/row['Desorption Coeff (1/s)'])
def svBiPeBh(row):
    return (row['Bi']*row['PeB']*row['h'])

def runSVSurfDOE(Surf_dict,numsamples):

    SurfDOE = build.space_filling_lhs(Surf_dict, num_samples=numsamples)
    #### Adding dimensionless parameter calculation for easier post processing
    Modified_SurfDOE = svsurf_restriction(SurfDOE)
    Modified_SurfDOE['G0/Ginf'] = Modified_SurfDOE.apply(lambda row: svgamma_ratio(row), axis = 1)
    Modified_SurfDOE['PeS'] = Modified_SurfDOE.apply(lambda row: svPeS(row), axis = 1)
    Modified_SurfDOE['PeB'] = Modified_SurfDOE.apply(lambda row: svPeB(row), axis = 1)
    Modified_SurfDOE['Bi'] = Modified_SurfDOE.apply(lambda row: svBi(row), axis = 1)
    Modified_SurfDOE['C0'] = Modified_SurfDOE.apply(lambda row: svC0(row), axis = 1)
    Modified_SurfDOE['h'] = Modified_SurfDOE.apply(lambda row: svh(row), axis = 1)
    Modified_SurfDOE['K'] = Modified_SurfDOE.apply(lambda row: svK(row), axis = 1)
    Modified_SurfDOE['BiPeBh'] = Modified_SurfDOE.apply(lambda row: svBiPeBh(row), axis=1)

    return Modified_SurfDOE

