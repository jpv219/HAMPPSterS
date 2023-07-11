# Loading, Cleaning Volume-Gamma-Nd dataframes
import numpy as np
import pandas as pd
import Clean_CSV

def extract_GVol(elem):
    csv_file = 'RawData/' + elem + '_GVol.csv'
    df = pd.read_csv(csv_file)
    df = Clean_CSV.clean_csv(df,list(df.columns.values)[1:3])
    return df

def extract_Nd(elem):
    Nd_csv_file = 'RawData/Nd/' + elem + '_dnum_corr.csv'
    df = pd.read_csv(Nd_csv_file)
    label_list = list(df.columns.values)
    df.rename(columns={label_list[0]: 'Ndrops'}, inplace = True)
    df['Time'] = df.apply(lambda row: row.name*0.005,axis=1)
    df = df[['Time','Ndrops']]
    return df

def extract_Vol(elem):
    csv_file = 'RawData/' + elem + '_Vol.csv'
    df = pd.read_csv(csv_file)
    df = Clean_CSV.clean_csv(df,list(df.columns.values)[1:2])
    return df



