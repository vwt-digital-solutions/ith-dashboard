# %%
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()

def get_extra_werk():
    
    path = 'C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/Data'
    
    # Geul codes ophalen
    df_codes = pd.read_pickle(path + '/pickles/codes')
    geul_codes = df_codes[['Tabblad codes VE BIS', 'Soort code']].\
        rename(columns={'Tabblad codes VE BIS':'Codes','Soort code':'omschrijving'})
    codes_extra = pd.read_excel(path + '/Artikelen_toegevoegd_A.xlsx', 'Blad2')
    codes_extra = codes_extra[['ARTIKEL','ARTIKEL_OMSCHRIJVING']].\
        rename(columns={'ARTIKEL':'Codes', 'ARTIKEL_OMSCHRIJVING':'omschrijving'})
    geul_codes = geul_codes.append(codes_extra, sort=True) 
    # inlezen extra werk codes en DP codes
    df_codes_ew = pd.read_excel(path + '/Codes_extrawerk.xlsx').astype('str')
    df_codes_ew.drop(index=[4, 5, 6], inplace=True)
    df_codes_ew.rename(columns={'Unnamed: 0': 'ARTIKEL'}, inplace=True)
    # inlezen alle inkoop orders 
    inkoop = pd.read_pickle(path + '/pickles/inkooporders')
    inkoop = inkoop[['INKOOPORDER', 'POSITIE', 'LEVERDATUM', 'INKOPER', 'PROJECT', 'ARTIKEL', 'ARTIKEL_OMSCHRIJVING',
                            'LEVERDATUM_ONTVANGST', 'STATUS', 'HOEVEELHEID_PAKBON', 'PRIJS', 'TOTAALPRIJS', 'Ontvangen']]  # artikel linkt naar codes geul

    # Bepaal of iedere regel een 'extra werk' code bevat
    for i in df_codes_ew.iloc[:4]['Code']:
        mask = inkoop['ARTIKEL'].str.contains(i)
        inkoop.at[mask, 'Extra_werk'] = 1
    inkoop['Extra_werk'] = inkoop['Extra_werk'].fillna(0)

    # Bepaal of iedere regel een 'DP_code' bevat
    for i in df_codes_ew.iloc[4:]['Code']:
        mask = inkoop['ARTIKEL'].str.contains(i)
        inkoop.at[mask, 'DP_code'] = 1
    inkoop['DP_code'] = inkoop['DP_code'].fillna(0)

    # Bepaal of iedere regel een 'Geul code' bevat
    for i in geul_codes['Codes']:
        mask = inkoop['ARTIKEL'].str.contains(i)
        inkoop.at[mask, 'Geul'] = 1
    inkoop['Geul'] = inkoop['Geul'].fillna(0)
    
    # Haal alles eruit wat dus geen Geul, DP of extra werk code is
    inkoop = inkoop[~((inkoop['Geul']==0) & (inkoop['DP_code']==0) & (inkoop['Extra_werk']==0))]
    
    # Eerst groeperen op inkooporder, daarna op project 
    inkooporders = inkoop.groupby(['INKOOPORDER']).agg({'PROJECT':'count', 'Extra_werk':'sum','DP_code':'sum','Geul':'sum','Ontvangen':'sum'})
    # Als er een code extra werk op een inkooporder aanwezig is, en er staat geen DP_code op de inkooporder, dan is het extra werk 
    inkooporders_ew = inkooporders[(inkooporders['Extra_werk']>0) & (inkooporders['DP_code']==0) & (inkooporders['Geul']>1)]
    inkooporders_ew = list(inkooporders_ew.index) # 135 orders met extra werk

    mask = ((inkoop['INKOOPORDER'].isin(inkooporders_ew)) & (inkoop['Geul']==1))
    inkoop_relevant = inkoop[mask]

    extra_werk_inkooporder = inkoop_relevant.groupby('INKOOPORDER').agg({'Ontvangen':'sum'})
    extra_werk_project = inkoop_relevant.groupby('PROJECT').agg({'Ontvangen':'sum'})


    return extra_werk_inkooporder, extra_werk_project 

def get_data(extra_werk_project): 

    #%% inlezen bestanden:
    path = 'C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/Data'
    # Inkooporders 
    df_inkooporder = pd.read_pickle(
        path + '/pickles/inkooporders')  # inkoop data uit BAAN
    # workflow financiceel
    df_wff = pd.read_pickle(path + '/pickles/wff')  # facturatie data uit Workflow
    # revisie data 
    df_rev = pd.read_excel(path + '/view_bestanden_deel_eindrevisie.xlsx')
    # codes gerelateerd aan geul werk
    df_codes = pd.read_pickle(path + '/pickles/codes')
    geul_codes = df_codes[['Tabblad codes VE BIS', 'Soort code']].\
        rename(columns={'Tabblad codes VE BIS':'Codes','Soort code':'omschrijving'})
    codes_extra = pd.read_excel(path + '/Artikelen_toegevoegd_A.xlsx', 'Blad2')
    codes_extra = codes_extra[['ARTIKEL','ARTIKEL_OMSCHRIJVING']].\
        rename(columns={'ARTIKEL':'Codes', 'ARTIKEL_OMSCHRIJVING':'omschrijving'})
    geul_codes = geul_codes.append(codes_extra, sort=True) 
    geul_codes
    # dit zijn alle codes geul, exclusief extra werk


    #%% Relevante kolommen uit inkooporder, workflow en revisie 
    df_ioa = df_inkooporder[['INKOOPORDER', 'LEVERDATUM', 'INKOPER', 'PROJECT', 'ARTIKEL', 'ARTIKEL_OMSCHRIJVING',
                            'LEVERDATUM_ONTVANGST', 'STATUS', 'HOEVEELHEID_PAKBON', 'PRIJS', 'TOTAALPRIJS', 'Ontvangen']]  # artikel linkt naar codes geul
    df_wffa = df_wff[['BisonNummer',
                    'Aangeboden – Geul graven Binnen Plan (Meters)',
                    'Aangeboden – Geul graven Buiten Plan (Meters)',
                    'Goedgekeurd – Geul graven Binnen Plan (Meters)',
                    'Goedgekeurd – Geul graven Buiten Plan (Meters)',
                    'Afgehecht - Geul graven binnen plan (meters)',
                    'Afgehecht - Geul graven buiten plan (meters)',
                    'Extra werk geregistreerd - Geul graven binnen plan (meters)',
                    'Extra werk geregistreerd - Geul graven buiten plan (meters)',
                    'Extra werk geaccordeerd - Geul graven binnen plan (meters)',
                    'Extra werk geaccordeerd - Geul graven buiten plan (meters)',
                    'Aantal buiten norm - Geul graven binnen plan (meters)',
                    'Aantal buiten norm - Geul graven buiten plan (meters)',
                    'Te factureren - Geul graven binnen plan (meters)',
                    'Te factureren - Geul graven buiten plan (meters)',
                    'Vrijgegeven - Geul Graven Binnen Plan (meters)',
                    'Vrijgegeven - Geul graven buiten plan (meters)',
                    'Pro Forma - Geul graven binnen plan (meters)',
                    'Pro Forma - Geul graven buiten plan (meters)',
                    'Gefactureerd - Geul graven binnen plan (meters)',
                    'Gefactureerd - Geul graven buiten plan (meters)',
                    'Openstaand - Geul graven binnen plan (meters)',
                    'Openstaand - Geul graven buiten plan (meters)']]  # BisonNummer == Projectcode
    df_rev = df_rev[['Type', 'Datum', 'Projectnummer', 'Totale geullengte']]
    

    #% Opschonen van data en controleren op correctheid
    # unieke lijst van projectcodes uit WF, dit geeft alle relevante projecten
    df_wffa['BisonNummer'] = df_wffa['BisonNummer'].fillna(0).astype('int64').astype('str')
    df_wffa = df_wffa[df_wffa['BisonNummer'] != '0']  # 58 projecten met code  0
    pcodes = df_wffa['BisonNummer'].unique()  # alle codes zijn uniek!

    # filteren van inkooporders op relevante projecten (pcodes)
    df_ioa = df_ioa[df_ioa['PROJECT'].isin(pcodes)]

    # filter van inkooporder op relevante artikel codes
    df_ioa['ARTIKEL'] = df_ioa['ARTIKEL'].fillna('0')
    df_ioa_t = pd.DataFrame([])
    for i in geul_codes['Codes'].to_list():
        mask = df_ioa['ARTIKEL'].str.contains(i)  # ombouwen naar afgeleid artikel
        df_ioa_t = pd.concat([df_ioa_t, df_ioa[mask]], axis=0)
    # uiteindelijk inkooporder analyse dataframe ZONDER DP EN EXTRA WERK CODES
    df_ioa = df_ioa_t

    #%% aantal gefactureerde meters per project:
    df_wffa['Gefactureerd Totaal'] = df_wffa['Te factureren - Geul graven binnen plan (meters)'] + \
        df_wffa['Te factureren - Geul graven buiten plan (meters)'] + \
        df_wffa['Vrijgegeven - Geul Graven Binnen Plan (meters)'] + \
        df_wffa['Vrijgegeven - Geul graven buiten plan (meters)'] + \
        df_wffa['Gefactureerd - Geul graven binnen plan (meters)'] + \
        df_wffa['Gefactureerd - Geul graven buiten plan (meters)'] + \
        df_wffa['Openstaand - Geul graven binnen plan (meters)'] + \
        df_wffa['Openstaand - Geul graven buiten plan (meters)'] +\
        df_wffa['Pro Forma - Geul graven binnen plan (meters)'] + \
        df_wffa['Pro Forma - Geul graven buiten plan (meters)'] +\
        df_wffa['Afgehecht - Geul graven binnen plan (meters)'] + \
        df_wffa['Afgehecht - Geul graven buiten plan (meters)']

    df_wffa['Goedgekeurd'] = df_wffa['Goedgekeurd – Geul graven Binnen Plan (Meters)'] + \
        df_wffa['Goedgekeurd – Geul graven Buiten Plan (Meters)'] + \
        df_wffa['Extra werk geaccordeerd - Geul graven binnen plan (meters)'] +\
        df_wffa['Extra werk geaccordeerd - Geul graven buiten plan (meters)'] +\
        df_wffa['Afgehecht - Geul graven binnen plan (meters)'] + \
        df_wffa['Afgehecht - Geul graven buiten plan (meters)']
    
    df_wffa['Afgehecht'] = df_wffa['Afgehecht - Geul graven binnen plan (meters)']+\
        df_wffa['Afgehecht - Geul graven buiten plan (meters)']
    
    df_wffa['Aangeboden'] = df_wffa['Aangeboden – Geul graven Binnen Plan (Meters)']+\
        df_wffa['Aangeboden – Geul graven Buiten Plan (Meters)']
    
    df_wffa['Goedgekeurd'] = df_wffa['Goedgekeurd – Geul graven Binnen Plan (Meters)']+\
        df_wffa['Goedgekeurd – Geul graven Buiten Plan (Meters)']
             
    df_wffa.drop(columns=[
        'Aangeboden – Geul graven Binnen Plan (Meters)',
        'Aangeboden – Geul graven Buiten Plan (Meters)',
        'Goedgekeurd – Geul graven Binnen Plan (Meters)',
        'Goedgekeurd – Geul graven Buiten Plan (Meters)',
        'Afgehecht - Geul graven binnen plan (meters)',
        'Afgehecht - Geul graven buiten plan (meters)',
        'Extra werk geregistreerd - Geul graven binnen plan (meters)',
        'Extra werk geregistreerd - Geul graven buiten plan (meters)',
        'Extra werk geaccordeerd - Geul graven binnen plan (meters)',
        'Extra werk geaccordeerd - Geul graven buiten plan (meters)',
        'Aantal buiten norm - Geul graven binnen plan (meters)',
        'Aantal buiten norm - Geul graven buiten plan (meters)',
        'Te factureren - Geul graven binnen plan (meters)',
        'Te factureren - Geul graven buiten plan (meters)',
        'Vrijgegeven - Geul Graven Binnen Plan (meters)',
        'Vrijgegeven - Geul graven buiten plan (meters)',
        'Pro Forma - Geul graven binnen plan (meters)',
        'Pro Forma - Geul graven buiten plan (meters)',
        'Gefactureerd - Geul graven binnen plan (meters)',
        'Gefactureerd - Geul graven buiten plan (meters)',
        'Openstaand - Geul graven binnen plan (meters)',
        'Openstaand - Geul graven buiten plan (meters)'], inplace=True)

    # Deze hebben we nog niet... 
    # df_wffa['Revisie'] =   df_wffa['Gerealiseerd - Geul graven binnen plan (meters)'] + \
    #                             df_wffa['Gerealiseerd - Geul graven buiten plan (meters)']

    #%% Klaar zetten van de DATAFRAMES voor het DASHBOARD
    ## Revisie basis frame 
    revisie = df_rev
    revisie = revisie[(~revisie['Projectnummer'].isna()) & (
        ~revisie['Totale geullengte'].isna()) & (revisie['Projectnummer'] != '-')]
    revisie['Projectnummer'] = revisie['Projectnummer'].astype('str')
    revisie['Datum'] = pd.to_datetime(revisie['Datum'])
    revisie['Datum'] = revisie['Datum'].dt.strftime('%Y-%m-%d')
    revisie['Datum'] = pd.to_datetime(revisie['Datum'])
    revisie = revisie.pivot_table(
        index='Datum', 
        columns='Projectnummer', 
        values='Totale geullengte').fillna(method='ffill')
    revisie = revisie.fillna(0)
    revisie = revisie[~(revisie > 200000)]
    revisie.fillna(method='ffill', inplace=True) # opnieuw ffill om de NAN van de 200000 eruit te halen

    ## Inkoop basis frame (ZONDER DP en extra werk Codes)
    inkoop = df_ioa
    inkoop['LEVERDATUM_ONTVANGST'] = pd.to_datetime(inkoop['LEVERDATUM_ONTVANGST'])
    inkoop = inkoop[inkoop['LEVERDATUM_ONTVANGST'].notna()] # delete empty dates (gebeurt alleen als er ook niks is ontvangen)
    inkoop.set_index('LEVERDATUM_ONTVANGST', inplace=True)
    inkoop.sort_index(inplace=True)

    ## workflow basis frame 
    workflow = df_wffa

    # Aanvullen van workflow met inkoop
    inkoop_per_project = inkoop.groupby('PROJECT').agg({'Ontvangen':'sum'})
    workflow = workflow.merge(inkoop_per_project, left_on='BisonNummer', right_on='PROJECT', how = 'left').fillna(0)

    # Aanvulen van workflow met revisie en delta1
    revisie_temp = pd.DataFrame(revisie.iloc[-1])
    revisie_temp.columns = ['Revisie totaal']
    workflow = workflow.merge(revisie_temp, left_on='BisonNummer', right_on='Projectnummer', how='left') # klopt het dat er veel artikel codes wel in revisie staan, maar niet in workflow???
    workflow.rename(columns={'BisonNummer':'Project', 'Gefactureerd Totaal':'Gefactureerd totaal','Ontvangen':'Ingekocht'}, inplace=True)
    workflow = workflow.fillna(0)
    workflow['delta_1']= workflow['Gefactureerd totaal'] - workflow['Ingekocht']

    workflow = workflow.merge(extra_werk_project, left_on='Project', right_on='PROJECT', how='left')
    workflow.rename(columns={'Ontvangen':'Extra werk'}, inplace=True)
    workflow = workflow.fillna(0)

    # Revisie aanvullen met 'lege projecten'
    temp_projecten = set(workflow['Project'].unique()) - set(revisie.columns)
    temp = pd.DataFrame(index=revisie.index,columns=list(temp_projecten)).fillna(0)
    revisie = pd.concat([revisie,temp],axis=1)

    # AREND: Alle projecten waar Aangeboden op 0 staat, eruit halen. 
    workflow = workflow[workflow['Aangeboden']!=0]

    return workflow, inkoop, revisie 

def categorize(workflow): 
    '''
    In deze functie wordt de OHW bepaald en daarna verdeeld over verschillende categoriën. 
    Als input worden alle projecten die in Workflow staan meegenomen. 
    Als ouput het dataframe met Projectnummer en categorie en het aantal meters
    '''
    
    path = 'C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/Data'

    # Analyse waar de revisie data een 'daling' weergeeft.
    df_rev = pd.read_excel(path + '/view_bestanden_deel_eindrevisie.xlsx')
    df_rev = df_rev[['Type', 'Datum', 'Projectnummer', 'Totale geullengte']]
    revisie = df_rev
    revisie = revisie[(~revisie['Projectnummer'].isna()) &\
        (~revisie['Totale geullengte'].isna()) &\
        (revisie['Projectnummer'] != '-')]
    revisie['Projectnummer'] = revisie['Projectnummer'].astype('str')
    revisie['Datum'] = pd.to_datetime(revisie['Datum'])
    revisie['Datum'] = revisie['Datum'].dt.strftime('%Y-%m-%d')
    revisie['Datum'] = pd.to_datetime(revisie['Datum'])
    revisie.sort_values('Datum', inplace=True)

    projectnummers_revisie = list(revisie['Projectnummer'].unique())
    
    negatieve_revisie = []
    for project in projectnummers_revisie:
        temp = revisie[revisie['Projectnummer']==project]
        temp = list(temp['Totale geullengte'])
        temp = [j-i for i, j in zip(temp[:-1], temp[1:])]
        temp = any(i<0 for i in temp)
        negatieve_revisie.append(temp)
    foutieve_revisie = pd.DataFrame({'Project':projectnummers_revisie,'Daling aanwezig':negatieve_revisie}, columns=['Project', 'Daling aanwezig'])
    foutieve_revisie = list(foutieve_revisie[foutieve_revisie['Daling aanwezig']]['Project'].unique())
    
    df_OHW = workflow[workflow['delta_1'] < 0]
    df_OHW['delta_it']= df_OHW['Ingekocht'] - df_OHW['Gefactureerd totaal']
    df_OHW['delta_ir']= df_OHW['Ingekocht'] - df_OHW['Revisie totaal']
    df_OHW['delta_tr']= df_OHW['Gefactureerd totaal'] - df_OHW['Revisie totaal']
    df_OHW['delta_ii']= df_OHW['Ingekocht'] - df_OHW['Goedgekeurd']
    
    df_OHW['Categorie']=''
    # Categorie 'Foutieve' revisie data
    df_OHW.at[df_OHW['Project'].isin(foutieve_revisie), 'Categorie'] = 'Cat1'
    # Categorie 'Vertraging KPN' 
    mask = ((df_OHW['Categorie']=='') & (df_OHW['Aangeboden']>0) & (df_OHW['Goedgekeurd']==0))
    df_OHW.at[mask, 'Categorie'] = 'Cat2'

    # Categorie 3 --> deelrevisie > facturatie & inkoop < deelrevisie
    mask = ((df_OHW['Categorie']=='') & \
        ((df_OHW['Revisie totaal']-df_OHW['Gefactureerd totaal'])>0) & \
        ((df_OHW['Ingekocht']-df_OHW['Revisie totaal'])<=0))
    df_OHW.at[mask, 'Categorie']= 'Cat3'
    # Categorie 4 --> deelrevisie > facturatie & inkoop > deelrevisie
    mask = ((df_OHW['Categorie']=='') & \
        ((df_OHW['Revisie totaal']-df_OHW['Gefactureerd totaal'])>0) & \
        ((df_OHW['Ingekocht']-df_OHW['Revisie totaal'])>0))
    df_OHW.at[mask, 'Categorie']= 'Cat4'

    # Categorie 5 --> deelrevisie < facturatie & inkoop < deelrevisie
    mask = ((df_OHW['Categorie']=='') & \
        ((df_OHW['Revisie totaal']-df_OHW['Gefactureerd totaal'])<=0) & \
        ((df_OHW['Ingekocht']-df_OHW['Revisie totaal'])<=0))
    df_OHW.at[mask, 'Categorie']= 'Cat5'
    # Categorie 6 --> deelrevisie < facturatie & inkoop > deelrevisie
    mask = ((df_OHW['Categorie']=='') & \
        ((df_OHW['Revisie totaal']-df_OHW['Gefactureerd totaal'])<=0) & \
        ((df_OHW['Ingekocht']-df_OHW['Revisie totaal'])>0))
    df_OHW.at[mask, 'Categorie']= 'Cat6'

    df_OHW.drop(columns=['Aangeboden','delta_it','delta_ir','delta_ii','delta_tr'], inplace=True)
    workflow = workflow.merge(df_OHW[['Project', 'Categorie']], on='Project', how='left')
    workflow['Categorie'] = workflow['Categorie'].fillna('Geen OHW')

    return df_OHW, workflow 




