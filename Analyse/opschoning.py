# %%
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()



def get_data(): 

    path = 'C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/Data'
    #%% inlezen bestanden:
    # Inkooporders 
    df_inkooporder = pd.read_pickle(
        path + '/pickles/inkooporders')  # inkoop data uit BAAN
    # codes gerelateerd aan geul werk
    df_codes = pd.read_pickle(path + '/pickles/codes')
    # codes gerelateerd aan extra geul werk
    df_codes_ew = pd.read_excel(path + '/Codes_extrawerk.xlsx').astype('str')
    df_codes_ew.drop(index=[4, 5, 6], inplace=True)
    df_codes_ew.rename(columns={'Unnamed: 0': 'ARTIKEL'}, inplace=True)
    # workflow financiceel
    df_wff = pd.read_pickle(path + '/pickles/wff')  # facturatie data uit Workflow
    # revisie data 
    df_rev = pd.read_excel(path + '/view_bestanden_deel_eindrevisie.xlsx')
    # Relevante kolommen uit inkooporder en workflow financieel
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
    # %% Opschonen van data en controleren op correctheid

    # unieke lijst van projectcodes uit WF, dit geeft alle relevante projecten
    df_wffa['BisonNummer'] = df_wffa['BisonNummer'].fillna(
        0).astype('int64').astype('str')
    df_wffa = df_wffa[df_wffa['BisonNummer'] != '0']  # 58 projecten met code  0
    pcodes = df_wffa['BisonNummer'].unique()  # alle codes zijn uniek!

    # filteren van inkooporders op relevante projecten (pcodes)
    # len(df_ioa['PROJECT'].unique()) # 11909 unieke projectcodes!
    df_ioa = df_ioa[df_ioa['PROJECT'].isin(pcodes)]
    # no emtpy entries though!, 8700 unieke projectcodes
    df_ioa['ARTIKEL'] = df_ioa['ARTIKEL'].fillna('0')

    # vervolgens op codes geulen (aangeleverd door Arend), 
    # codes voor meerwerk voorbij erf toegevoegd geul, 
    # deze moeten later gecrosscheckt worden op aanwezigheid DP inkooporder, 
    # dan namelijk weer eruit (dubbel betalen)!
    df_ioa_t = pd.DataFrame()
    acodes = df_codes['Tabblad codes VE BIS'].to_list(
    ) + df_codes_ew['Code'].iloc[0:4].astype('str').to_list()
    for i in acodes:
        mask = df_ioa['ARTIKEL'].str.contains(i)  # ombouwen naar afgeleid artikel
        # 5251 unieke project codes!
        df_ioa_t = pd.concat([df_ioa_t, df_ioa[mask]], axis=0)

    codes_extra = pd.read_excel(path + '/Artikelen_toegevoegd_A.xlsx', 'Blad2')

    # %% extra codes meenemen of niet? --> geeft groot verschil met dashboard Arend als wel meegenomen
    codes_extra = pd.concat([codes_extra['ARTIKEL'], df_codes_ew['ARTIKEL'].iloc[4:].astype(
        'str')], axis=0, ignore_index=True)  # zorgt voor grotere delta tov Arends dashboard...
    # codes_extra = df_codes_ew['ARTIKEL'].iloc[4:].astype('str')

    # extra filter op extra codes die te maken hebben met geulen (gecheckt door Arend) & DP ook toegevoegd
    for i in acodes:  # just to be safe, dubbel check extra filter
        mask = codes_extra.str.contains(i)  # ombouwen naar afgeleid artikel
        codes_extra = codes_extra[~mask]
    df_ioa_t3 = df_ioa[df_ioa['ARTIKEL'].isin(codes_extra)]
    # 5251 unieke projectcodes!
    df_ioa_t = pd.concat([df_ioa_t, df_ioa_t3], axis=0)

    # uiteindelijk inkooporder analyse dataframe
    df_ioa = df_ioa_t

    # aantal gefactureerde meters per project:
    df_wffa['Gefactureerd Totaal'] = df_wffa['Extra werk geregistreerd - Geul graven binnen plan (meters)'] + \
        df_wffa['Extra werk geregistreerd - Geul graven buiten plan (meters)'] + \
        df_wffa['Te factureren - Geul graven binnen plan (meters)'] + \
        df_wffa['Te factureren - Geul graven buiten plan (meters)'] + \
        df_wffa['Vrijgegeven - Geul Graven Binnen Plan (meters)'] + \
        df_wffa['Vrijgegeven - Geul graven buiten plan (meters)'] + \
        df_wffa['Gefactureerd - Geul graven binnen plan (meters)'] + \
        df_wffa['Gefactureerd - Geul graven buiten plan (meters)'] + \
        df_wffa['Openstaand - Geul graven binnen plan (meters)'] + \
        df_wffa['Openstaand - Geul graven buiten plan (meters)']

    df_wffa['Ingeschat'] = df_wffa['Goedgekeurd – Geul graven Binnen Plan (Meters)'] + \
        df_wffa['Goedgekeurd – Geul graven Buiten Plan (Meters)']  # 10296 projecten, uniek!

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

    # klaarmaken van data info over facturatie projecten uit overzicht TPG en toevoegen aan wffa

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
    # opnieuw ffill om de NAN van de 200000 eruit te halen
    revisie.fillna(method='ffill', inplace=True)

    ## Inkoop basis frame (Met DP erin!!)
    inkoop = df_ioa
    inkoop['LEVERDATUM_ONTVANGST'] = pd.to_datetime(inkoop['LEVERDATUM_ONTVANGST'])
    inkoop = inkoop[inkoop['LEVERDATUM_ONTVANGST'].notna()] # delete empty dates (gebeurt alleen als er ook niks is ontvangen)
    inkoop.set_index('LEVERDATUM_ONTVANGST', inplace=True)
    inkoop.sort_index(inplace=True)
    # inkoop = inkoop[~inkoop['ARTIKEL'].isin(df_codes_ew['ARTIKEL'].iloc[4:].astype('str').to_list())]

    ## workflow basis frame 
    workflow = df_wffa

    ##########################################################################################################
    # Aanvullen van workflow met inkoop
    inkoop_zonder_DP = inkoop[~inkoop['ARTIKEL'].isin(df_codes_ew['ARTIKEL'].iloc[4:].astype('str').to_list())]
    inkoop_zonder_DP = inkoop_zonder_DP.groupby('PROJECT').agg({'Ontvangen':'sum'})
    workflow = workflow.merge(inkoop_zonder_DP, left_on='BisonNummer', right_on='PROJECT', how = 'left').fillna(0)

    # Aanvulen van workflow met revisie en delta1
    revisie_temp = revisie.iloc[-1] 
    workflow = workflow.merge(revisie_temp, left_on='BisonNummer', right_on='Projectnummer', how='left') # klopt het dat er veel artikel codes wel in revisie staan, maar niet in workflow???
    workflow.columns = ['Project', 'Gefactureerd totaal', 'Ingeschat', 'Ingekocht', 'Revisie totaal']
    workflow = workflow.fillna(0)
    workflow['delta_1']=workflow['Gefactureerd totaal'] - workflow['Ingekocht']

    # Revisie aanvullen met 'lege projecten'
    temp_projecten = set(workflow['Project'].unique()) - set(revisie.columns)
    temp = pd.DataFrame(index=revisie.index,columns=list(temp_projecten)).fillna(0)
    revisie = pd.concat([revisie,temp],axis=1)

    return workflow, inkoop, revisie 

def categorize(workflow): 
    '''
    In deze functie wordt de OHW bepaald en daarna verdeeld over verschillende categoriën. 
    Als input worden alle projecten die in Workflow staan meegenomen. 
    Als ouput het dataframe met Projectnummer en categorie en het aantal meters
    '''
    
    df_OHW = workflow[workflow['delta_1'] < 0]
    df_OHW['delta_it']= df_OHW['Ingekocht'] - df_OHW['Gefactureerd totaal']
    df_OHW['detla_ir']= df_OHW['Ingekocht'] - df_OHW['Revisie totaal']
    df_OHW['delta_tr']= df_OHW['Gefactureerd totaal'] - df_OHW['Revisie totaal']
    df_OHW['delta_ii']= df_OHW['Ingekocht'] - df_OHW['Ingeschat']

    df_OHW = df_OHW.fillna(0)

    # verschillende bakken:
    # bak 1 meer ingekocht dan gefactureerd & (deel revisie gefactureerd klopt niet met totaal gefactureerd) (Mark Beunk trapt op de rem):
    # niets gefactureerd en ook geen deelrevisies...fout bij invoer TPG?
    df_OHW.at[((df_OHW['Gefactureerd totaal']== 0) & (df_OHW['delta_tr'] == 0)), 'Categorie'] = 'Cat1' 
    
    # niets gefactureerd maar wel een deelrevisie, inkoop meer dan ingeschat...niet doorgezet WF of Mark Beunk rem?
    df_OHW.at[(df_OHW['Gefactureerd totaal'] == 0) & (df_OHW['delta_tr'] != 0) & (df_OHW['delta_ii'] > 0), 'Categorie'] = 'Cat2a'
    
    # niets gefactureerd maar wel een deelrevisie, inkoop minder dan ingeschat...niet doorgezet WF of Mark Beunk rem?
    df_OHW.at[(df_OHW['Gefactureerd totaal'] == 0) & (df_OHW['delta_tr'] != 0) & (df_OHW['delta_ii'] <= 0), 'Categorie'] = 'Cat2b'
   
    # wel gefactureerd en ook gelijk aan deelrevisies...doorvoer naar WF klopt maar te weinig? aannemer, TPG handmatig fout excel
    df_OHW.at[(df_OHW['Gefactureerd totaal'] != 0) & (df_OHW['delta_tr'] == 0), 'Categorie'] = 'Cat3'
    
    # wel gefactureerd maar deels geremd door Mark Beunk? inkoop meer dan ingeschat, dit is te checken kolom gerealiseerd...
    df_OHW.at[(df_OHW['Gefactureerd totaal'] != 0) & (df_OHW['delta_tr'] < 0) & (df_OHW['delta_ii'] > 0), 'Categorie'] = 'Cat4a'

    # wel gefactureerd maar deels geremd door Mark Beunk? inkoop minder dan ingeschat, dit is te checken kolom gerealiseerd...
    df_OHW.at[(df_OHW['Gefactureerd totaal'] != 0) & (df_OHW['delta_tr'] < 0) & (df_OHW['delta_ii'] <= 0), 'Categorie']= 'Cat4b'
    
    # wel gefactureerd en meer dan deelrevisies? dit mag niet kunnen...fout in workflow of TPG?
    df_OHW.at[(df_OHW['Gefactureerd totaal']!= 0) & (df_OHW['delta_tr'] > 0), 'Categorie']= 'Cat5'

    df_OHW = df_OHW.fillna(0)

    return df_OHW

def get_extra_werk(inkoop, df_OHW):


    # inlezen extra werk codes en DP codes
    path = 'C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/Data'
    df_codes_ew = pd.read_excel(path + '/Codes_extrawerk.xlsx').astype('str')
    df_codes_ew.drop(index=[4, 5, 6], inplace=True)
    df_codes_ew.rename(columns={'Unnamed: 0': 'ARTIKEL'}, inplace=True)

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

    # filter alle extra werk en dp codes 
    alle_codes = inkoop[((inkoop['Extra_werk']==1) | (inkoop['DP_code'] ==1))]
    # Eerst groeperen op inkooporder, daarna op project 
    alle_codes = alle_codes.groupby(['INKOOPORDER','PROJECT']).agg({'Extra_werk':'sum','DP_code':'sum','Ontvangen':'sum'})
    # Als er een code extra werk op een inkooporder aanwezig is, en er staat geen DP_code op de inkooporder, dan is het extra werk 
    extra_werk = alle_codes[(alle_codes['Extra_werk']>0) & (alle_codes['DP_code']==0)]
    extra_werk_m = sum(extra_werk['Ontvangen'])

    temp = extra_werk.copy()
    temp = temp.groupby('PROJECT').agg({'Ontvangen':'sum'}).rename(columns={'Ontvangen':'Meerwerk'})
    df_OHW = df_OHW.merge(temp, left_on='Project', right_on='PROJECT', how='left')
    df_OHW = df_OHW.fillna(0)

    return alle_codes, extra_werk, extra_werk_m, df_OHW

