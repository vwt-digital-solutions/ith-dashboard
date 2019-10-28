#%%
import pandas as pd 
import numpy as np

#%% reading test data
df_inkooporder = pd.read_excel('./Data/Alle inkooporder 280.xlsx')
df_kosten = pd.read_excel('./Data/Alle kosten (zonder afgesloten projecten).xlsx')
df_codes = pd.read_excel('./Data/Codes Geul.xlsx')
df_organize = pd.read_excel('./Data/Excel Organize.xlsx')
df_wff = pd.read_excel('./Data/WFM Financieel.xlsx')
df_wfp = pd.read_excel('./Data/WFM Projecten 2.0.xlsx')
df_wfe = pd.read_excel('./Data/Workflow Excel.xlsx')

df_inkooporder.to_pickle('inkooporders')
df_kosten.to_pickle('kosten')
df_codes.to_pickle('codes')
df_organize.to_pickle('organize')
df_wff.to_pickle('wff')
df_wfp.to_pickle('wfp')
df_wfe.to_pickle('wfe')



#%%
