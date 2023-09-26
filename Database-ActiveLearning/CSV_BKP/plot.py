##########################################################################
#### Run listing and early visualization
#### Author : Juan Pablo Valdes
##########################################################################
import pandas as pd

case = 'sp_geom'

# Read backup csv with post-process data and DOE table from pkl file
df = pd.read_csv(f'old_csv/{case}_1.csv')
df_DOE = pd.read_pickle(f'../DOE/old_DOE/LHS_{case}_1.pkl')
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

# Plot segment for single-phase cases

if case == 'sp_geom':

    choice = input("plot hydrodynamics? (y/n): ")

    if choice.lower() == 'y' or choice.lower() == 'yes':

        df_updated.index = [f'run_sp_{i+1}' for i in df_updated.index]
        
        num_cases = input('List all case numbers you want to plot separated by spaces: ')
        numbers = num_cases.split()

        if not num_cases.replace(' ','').isdigit():
            raise ValueError('Non-numeric value entered as input. Re-check input values.')

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
        cases_plotted = []
        Re_plotted = []

        for jdx, case in enumerate(case_list):
        #for case, jdx in zip(case_list, range(len(case_list))):

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

        # Combining case and Re list to create legend label as a tuple with idx position
        legend_list = [(idx, case + ': Re = {:.2f}'.format(Re)) for idx, (case, Re) in enumerate(zip(cases_plotted,Re_plotted))]

        # Sorting legend list by Re
        sorted_legend = sorted(legend_list, key=lambda x: float(x[1].split('= ')[-1]))

        # Sorting legend_handles object by idx sorted above through Re
        legend_handles_sorted = sorted(zip(list(zip(*sorted_legend))[0],legend_handles), key = lambda x: x[0])
        
        fig.legend(handles=list(zip(*legend_handles_sorted))[1], labels=list(zip(*sorted_legend))[1], loc='upper right', bbox_to_anchor=(1.0, 1.0))
        #fig.legend(handles=legend_handles, labels=legend_list, loc='upper right', bbox_to_anchor=(1.0, 1.0))
        plt.show()


    elif choice.lower() == 'n':
        pass
        
    else:
        print("Invalid choice. Please enter 'yes' or 'no'.")

else:
    pass



