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
from matplotlib.lines import Line2D
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

case = 'svgeom'#'sp_svgeom'#sys.srgv[1]
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

#######################################################
# Plotting Func DSD for Two phase cases
#######################################################
def plot_DSD(df, case_list, sorting_key, param_keys, key_map,plot_case):#,x_axis_format):
    # plotting params:
    color_map = sns.color_palette("muted", len(case_list))
    markers = ['o', 's', 'D', '^', 'v', '>', '<', 'p', '*', 'h', '+', 'x']

    fig, axes = plt.subplots(2, 2,figsize=(10, 6), sharex=False)
    plt.subplots_adjust(wspace=0.4, hspace=0.4)
    sns.set(style="whitegrid")

    #Legend handling
    legend_handles = []
    cases_plotted = []
    param_plotted = []

    # Number of drops and IA
    Nd_list = []
    IA_list = []

    # Looping through the cases to be plotted
    for jdx, case in enumerate(case_list):
        
        # selecting case to plot
        filtered_df = df[df['Run'] == case].reset_index(drop=True)

        ## Error handling
        if filtered_df.shape[0] == 0:
            print(f'Case with ID {case} does not exist, ignoring plot.')
            continue
        if case in cases_plotted:
            print ('case duplicated, ignoring')
            continue


        ## Appending for later legend and label sorting, and Nd/IA vs. surf. plot construction
        cases_plotted.append(case)
        Nd_list.append(filtered_df['Nd'].values[0])
        IA_list.append(filtered_df['IntA'].values[0])

        color = color_map[jdx % len(color_map)]
        marker = markers[jdx % len(markers)]
        marker_frequency = 10

        # update DSD to V/VCAP
        l_cap = (0.035/(9.80665*(998-824)))**0.5
        v_cap = (4/3) * math.pi * (l_cap/2)**3
        filtered_df['DSD'] = filtered_df['DSD'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        DSD_norm = np.log10(np.array(filtered_df['DSD'][0])/v_cap)
        ## plot the histogram for DSD
        sns.histplot(DSD_norm, kde=False, ax=axes[0,0],bins=12, color = color,
                         fill=False)
        # axes[0,0].xaxis.set_major_formatter(plt.FuncFormatter(x_axis_format))
        axes[0,0].set_ylabel("$N_{d}$")
        axes[0,0].set_xlabel("$V/V_{cap}$")
        axes[0,0].set_title(f"Droplet Size Distribution")
        legend_handles.append(Line2D([0], [0], color=color,marker=marker, lw=2))
        ## plot PDF and CDF
        sns.kdeplot(DSD_norm, ax=axes[0,1],color=color, 
                        marker= marker, markevery=marker_frequency, markersize = 6, 
                        markeredgecolor = 'k',ls=('-'),lw=2.0,fill = False, legend=False)
        # axes[0,1].xaxis.set_major_formatter(plt.FuncFormatter(x_axis_format))
        axes[0,1].set_xlabel("$V/V_{cap}$")
        axes[0,1].set_ylabel("$PDF$")

        sns.kdeplot(DSD_norm, cumulative=True, ax=axes[1,0], color=color, 
                    marker=marker,markevery=marker_frequency, markersize = 6, 
                    markeredgecolor = 'k',ls=('-.'),lw=2.0, legend=False)
        # axes[1,0].xaxis.set_major_formatter(plt.FuncFormatter(x_axis_format))
        axes[1,0].set_xlabel("$V/V_{cap}$")
        axes[1,0].set_ylabel("$CDF$")

        # initializing property dictionary
        case_params = {}
        # Extracting values of interest from DOE dataframe
        for key in param_keys:
            case_params[f'{key}'] = df_DOE_updated[df_DOE_updated.index==case][f'{key}'].values[0]

        param = case_params[key_map[sorting_key]]
        param_plotted.append(param)
    
    ## plot ND and IA vs. surfactant features
    sns.scatterplot(x=param_plotted, y=Nd_list, markers='*',
                    color='c', s=120,
                    edgecolor='black', ax=axes[1,1])
    axes[1,1].set_xlabel(f'{sorting_key}')
    axes[1,1].set_ylabel('$N_{d}$', color='tab:cyan')
    axes[1,1].tick_params(axis='y',labelcolor='tab:cyan')

    ### second y_axis
    ax2 = axes[1,1].twinx()
    ### Set style for second axis
    ax2.grid(False)
    for spine in ax2.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(0.2)

    sns.scatterplot(x=param_plotted, y=IA_list, marker='^', 
                    color='brown', s=120,
                    edgecolor='black',ax=ax2)
    ax2.set_ylabel('Interfacial Area', color='tab:brown')
    ax2.tick_params(axis='y', labelcolor='tab:brown')
    axes[1,1].set_title(f'Dispersion performance vs {sorting_key}')

    ## Legend handling: Creating unsorted list of labels and indices for the legend (as tuple)
    legend_list = [(idx, f'{case}: {sorting_key} ' + '= {:.5f}'.format(param)) for idx, (case, param) in enumerate(zip(cases_plotted,param_plotted))]
    
    # Sorting legend values by parameter from sorting key
    sorted_legend = sorted(legend_list, key= lambda x: float(x[1].split('= ')[-1]))

    # Sorting legend_handles object by idx sorted above from parameter chosen. zip(list(zip)) construction used to switch between tuples and lists
    legend_handles_sorted = sorted(zip(list(zip(*sorted_legend))[0],legend_handles), key = lambda x: x[0])

    fig.legend(handles=list(zip(*legend_handles_sorted))[1], labels=list(zip(*sorted_legend))[1], loc='upper right', bbox_to_anchor=(1.0, 1.0))
    plt.show()

    if plot_case=='svgeom':
        # Plot DSD for all the features
        fig1,axes1 = plt.subplots(2,4,figsize=(20,6))

        for kdx, key in enumerate(param_keys):
            row = kdx // 4
            col = kdx % 4
            ax = axes1[row,col]

            param_cases = []
            Nd_list =[]
            IA_list = []
            for case in case_list:
                param_case = df_DOE_updated[df_DOE_updated.index==case][f'{key}'].values[0]
                filtered_df = df[df['Run'] == case].reset_index(drop=True)

                param_cases.append(param_case)
                Nd_list.append(filtered_df['Nd'].values[0])
                IA_list.append(filtered_df['IntA'].values[0])

            ## plot ND and IA vs. surfactant features
            sns.scatterplot(x=param_cases, y=Nd_list, markers='*',
                            color='c', s=120,
                            edgecolor='black', ax=ax)
            ax.set_ylabel('$N_{d}$', color='tab:cyan')
            ax.tick_params(axis='y',labelcolor='tab:cyan')

            ### second y_axis
            ax0 = ax.twinx()
            ### Set style for second axis
            ax0.grid(False)
            for spine in ax0.spines.values():
                spine.set_edgecolor('black')
                spine.set_linewidth(0.2)

            sns.scatterplot(x=param_cases, y=IA_list, marker='^', 
                            color='brown', s=120,
                            edgecolor='black',ax=ax0)
            ax0.set_ylabel('Interfacial Area', color='tab:brown')
            ax0.tick_params(axis='y', labelcolor='tab:brown')
            ax.set_title(f'{key}')
        fig1.tight_layout()
        fig1.suptitle('Dispersion performance vs Mixer geometry parameters', fontsize=20)
        plt.show()

    elif plot_case == 'svsurf':
        # Plot DSD for all the features
        fig1,axes1 = plt.subplots(2,2,figsize=(20,6))

        for kdx, key in enumerate(param_keys):
            row = kdx // 2
            col = kdx % 2
            ax = axes1[row,col]

            param_cases = []
            Nd_list =[]
            IA_list = []
            for case in case_list:
                param_case = df_DOE_updated[df_DOE_updated.index==case][f'{key}'].values[0]
                filtered_df = df[df['Run'] == case].reset_index(drop=True)

                param_cases.append(param_case)
                Nd_list.append(filtered_df['Nd'].values[0])
                IA_list.append(filtered_df['IntA'].values[0])

            ## plot ND and IA vs. surfactant features
            sns.scatterplot(x=param_cases, y=Nd_list, markers='*',
                            color='c', s=120,
                            edgecolor='black', ax=ax)
            ax.set_ylabel('$N_{d}$', color='tab:cyan')
            ax.tick_params(axis='y',labelcolor='tab:cyan')

            ### second y_axis
            ax0 = ax.twinx()
            ### Set style for second axis
            ax0.grid(False)
            for spine in ax0.spines.values():
                spine.set_edgecolor('black')
                spine.set_linewidth(0.2)

            sns.scatterplot(x=param_cases, y=IA_list, marker='^', 
                            color='brown', s=120,
                            edgecolor='black',ax=ax0)
            ax0.set_ylabel('Interfacial Area', color='tab:brown')
            ax0.tick_params(axis='y', labelcolor='tab:brown')
            ax.set_title(f'{key}')
        fig1.suptitle('Dispersion performance vs Surfactant properties', fontsize=20)
        plt.show()

### Single Phase ###
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

    elif choice.lower() == 'n':
        pass

    else:
        print("Invalide choice. Please enter 'yes' or 'no'.")

##### Surfactant-laden cases #######
elif case == 'svsurf':

    choice = input("plot dispersion metrices? (y/n): ")

    if choice.lower() == 'y' or choice.lower() == 'yes':
        # Replacing index in dfDOE with RunID to match later with case results
        df_DOE_updated.index = [f'run_svsurf_{i+1}' for i in df_DOE_updated.index]
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

        case_list = [f'run_svsurf_{n}' for n in numbers]

        ## Surfactant parameter chosen to label and sort plots
        sorting_key = input('Sort DSD plots by? (choose between h, Bi, PeS, Beta): ')

        param_keys = ['Bi', 'h', 'PeS', 'Elasticity Coeff']
        key_map = {'h':'h', 'Bi': 'Bi', 'PeS': 'PeS', 'Beta': 'Elasticity Coeff'}

        # x_axis_format = x_axis_formatter

        ## Plotting
        plot_DSD(df,case_list,sorting_key, param_keys,key_map,plot_case='svsurf')
        

    elif choice.lower() == 'n':
        pass
        
    else:
        print("Invalid choice. Please enter 'yes' or 'no'.")


### Two-phase Geometry ###
elif case == 'svgeom':
    choice = input("plot dispersion metrics? (y/n): ")

    if choice.lower() == 'y' or choice.lower() == 'yes':

        ## Replacing index in dfDOE with RunID to match later with case results
        df_DOE_updated.index = [f'run_svgeom_{i+1}' for i in df_DOE_updated.index]
        numbers = []

        num_cases = input('List all case numbers you want to plot separated by spaces: ')

        if num_cases == 'all':
            for elem in sorted_runs:
                num = elem.split('_')[-1]
                numbers.append(int(num))
        else:
            ## Storing and splitting numbers inputted by the user.
            numbers = num_cases.split()

        ## Error if non numeric values
        if num_cases != 'all' and not num_cases.replace(' ','').isdigit():
            raise ValueError('Non-numeric value entered as input. Re-check input values.')

        ## cases selected to be plotted
        case_list = [f'run_svgeom_{n}' for n in numbers]

        ## Geomtry parameter chosen to label and sort plots
        sorting_key = input('Sort DSD plots by? (choose between Di, f, C, W, Th, Nb, Inc, Re): ')

        param_keys = ['Impeller_Diameter (m)', 'Frequency (1/s)', 'Clearance (m)',
       'Blade_width (m)', 'Blade_thickness (m)', 'Nblades', 'Inclination',
       'Re']
        
        key_map = {'Di':'Impeller_Diameter (m)', 'f':'Frequency (1/s)', 'C':'Clearance (m)', 
                   'W':'Blade_width (m)', 'Th':'Blade_thickness (m)', 'Nb':'Nblades', 
                   'Inc':'Inclination', 'Re':'Re'}
        
        ## Plotting
        plot_DSD(df,case_list,sorting_key, param_keys,key_map,plot_case='svgeom')
        

    elif choice.lower() == 'n':
        pass
        
    else:
        print("Invalid choice. Please enter 'yes' or 'no'.")

else:
    print("Invalid case to plot, select either sp_svgeom, svgeom or svsurf")
