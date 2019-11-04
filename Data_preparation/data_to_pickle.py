#%%
import pandas as pd 
import numpy as np

#%% reading test data
path_from = 'C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/Data/Aanlevering Arend/transfer-aschonewille-REF53789/'
df_inkooporder = pd.read_excel(path_from +'Alle inkooporder 280.xlsx')
# df_kosten = pd.read_excel('./Data/Alle kosten (zonder afgesloten projecten).xlsx')
# df_codes = pd.read_excel('Codes Geul.xlsx')
# df_organize = pd.read_excel('./Data/Excel Organize.xlsx')
df_wff = pd.read_excel(path_from + 'WFM Financieel.xlsx')
# df_wfp = pd.read_excel('./Data/WFM Projecten 2.0.xlsx')
df_wfe = pd.read_excel(path_from + 'Workflow Excel.xlsx')

path_to = 'C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/Data/Aanlevering Arend/transfer-aschonewille-REF53789/'
df_inkooporder.to_pickle(path_to + 'inkooporders.pkl')
# df_kosten.to_pickle('kosten')
# df_codes.to_pickle('codes')
# df_organize.to_pickle('organize')
df_wff.to_pickle(path_to + 'wff.pkl')
# df_wfp.to_pickle('wfp')
df_wfe.to_pickle(path_to + 'wfe.pkl')
