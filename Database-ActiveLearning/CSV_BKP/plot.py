##########################################################################
#### Run listing and early visualization
#### Author : Juan Pablo Valdes
##########################################################################
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import math

#### PLOT PARAMETERS #####
#Plot parameters
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ['Computer Modern']})

SMALL_SIZE = 8
MEDIUM_SIZE = 12
BIGGER_SIZE = 13
plt.rc('font', size=BIGGER_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=BIGGER_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=BIGGER_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=BIGGER_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=BIGGER_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=MEDIUM_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title
#######

case = sys.argv[1]

# Read backup csv with post-processed data and DOE table from pkl file

file_count = len(os.listdir(f'finished_{case}'))

df_list = []
df_DOE_list = []

## Loop concatenating DOE and csv files from different parametric sweeps
for i in range(1,file_count+1):

    csv_filename = f'{case}_{i}.csv'
    doe_pickle_filename = f'LHS_{case}_{i}.pkl'
    
    # Check if the CSV file exists
    if os.path.isfile(os.path.join(f'finished_{case}/', csv_filename)):
        data = pd.read_csv(os.path.join(f'finished_{case}/', csv_filename))
        df_list.append(data)
    
    # Check if the pickle file exists
    if os.path.isfile(os.path.join(f'../DOE/fin_DOE_{case}', doe_pickle_filename)):
        DOE = pd.read_pickle(os.path.join(f'../DOE/fin_DOE_{case}', doe_pickle_filename))
        df_DOE_list.append(DOE)

# Concatenate all files to process at the same time
df = pd.concat(df_list, ignore_index=True)
df_DOE = pd.concat(df_DOE_list, ignore_index=True)

run_list = []
run_count = 1 # Assuming at least one run exists, since last/single run is not counted in the loop  

if case == 'surf' or case == 'geom':
    ## Filling NaN values with case names
    df['Run_ID'].fillna(method='ffill', inplace=True)
    df['Interfacial Area'].fillna(method='ffill', inplace=True)
    df['Number of Drops'].fillna(method='ffill', inplace=True)
    df['V/VCAP'] = df['DSD']/(4*math.pi/3*(math.sqrt(0.036/(9.81*(1364-970))))**3)


# Count how many runs stored successfully in the CSV.
for i in range(1,len(df['Run_ID'])):
    
    if df['Run_ID'].iloc[i-1] == df['Run_ID'].iloc[i]:
        continue
    else:
        run_count +=1
        run_list.append(df['Run_ID'].iloc[i-1])

run_list.append(df['Run_ID'].iloc[-1])
sorted_runs = sorted(run_list, key=lambda x: int(x.split('_')[-1]))


print(f'Number of runs completed for case {case} : {run_count}')
print(sorted_runs)

# Merge input paramters from psweep run with cases successfully ran.
df_updated = df_DOE[df_DOE.index.isin([int(run.split('_')[-1])-1 for run in sorted_runs])]

##### SINGLE PHASE#####

if case == 'sp_geom':

    choice = input("plot hydrodynamics? (y/n): ")

    # Plot segment for single-phase cases
    if choice.lower() == 'y' or choice.lower() == 'yes':

        df_updated.index = [f'run_sp_{i+1}' for i in df_updated.index]
        
        num_cases = input('List all case numbers you want to plot separated by spaces: ')

        ## Storing and splitting numbers inputted by the user.
        numbers = num_cases.split()

        ## Error if non numeric values
        if not num_cases.replace(' ','').isdigit():
            raise ValueError('Non-numeric value entered as input. Re-check input values.')

        case_list = [f'run_sp_{n}' for n in numbers]

        #plotting hydrodynamics:
        color_map = sns.color_palette("husl", len(case_list))
        markers = ['o', 's', 'D', '^', 'v', '>', '<', 'p', '*', 'h', '+', 'x']
        ylabels = ['$e_{max}$', 'Q', '$e_{diss}$','$\dot{\gamma}$ $(s^{-1})$', 'P (Pa)', '$u$ (m/s)']

        fig, axes = plt.subplots(3, 2, figsize=(16, 12), sharex=True)
        plt.subplots_adjust(wspace=0.4, hspace=0.4)
        legend_handles = []
        cases_plotted = []
        Re_plotted = []

        ## Looping through the cases to be plotted
        for jdx, case in enumerate(case_list):

            filtered_df = df[df['Run_ID'] == case]

            ## Error handling
            if filtered_df.shape[0] == 0:
                print(f'Case with ID {case} does not exist, ignoring plot.')
                continue
            if case in cases_plotted:
                print ('case duplicated, ignoring')
                continue
            
            Re = df_updated[df_updated.index==case]['Re'].values[0]

            cases_plotted.append(case)
            Re_plotted.append(Re)
        
            for idx, feature in enumerate(['E_max','Q','E_diss','Gamma','Pressure','Velocity']):

                row = idx // 2  # Calculate the row for the subplot
                col = idx % 2   # Calculate the column for the subplot
                ax = axes[row, col]

                L = filtered_df['Length']
                L_norm = filtered_df['Length']/max(filtered_df['Length'])
                hyd_feat = filtered_df[feature]
                color = color_map[jdx % len(color_map)]
                marker = markers[jdx % len(markers)]

                line, = ax.plot(L_norm,hyd_feat,marker=marker,markersize = 5, 
                        markerfacecolor = color, markeredgewidth = 1.0, markeredgecolor = 'k',
                        ls=('-'),lw=3.0,color=color,label=f'{case}')
                
                ax.set_title(f'Hydrodynamic field: {feature}')
                ax.set_xlabel('$L/L_{max}$')
                ax.set_ylabel(f'{ylabels[idx]}')
                
            legend_handles.append(line)

        # Combining case and Re list to create legend label as a tuple with idx position: enumerate to extract idx a zip of cases and Re
        legend_list = [(idx, case + ': Re = {:.2f}'.format(Re)) for idx, (case, Re) in enumerate(zip(cases_plotted,Re_plotted))]

        # Sorting legend list by Re, splitting the label at the = to extract the numerical value
        sorted_legend = sorted(legend_list, key=lambda x: float(x[1].split('= ')[-1]))

        # Sorting legend_handles object by idx sorted above through Re. zip(list(zip)) construction used to switch between tuples and lists
        legend_handles_sorted = sorted(zip(list(zip(*sorted_legend))[0],legend_handles), key = lambda x: x[0])
        
        fig.legend(handles=list(zip(*legend_handles_sorted))[1], labels=list(zip(*sorted_legend))[1], loc='upper right', bbox_to_anchor=(1.0, 1.0))
        plt.show()


    elif choice.lower() == 'n':
        pass
        
    else:
        print("Invalid choice. Please enter 'yes' or 'no'.")

#### SURFACTANTS ######

elif case == 'surf':

    choice = input("plot dispersion metrics? (y/n): ")

    if choice.lower() == 'y' or choice.lower() == 'yes':

        df_updated.index = [f'run_surf_{i+1}' for i in df_updated.index]

        num_cases = input('List all case numbers you want to plot separated by spaces: ')

        ## Storing and splitting numbers inputted by the user.
        numbers = num_cases.split()

        ## Error if non numeric values
        if not num_cases.replace(' ','').isdigit():
            raise ValueError('Non-numeric value entered as input. Re-check input values.')

        case_list = [f'run_surf_{n}' for n in numbers]

        #plotting:
        color_map = sns.color_palette("husl", len(case_list))
        markers = ['o', 's', 'D', '^', 'v', '>', '<', 'p', '*', 'h', '+', 'x']

        fig, axes = plt.subplots(2, 1, figsize=(16, 12), sharex=True)
        plt.subplots_adjust(wspace=0.4, hspace=0.4)
        sns.set(style="whitegrid")

        #Legend handling
        legend_handles = []
        cases_plotted = []
        property_keys = ['Bi', 'Da', 'PeS','Elasticity Coeff']

        properties = {}

        ## Looping through the cases to be plotted
        for jdx, case in enumerate(case_list):

            filtered_df = df[df['Run_ID'] == case]

            ## Error handling
            if filtered_df.shape[0] == 0:
                print(f'Case with ID {case} does not exist, ignoring plot.')
                continue
            if case in cases_plotted:
                print ('case duplicated, ignoring')
                continue
            
            case_properties = {}

            for key in property_keys:
                case_properties[f'{key}'] = df_updated[df_updated.index==case][f'{key}'].values[0]

            ## Appending for later legend usage
            cases_plotted.append(case)
            ## Dictionary containing propety dictionaries
            properties[case] = case_properties

            sns.histplot(filtered_df['V/VCAP'], kde=True, ax=axes[0])
            axes[0].set_ylabel("Frequency")
            axes[0].set_title(f"Droplet Size Distribution for {case} with KDE")

            # Plot PDF and CDF
            sns.kdeplot(filtered_df['V/VCAP'], ax=axes[1], label="PDF", cumulative=True)
            sns.histplot(filtered_df['V/VCAP'], ax=axes[1], kde=True, stat="density", common_norm=False, color='red', label="PDF")
            axes[1].set_xlabel("Droplet Size")
            axes[1].set_ylabel("Density/CDF")
            axes[1].set_title(f"PDF and CDF for {case}")
            axes[1].legend()
        
        # Show the plot for the current case
        plt.show()



    elif choice.lower() == 'n':
        pass
        
    else:
        print("Invalid choice. Please enter 'yes' or 'no'.")

else:
    print("Invalid case to plot, select either sp_geom, geom or surf")



