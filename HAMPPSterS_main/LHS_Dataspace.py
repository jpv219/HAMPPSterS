### Automation_simulation_run, tailored for BLUE 12.5.1
### LHS DOE Sample experiments generator
### to be run locally in psweep script
### Author: Juan Pablo Valdes, Fuyue Liang, Paula Pico
### First commit: July, 2023
### Version: 6.0
### Department of Chemical Engineering, Imperial College London
#######################################################################################################################################################################################
#######################################################################################################################################################################################

from doepy import build
import math
import numpy as np
from abc import ABC, abstractmethod


class LHS_Sampler(ABC):

    def __init__(self,LHS_space: dict,n_samples: int) -> None:

        self.LHS_space = LHS_space
        self.n_samples = n_samples
        self.param_funs = None

    def __call__(self) -> dict:

        LHS_space = build.space_filling_lhs(self.LHS_space, self.n_samples)

        modified_space = self.apply_restrictions(LHS_space)

        final_space = self.add_parameters(modified_space)

        return final_space
    
    @abstractmethod
    def apply_restrictions(self, LHS_space: dict) -> dict:
        pass

    def add_parameters(self, modified_space: dict) -> dict:
        
        for param, function in self.param_funs.items():
            modified_space[param] = modified_space.apply(lambda row: function(row), axis = 1)

        return modified_space

####################################################################################### GEOMETRY FEATURES SMX - LHS ###################################################################################

class SMX_Sampler(LHS_Sampler):

    def __init__(self, LHS_space: dict, n_samples: int) -> None:
        super().__init__(LHS_space, n_samples)

        cls = SMX_Sampler

        self.param_funs = {'Re' : cls.calcRe,
                           'SMX_pos (mm)': cls.calcPos,
                           'We': cls.calcWe}

    def __call__(self) -> dict:
        return super().__call__()
    
    def apply_restrictions(self, LHS_space: dict) -> dict:
        
        for i in range(LHS_space.shape[0]):
            
            W = LHS_space.loc[i,'Bar_Width (mm)']
            R = LHS_space.loc[i,'Radius (mm)']
            N = round(LHS_space.loc[i,'Nbars'])
            Q = LHS_space.loc[i,'Flowrate (m3/s)']
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

            LHS_space.loc[i,'Bar_Width (mm)'] = W
            LHS_space.loc[i,'Flowrate (m3/s)']  = Q
            LHS_space.loc[i,'Nbars'] = N
        
        return LHS_space
    
    @staticmethod
    def calcRe(row):
        return 1364*(row['Flowrate (m3/s)']/(math.pi*(row['Radius (mm)']/1000)**2))*(2*row['Radius (mm)']/1000)/0.615

    @staticmethod
    def calcPos(row):
        return row['Radius (mm)']

    @staticmethod
    def calcWe(row):
        return 1364*((row['Flowrate (m3/s)']/(math.pi*(row['Radius (mm)']/1000)**2))**2)*(2*row['Radius (mm)']/1000)/0.036

class SMX_SP(LHS_Sampler):

    def __init__(self, LHS_space: dict, n_samples: int) -> None:
        super().__init__(LHS_space, n_samples)

        cls = SMX_SP

        self.param_funs = {'Re' : cls.calcRe,
                           'SMX_pos (mm)': cls.calcPos}
        
    def __call__(self) -> dict:
        return super().__call__()
        
    def apply_restrictions(self, LHS_space: dict) -> dict:
        
        #Loading features
        for i in range(LHS_space.shape[0]):
            W = LHS_space.loc[i,'Bar_Width (mm)']
            R = LHS_space.loc[i,'Radius (mm)']
            N = round(LHS_space.loc[i,'Nbars'])
            Q = LHS_space.loc[i,'Flowrate (m3/s)']
            N_ele = round(LHS_space.loc[i,'NElements'])
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

            LHS_space.loc[i,'Bar_Width (mm)'] = W
            LHS_space.loc[i,'Flowrate (m3/s)']  = Q
            LHS_space.loc[i,'Nbars'] = N
            LHS_space.loc[i,'NElements'] = N_ele
        
        return LHS_space
    
    @staticmethod
    def calcRe(row):
        return 1364*(row['Flowrate (m3/s)']/(math.pi*(row['Radius (mm)']/1000)**2))*(2*row['Radius (mm)']/1000)/0.615

    @staticmethod
    def calcPos(row):
        return row['Radius (mm)']


####################################################################################### SURFACTANT PROPERTIES SMX - LHS ###################################################################################

class SMX_Surf(LHS_Sampler):

    def __init__(self, LHS_space: dict, n_samples: int) -> None:
        super().__init__(LHS_space, n_samples)

        cls = SMX_Surf

        self.param_funs = {'G0/Ginf' : cls.gamma_ratio,
                           'PeS': cls.PeS,
                           'PeB': cls.PeB,
                           'Bi': cls.Bi,
                           'Cinf': cls.Cinf,
                           'Da': cls.Da,
                           'K': cls.K}

    def __call__(self) -> dict:
        return super().__call__()
    
    def apply_restrictions(self, LHS_space: dict) -> dict:

        for i in range(LHS_space.shape[0]):
            ginf = LHS_space.loc[i,'Maximum packing conc (mol/ m2)']
            gini = LHS_space.loc[i,'Initial surface conc (mol/m2)']

            old_gini = gini

            if gini>=ginf:
                random_float = np.random.uniform(low=0.05, high=0.95)  
                random_float = round(random_float, 2) 
                gini = random_float*ginf
                print('G_ini (mol/m2) in row ' + str(i) + ' modified from ' + str(old_gini) + ' to ' + str(gini))
            LHS_space.loc[i,'Initial surface conc (mol/m2)'] = gini

        return LHS_space
    
    @staticmethod
    def gamma_ratio(row):
        return (row['Initial surface conc (mol/m2)']/row['Maximum packing conc (mol/ m2)'])
    
    @staticmethod
    def PeS(row):
        return (0.159*0.008/row['Surface diffusivity (m2/s)'])
    
    @staticmethod
    def PeB(row):
        return (0.159*0.008/row['Bulk Diffusivity (m2/s)'])
    
    @staticmethod
    def Bi(row):
        return (row['Desorption Coeff (1/s)']*0.008/0.159)
    
    @staticmethod
    def Cinf(row):
        return ((row['Desorption Coeff (1/s)']*row['Initial surface conc (mol/m2)'])/
                (row['Adsorption Coeff (m3/mol s)']*(row['Maximum packing conc (mol/ m2)']-row['Initial surface conc (mol/m2)'])))
    
    @staticmethod
    def Da(row):
        return (row['Maximum packing conc (mol/ m2)']/(row['Cinf']*0.008))
    
    @staticmethod
    def K(row):
        return (row['Adsorption Coeff (m3/mol s)']*row['Cinf']/row['Desorption Coeff (1/s)'])


####################################################################################
# # STIRRED VESSEL GEOMETRY FEATURES - LHS #
# ##################################################################################

class SV_Geom(LHS_Sampler):

    def __init__(self, LHS_space: dict, n_samples: int) -> None:
        super().__init__(LHS_space, n_samples)

        cls = SV_Geom

        self.param_funs = {'Re': cls.calcsvRe,
                           'We': cls.calcsvWe}
        
    def __call__(self) -> dict:
        return super().__call__()
    
    def apply_restrictions(self, LHS_space: dict) -> dict:

        for i in range(LHS_space.shape[0]):
            # make sure blade number is an integer
            N = round(LHS_space.loc[i,'Nblades'])
            LHS_space.loc[i,'Nblades'] = N

            # make sure Re > 500
            F = round(LHS_space.loc[i, 'Frequency (1/s)'],2)
            D = LHS_space.loc[i,'Impeller_Diameter (m)']
            oldF = F

            Re = (998*F*D**2)/1e-3

            if Re < 500:
                F = round((500*1e-3)/(998*D**2),2)
                print('Re modification')
                print(f'Frequency (1/s) in row {i} is modified from {oldF} to {F}.')
            LHS_space.loc[i,'Frequency (1/s)'] = F

            # make sure the combination of clearance and blade width is within domain
            C = LHS_space.loc[i,'Clearance (m)']
            bw = LHS_space.loc[i, 'Blade_width (m)']
            oldC = C
            # bw/2 < C and C + bw/2 < 0.05
            if bw/2 >= C:
                C = 0.005+bw/2 # 0.005 is the lower bound of clearance
                print('Clearance modification')
                print(f'Clearance (m) in row {i} is modified from {oldC}')
            LHS_space.loc[i,'Clearance (m)'] = C

            if bw/2+C >= 0.05:
                C = 0.041-bw/2 
                # 0.041 is chosen to make the new distance from vessel bottom is 0.005
                print('Clearance modification')
                print(f'Clearance (m) in row {i} is modified from {oldC}')
            LHS_space.loc[i,'Clearance (m)'] = C

        return LHS_space

    @staticmethod
    def calcsvRe(row):
        return (998*row['Frequency (1/s)']*row['Impeller_Diameter (m)']**2)/1e-3

    @staticmethod
    def calcsvWe(row):
        return (998* row['Frequency (1/s)']**2 * row['Impeller_Diameter (m)']**3)/0.035

class SV_SP(SV_Geom):

    def __init__(self, LHS_space: dict, n_samples: int) -> None:
        super().__init__(LHS_space, n_samples)

    def __call__(self) -> dict:
        return super().__call__()


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

####################################################################################
# # INTERFACIAL OSCILLATION CLEAN FEATURES - LHS #
# ##################################################################################

# Apply restrictions to chosen properties
def IOclean_restrictions(DOE):

    for i in range(DOE.shape[0]):

        # Ensure wave number is an integer
        K = round(DOE.loc[i,'Wave_number (1/m)'])
        DOE.loc[i,'Wave_number (1/m)'] = K

        # Ensure rho_l >= rho_g by changing rho_g
        rho_l = DOE.loc[i,'Density_l (kg/m3)']
        rho_g = DOE.loc[i,'Density_g (kg/m3)']

        old_rho_g = rho_g

        if rho_g>rho_l:
            random_float = np.random.uniform(low=1, high=1e3)  
            random_float = round(random_float, 2) 
            rho_g = rho_l/random_float
            print(f'rho_g (kg/m3) in row {i} is modified from {old_rho_g} to {rho_g}')
        DOE.loc[i,'Density_g (kg/m3)'] = rho_g

        # Ensure mu_l >= mu_g by changing mu_g
        mu_l = DOE.loc[i,'Viscosity_l (Pa*s)']
        mu_g = DOE.loc[i,'Viscosity_g (Pa*s)']

        old_mu_g = mu_g

        if mu_g>mu_l:
            random_float = np.random.uniform(low=1, high=1e3)  
            random_float = round(random_float, 2) 
            mu_g = mu_l/random_float
            print(f'mu_g (Pa*s) in row {i} is modified from {old_mu_g} to {mu_g}')
        DOE.loc[i,'Viscosity_g (Pa*s)'] = mu_g

    return DOE

def IOa0(row):
    return row['epsilon']/row['Wave_number (1/m)']

def IOrho_r(row):
    return row['Density_l (kg/m3)']/row['Density_g (kg/m3)']

def IOmu_r(row):
    return row['Viscosity_l (Pa*s)']/row['Viscosity_g (Pa*s)']

def IOLa_g(row):
    return ((row['Surf_tension (N/m)']*row['Density_g (kg/m3)'])/(row['Wave_number (1/m)']*row['Viscosity_g (Pa*s)']**2))

def IOLa_l(row):
    return ((row['Surf_tension (N/m)']*row['Density_l (kg/m3)'])/(row['Wave_number (1/m)']*row['Viscosity_l (Pa*s)']**2))

def IOGa_g(row):
    return ((row['Gravity (m/s2)']*row['Density_g (kg/m3)']**2)/((row['Viscosity_g (Pa*s)']**2)*(row['Wave_number (1/m)']**3)))

def IOGa_l(row):
    return ((row['Gravity (m/s2)']*row['Density_l (kg/m3)']**2)/((row['Viscosity_l (Pa*s)']**2)*(row['Wave_number (1/m)']**3)))

def IOBo_l(row):
    return ((row['Density_l (kg/m3)']*row['Gravity (m/s2)'])/(row['Surf_tension (N/m)']*row['Wave_number (1/m)']**2))

def IOomegasq(row):
    return (((row['Gravity (m/s2)']*row['Wave_number (1/m)']*(row['Density_l (kg/m3)'] - row['Density_g (kg/m3)']))/(row['Density_l (kg/m3)'] + row['Density_g (kg/m3)'])) 
            + ((row['Surf_tension (N/m)']*row['Wave_number (1/m)']**3)/(row['Density_l (kg/m3)'] + row['Density_g (kg/m3)'])))

def IOomega(row):
    omega_sq = IOomegasq(row)
    return omega_sq**(1/2)

def IOT(row):
    return (2*math.pi)/(IOomega(row))

# Final time is 5T plus 0.5%
def IOt_final(row):
    return 5*IOT(row) + 0.005*5*IOT(row)

def IOdelta_t_sn(row):
    return IOT(row)/20

def runIODOE(IO_dict,numsamples):

    ## Initial LHS with no restrictions
    LHS_DOE = build.space_filling_lhs(IO_dict,num_samples = numsamples)
    Modified_DOE = IOclean_restrictions(LHS_DOE)
    Modified_DOE['a0'] = Modified_DOE.apply(lambda row: IOa0(row), axis = 1)
    Modified_DOE['Density_ratio'] = Modified_DOE.apply(lambda row: IOrho_r(row), axis = 1)
    Modified_DOE['Viscosity_ratio'] = Modified_DOE.apply(lambda row: IOmu_r(row), axis = 1)
    Modified_DOE['La_g'] = Modified_DOE.apply(lambda row: IOLa_g(row), axis = 1)
    Modified_DOE['La_l'] = Modified_DOE.apply(lambda row: IOLa_l(row), axis = 1)
    Modified_DOE['Ga_g'] = Modified_DOE.apply(lambda row: IOGa_g(row), axis = 1)
    Modified_DOE['Ga_l'] = Modified_DOE.apply(lambda row: IOGa_l(row), axis = 1)
    Modified_DOE['Bo_l'] = Modified_DOE.apply(lambda row: IOBo_l(row), axis = 1)
    Modified_DOE['omega'] = Modified_DOE.apply(lambda row: IOomega(row), axis = 1)
    Modified_DOE['T (s)'] = Modified_DOE.apply(lambda row: IOT(row), axis = 1)
    Modified_DOE['t_final (s)'] = Modified_DOE.apply(lambda row: IOt_final(row), axis = 1)
    Modified_DOE['delta_t_sn (s)'] = Modified_DOE.apply(lambda row: IOdelta_t_sn(row), axis = 1)
    
    return Modified_DOE