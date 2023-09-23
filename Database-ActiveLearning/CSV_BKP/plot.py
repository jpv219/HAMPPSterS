##########################################################################
#### Run listing and early visualization
#### Author : Juan Pablo Valdes
##########################################################################
import pandas as pd

case = 'sp_geom'

# Read backup csv with post-process data and DOE table from pkl file
df = pd.read_csv(f'old_csv/{case}.csv')
df_DOE = pd.read_pickle(f'../DOE/old_DOE/LHS_{case}.pkl')
run_list = []
run_count = 1 # Assuming at least one run exists, since last/single run is not counted in the loop    

# Count how many runs stored successfully in the CSV.
for i in range(1,len(df['Run_ID'])-1):
    
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

df_updated.index = [f'run_{case}_{i+1}' for i in df_updated.index]

# Plot segment for single-phase cases

if case == 'sp_geom':

    choice = input("plot hydrodynamics? (yes/no): ")

    if choice.lower() == 'yes':

        num_cases = input('List all case numbers you want to plot separated by spaces: ')
        numbers = num_cases.split()
        case_list = [f'run_sp_{n}' for n in numbers]

        import matplotlib.pyplot as plt
        import seaborn as sns


        #Plot parameters
        color_map = sns.color_palette("husl", len(case_list))
        markers = ['o', 's', 'D', '^', 'v', '>', '<', 'p', '*', 'h', '+', 'x']
        ylabels = ['$e_{max}$', 'Q', '$e_{diss}$','$\dot{\gamma}$ $(s^{-1})$', 'P (Pa)', '$u$ (m/s)']
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

        #plotting hydrodynamics:

        fig, axes = plt.subplots(3, 2, figsize=(16, 12), sharex=True)
        plt.subplots_adjust(wspace=0.4, hspace=0.4)
        legend_handles = []

        for idx, feature in enumerate(['E_max','Q','E_diss','Gamma','Pressure','Velocity']):

            row = idx // 2  # Calculate the row for the subplot
            col = idx % 2   # Calculate the column for the subplot
            ax = axes[row, col]
        
            for case, jdx in zip(case_list, range(len(case_list))):
                filtered_df = df[df['Run_ID'] == case]
                L = filtered_df['Length']
                L_norm = filtered_df['Length']/max(filtered_df['Length'])
                hyd_feat = filtered_df[feature]
                color = color_map[jdx % len(color_map)]
                marker = markers[jdx % len(markers)]

                line, = ax.plot(L_norm,hyd_feat,marker=marker,markersize = 5, 
                        markerfacecolor = color, markeredgewidth = 1.0, markeredgecolor = 'k',
                        ls=('-'),lw=3.0,color=color,label=f'{case}')
                
                legend_handles.append(line)
                
            ax.set_title(f'Hydrodynamic field: {feature}')
            fig.legend(handles=legend_handles, labels=case_list, loc='upper right', bbox_to_anchor=(1.0, 1.0))
            ax.set_xlabel('$L/L_{max}$')
            ax.set_ylabel(f'{ylabels[idx]}')

        plt.show()



        
    elif choice.lower() == 'no':
        pass
        
    else:
        print("Invalid choice. Please enter 'yes' or 'no'.")

else:
    pass



