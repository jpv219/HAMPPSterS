import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def clean_csv(df,columns):

    for column in columns:
        df[column] = df[column].str.replace('[','').str.replace(']','').str.split(' ')
        df[column] = df[column].apply(lambda x: [i for i in x if i != ''])
        df[column] = df[column].apply(lambda x: np.array([float(i) for i in x]))
    return df