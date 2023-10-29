import pandas as pd
import glob
import sys
import csv
import os
import numpy as np
import math

import matplotlib.pyplot as plt
import matplotlib.pylab as pl
from matplotlib import rc
import seaborn as sns

# For fitting test #
from scipy import stats
# import statsmodels.api as sm
import pylab as py
import ast

import matplotlib as mpl
mpl.rcParams['axes.linewidth'] = 3 #set the value globally
from matplotlib.ticker import FormatStrFormatter
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ['Times']})

case = 'sp_svgeom'#sys.srgv[1]
csv_path = '/home/fl18/Desktop/automatework/ML_auto/SMX_DeepLearning/Database-ActiveLearning/CSV_BKP'
doe_path = '/home/fl18/Desktop/automatework/ML_auto/SMX_DeepLearning/Database-ActiveLearning/DOE'

# Read the backup csv with post-processed data and DOE table from pkl file #
file_count = len(os.listdir(os.path.join(csv_path, f'finished_{case}')))

df_list = []
df_DOE_list = []
# Loop concatenating DOE and csv files from different paramatric sweeps
for i in range(1,file_count+1):
    csv_filename = f'{case}_{i}.csv'
    doe_pickle_filename = f'LHS_{case}_{i}.pkl'

    # Check if the CSV file exists
    if os.path.isfile(os.path.join(csv_path,f'finished_{case}', csv_filename)):
        data = pd.read_csv(os.path.join(csv_path, f'finished_{case}', csv_filename))
        df_list.append(data)

    # Check if the pickle file exists
    if os.path.isfile(os.path.join(doe_path, f'finished_{case}', doe_pickle_filename)):
        DOE = pd.read_pickle(os.path.join(doe_path, f'finished_{case}', doe_pickle_filename))
        df_DOE_list.append(DOE)

# Concatenate all files to proecss at the same time
df = pd.concat(df_list, ignore_index=True)
df_DOE = pd.concat(df_DOE_list, ignore_index=True)

# Read how many runs are successfully stored
### would ned to modify if a complpete csv is saved from workflow (NaN for failed cases)
run_list = df['Run'].tolist()
sorted_runs = sorted(run_list, key=lambda x: int(x.split('_')[-1]))


print(f'Number of runs completed for case {case}: {len(run_list)}')
print(sorted_runs)

# Merge input parameters from psweep run with cases successfully finished
df_DOE_updated = df_DOE[df_DOE.index.isin([int(run.split('_')[-1])-1 for run in sorted_runs])]
    
### Interactive plotting window ###
if case == 'sp_svgeom':
    choice = input("plot hydrodynamics? (y/n): ")

    # plot segment for single-phase cases
    if choice.lower() == 'y' or choice.lower() == 'yes':
        ## Replacing index in dfDOE with RunID to match later with case results
        df_DOE_updated.index = [f'run_spsv_{i+1}' for i in df_DOE_updated.index]
        numbers = []

        num_cases = input('List all case numbers you want to plot separated by spaces: ')

        if num_cases == 'all':
            for elem in sorted_runs:
                num = elem.split('_')[-1]
                numbers.append(int(num))
        else:
            # storing and splitting numbers inputted by the user.
            numbers = num_cases.split()

        ## Error if non numeric values
        if num_cases != 'all' and not num_cases.replace(' ','').isdigit():
            raise ValueError('Non-numeric value entered as input. Re-check input values.')

        case_list = [f'run_spsv_{n}' for n in numbers]
        
        ## Looping through the cases to be plotted
        color_map = sns.color_palette("muted", len(case_list))
        markers = ['o', 's', 'D', '^', 'v', '>', '<', 'p', '*', 'h', '+', 'x']
        xlabels = ['Q', 'Pres', r'$U_r/V_{tip}$', r'$U_z/V_{tip}$']
        ylabels = ['Q_over_line', r'$U_r/V_{tip}$', r'$U_z/V_{tip}$']

        ## along vessel height ##
        fig1, axes1 = plt.subplots(1,4,figsize=(20,8),sharey=True)
        ## along vessel height ##
        fig2, axes2 = plt.subplots(3,1,figsize=(8,15),sharex=True)

        cases_plotted = []
        Re_plotted = []
        legend_handles = []

        for idx, case in enumerate(case_list):

            filtered_df = df[df['Run'] == case].reset_index(drop=True)
            
            ## Error handling
            if filtered_df.shape[0] == 0:
                print(f'Case with ID {case} does not exist, ignoring plot.')
                continue
            if case in cases_plotted:
                print ('case duplicated, ignoring')
                continue

            Re = df_DOE_updated[df_DOE_updated.index==case]['Re'].values[0]
            D = df_DOE_updated[df_DOE_updated.index==case]['Impeller_Diameter (m)'].values[0]
            N = df_DOE_updated[df_DOE_updated.index==case]['Frequency (1/s)'].values[0]
            v_tip = math.pi*N*D
            
            cases_plotted.append(case)
            Re_plotted.append(Re)

            ## along vessel height ##
            for jdx,jfeature in enumerate(['Q','Pres','Ur', 'Uz']):
                
                ax = axes1[jdx]

                filtered_df[jfeature] = filtered_df[jfeature].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
                filtered_df['Height'] = filtered_df['Height'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
                H_norm = np.array(filtered_df['Height'][0])/max(filtered_df['Height'][0])
                if jfeature == 'Ur' or jfeature == 'Uz':
                    filtered_df[jfeature][0] = np.array(filtered_df[jfeature][0]/v_tip)
        
                
                hyd_feat = filtered_df[jfeature][0]
                color = color_map[idx]
                marker = markers[idx]
                
                line, = ax.plot(hyd_feat,H_norm, 
                                color=color,marker=marker, markevery=5,
                                label=f'{case}')

                ax.set_title(f'{jfeature}')
                ax.set_ylabel('$H/H_T$')
                ax.set_xlabel(f'{xlabels[jdx]}')

            ## along vessel height ##
            for kdx,kfeature in enumerate(['Q_over_line','Ur_over_line', 'Uz_over_line']):
                
                ax = axes2[kdx]

                filtered_df[kfeature] = filtered_df[kfeature].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
                filtered_df['arc_length'] = filtered_df['arc_length'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
                arc_norm = np.array(filtered_df['arc_length'][0])/max(filtered_df['arc_length'][0])
                if not kfeature == 'Q_over_line':
                    filtered_df[kfeature][0] = np.array(filtered_df[kfeature][0]/v_tip)
        
                hyd_feat = filtered_df[kfeature][0]
                color = color_map[idx]
                marker = markers[idx]
                
                line, = ax.plot(arc_norm,hyd_feat, 
                                color=color,marker=marker, markevery=5,
                                label=f'{case}')

                ax.set_title(f'{kfeature}')
                ax.set_xlabel('$R/D_T$')
                ax.set_ylabel(f'{ylabels[kdx]}')
            
            legend_handles.append(line)
        
        # Combining case and Re list to create legend label as a tuple with idx position: enumerate to extract idx a zip of cases and Re
        legend_list1 = [(jdx, case+ ': Re = {:.2f}'.format(Re)) for jdx, (case, Re) in enumerate(zip(cases_plotted,Re_plotted))]
        legend_list2 = [(kdx, case+ ': Re = {:.2f}'.format(Re)) for kdx, (case, Re) in enumerate(zip(cases_plotted,Re_plotted))]

        # Sorting legend list by Re, splitting the label at the = to extract the numerical value
        sorted_legend1 = sorted(legend_list1, key=lambda x: float(x[1].split('= ')[-1]))
        sorted_legend2 = sorted(legend_list2, key=lambda x: float(x[1].split('= ')[-1]))

        # Sorting legend_handles object by idx sorted above through Re. zip(list(zip)) construction used to switch between tuples and lists
        legend_handles_sorted1 = sorted(zip(list(zip(*sorted_legend1))[0],legend_handles), key = lambda x: x[0])
        legend_handles_sorted2 = sorted(zip(list(zip(*sorted_legend2))[0],legend_handles), key = lambda x: x[0])
        
        fig1.legend(handles=list(zip(*legend_handles_sorted1))[1], labels=list(zip(*sorted_legend1))[1], loc='upper right', bbox_to_anchor=(1.0, 1.0))
        fig1.suptitle('Hydrodynamic field along tank height', fontsize=20)
        plt.show()
        
        fig2.legend(handles=list(zip(*legend_handles_sorted2))[1], labels=list(zip(*sorted_legend2))[1], loc='upper right', bbox_to_anchor=(1.0, 1.0))
        fig2.suptitle('Hydrodynamic field at plane of the impeller center', fontsize=20)
        plt.show()
            # # convert data in dataframe into right type
            # columns = ['Height', 'Q', 'Pres', 'Ur', 'Uth', 'Uz', 
            #            'arc_length','Q_over_line', 'Ur_over_line', 'Uz_over_line']
            # Vels = ['Ur', 'Uth', 'Uz', 'Ur_over_line', 'Uz_over_line']


    elif choice.lower() == 'n':
        pass

    else:
        print("Invalide choice. Please enter 'yes' or 'no'.")