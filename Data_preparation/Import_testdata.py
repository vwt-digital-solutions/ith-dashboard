# %%
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()

path = 'C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/Data'

# %% loading relevant snapshot data
# df_inkooporder = pd.read_excel('./Data/Alle inkooporder 280.xlsx')
# df_inkooporder.to_pickle('./Data/inkooporders')

df_inkooporder = pd.read_pickle(
    path + '/pickles/inkooporders')  # inkoop data uit BAAN
# df_kosten = pd.read_pickle('./Data/kosten')
# codes gerelateerd aan geul werk
df_codes = pd.read_pickle(path + '/pickles/codes')
# df_codes = pd.read_excel('./Data/Codes Geul_am.xlsx') # codes gerelateerd aan geul werk
# codes gerelateerd aan extra geul werk
df_codes_ew = pd.read_excel(path + '/Codes_extrawerk.xlsx').astype('str')
df_codes_ew.drop(index=[4, 5, 6], inplace=True)
df_codes_ew.rename(columns={'Unnamed: 0': 'ARTIKEL'}, inplace=True)

# df_organize = pd.read_pickle('./Data/organize')
df_wff = pd.read_pickle(path + '/pickles/wff')  # facturatie data uit Workflow
# df_wfp = pd.read_pickle('./Data/wfp')
df_wfe = pd.read_pickle(path + '/pickles/wfe')
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

# %% Totaal balans
inkoop_tot = df_inkooporder['TOTAALPRIJS'].sum()
factuur_tot = df_fac_tot = df_wfe[['Offertebedrag MPI', 'Offertebedrag BIS', 'Offertebadrag HAS', 'Offertebedrag FTU',
                                   'Offertebedrag Aanhaalroute', 'Offertebedrag Extra werk']].fillna(0).sum(axis=1).sum()  # niet zeker of dit totaal gefactureerd naar KPN is!
delta_tot = factuur_tot - inkoop_tot
print('inkoop_tot: ' + str(inkoop_tot) + ', factuur_tot: ' +
      str(factuur_tot) + ', delta_tot: ' + str(delta_tot))

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

# vervolgens op codes geulen (aangeleverd door Arend), # codes voor meerwerk voorbij erf toegevoegd geul, deze moeten later gecrosscheckt worden op aanwezigheid DP inkooporder, dan namelijk weer eruit (dubbel betalen)!
df_ioa_t = pd.DataFrame()
acodes = df_codes['Tabblad codes VE BIS'].to_list(
) + df_codes_ew['Code'].iloc[0:4].astype('str').to_list()
for i in acodes:
    mask = df_ioa['ARTIKEL'].str.contains(i)  # ombouwen naar afgeleid artikel
    # 5251 unieke project codes!
    df_ioa_t = pd.concat([df_ioa_t, df_ioa[mask]], axis=0)

# test alle juiste codes gefilterd?
df_ioa_t2 = df_ioa[~df_ioa.isin(df_ioa_t['ARTIKEL'].to_list())]
df_ioa_t2 = df_ioa_t2.drop_duplicates(subset='ARTIKEL')
# df_ioa_t2[['ARTIKEL','ARTIKEL_OMSCHRIJVING']].to_excel('./Data/Artikelen_toegevoegd.xlsx') # hier pas ik vervolgens handmatig een selectie op in Blad1
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

# df_wffa['Revisie'] =   df_wffa['Gerealiseerd - Geul graven binnen plan (meters)'] + \
#                             df_wffa['Gerealiseerd - Geul graven buiten plan (meters)']

# klaarmaken van data info over facturatie projecten uit overzicht TPG en toevoegen aan wffa
df_rev = df_rev[(~df_rev['Projectnummer'].isna()) & (
    ~df_rev['Totale geullengte'].isna()) & (df_rev['Projectnummer'] != '-')]
df_rev['Projectnummer'] = df_rev['Projectnummer'].astype('str')
df_rev['Datum'] = pd.to_datetime(df_rev['Datum'])
df_rev['Datum'] = df_rev['Datum'].dt.strftime('%Y-%m-%d')

df_wffa = df_wffa.merge(df_rev, left_on='BisonNummer',
                        right_on='Projectnummer', how='left')
df_wffa.drop(columns='Projectnummer', inplace=True)
df_wffa.rename(columns={'Totale geullengte': 'Gefactureerd Revisie',
                        'Datum': 'Datum Revisie'}, inplace=True)

# dataframe waarin ingekocht en gefactureerd gekoppeld wordt met alle artikel info erin (geul + DP), kan naar database worden weggeschreven
df_d = df_ioa.merge(df_wffa, left_on='PROJECT',
                    right_on='BisonNummer', how='left')
df_d.drop(columns='BisonNummer', inplace=True)

# %% aantal ontvangen meters sommeren per project: aantal meters ingekocht + leverdatum.
df_da = df_d
df_da = df_da[~df_da['ARTIKEL'].isin(df_codes_ew['ARTIKEL'].iloc[4:].astype(
    'str').to_list())]  # artikelen DP eruit filteren
df_da = df_da.groupby(['PROJECT', 'INKOOPORDER', 'ARTIKEL'], as_index=False).agg(
    {'LEVERDATUM_ONTVANGST': 'first', 'Gefactureerd Totaal': 'first', 'Ingeschat': 'first', 'Ontvangen': 'first'})
df_da = df_da.groupby('PROJECT', as_index=False).agg(
    {'LEVERDATUM_ONTVANGST': 'first', 'Gefactureerd Totaal': 'first', 'Ingeschat': 'first', 'Ontvangen': 'sum'})

# dubbelcheck ontbrekende projecten of inkooporders...
df_geeninkoop = df_wffa[~df_wffa['BisonNummer'].isin(df_d['PROJECT'].tolist())]
# 5925 projecten zonder inkooporders...
df_geeninkoop = df_geeninkoop[df_geeninkoop['BisonNummer'] != '0']
# df_geeninkoop = df_geeninkoop[(df_geeninkoop['Gefactureerd Totaal'] != 0) & (df_geeninkoop['Ingeschat'] != 0)] # 738 projecten zonder inkooporders...code filtering niet goed...en missen 3 maanden uit 2016 (dump daarvoor aanvragen)...vergelijken met dashboard Arend

VE = 30
mcheck = pd.DataFrame(
    columns=['type', 'Gefactureerd Totaal', 'Ingekocht', 'delta (m)', 'delta (euro)'])
mcheck['type'] = ['wffa', 'df_geul', 'df_ontbreekt', 'balans']
mcheck['Gefactureerd Totaal'] = [df_wffa['Gefactureerd Totaal'].sum(), df_da['Gefactureerd Totaal'].sum(
), df_geeninkoop['Gefactureerd Totaal'].sum(), df_da['Gefactureerd Totaal'].sum() + df_geeninkoop['Gefactureerd Totaal'].sum()]
mcheck['Ingekocht'] = [
    '-', df_da['Ontvangen'].sum(), 'ingekocht via uren end.', '-']
mcheck['delta (m)'] = [
    '-', (df_da['Gefactureerd Totaal'].sum() - df_da['Ontvangen'].sum()), 0, '-']
mcheck['delta (euro)'] = [
    '-', (df_da['Gefactureerd Totaal'].sum() - df_da['Ontvangen'].sum())*VE, 0, '-']
mcheck
# redenen voor meters die wel gefactureerd zijn in WF en geen graaf inkoopopdracht van is terug te vinden: 1) inkoop nog niet binnen of 2) op uren artikelen geschreven bijvoorbeeld (aannemer Selecta deed dit veel bijv.)
# deze meters gefactureerd zijn dus ook ingekocht maar op niet navolgbare artikel codes zoals uren...
# deze bak kunnen we dus voorlopig negeren...
# facturatie in  workflow komt direct uit TPG...

# mask = df_inkooporder['PROJECT'].isin(df_geeninkoop['BisonNummer'].to_list())
# df_inkooporder[mask]['ARTIKEL_OMSCHRIJVING'].to_excel('./Data/Artikelen_ontbrekende_projecten.xlsx') # nog meer geul gerelateerd eruit halen?
# df_wffa[df_wffa['BisonNummer'] == df_inkooporder[mask]['PROJECT'].iloc[0]]

# %% Analyse grove delta 1: gefactureerd - ingekocht
df_da['delta_1'] = df_da['Gefactureerd Totaal'] - df_da['Ontvangen']
# We zien twee effecten: 1) overfacturatie, dit kan komen omdat de inkooporder nog niet binnen is gekomen of een fout aannemer..., vormt geen probleem voor OHW en gaan we verder niet op in,
# 2) Onderfacturatie, OHW, deze delta gaan we verder opsplitsen in bakjes om verschillende oorzaken bloot te leggen.
# vraag wffa: wrm ook vrijgegeven geulen meenenemen in facturatie??
df_OHW_t = df_da[df_da['delta_1'] < 0]

# plt.rcParams.update({'font.size': 22})
FS = 25

plt.figure(0)
fig, axes = plt.subplots(2, 2, figsize=(15, 15))
axes[0, 0].hist(df_da['delta_1'], bins=25, range=(-500, 500))
# axes[0,0].hist(df_d[df_d['delta_1'] < 0]['delta_1'], bins=25, range=(-500,0)) # OHW
<<<<<<< HEAD
axes[0,0].set_xlabel('Gefactureerd - Ingekocht per project [m]')
axes[0,1].plot(-df_OHW_t['delta_1'].cumsum(),'-') # euro
axes[0,1].set_ylabel('OHW cumulatief (te factureren) [m]')
axes[0,1].set_xlabel('Projecten')
axes[1,0].plot(df_da[df_da['delta_1'] > 0]['delta_1'].cumsum(),'-') # euro
axes[1,0].set_ylabel('Overgefactureerd cumulatief [m]')
axes[1,0].set_xlabel('Projecten')
axes[1,1].plot(-df_da['delta_1'].cumsum(),'-') # euro
axes[1,1].set_ylabel('OHW - Overgefactureerd [m]')
axes[1,1].set_xlabel('Projecten')
plt.show()

plt.figure(1,figsize=(10,10))
plt.hist(df_da['delta_1'], bins=25, range=(-500,500))
# axes[0,0].hist(df_d[df_d['delta_1'] < 0]['delta_1'], bins=25, range=(-500,0)) # OHW
plt.xlabel('Gefactureerd - Ingekocht per project [m]',FontSize=FS)
plt.rc('xtick',labelsize=FS)
plt.rc('ytick',labelsize=FS)
plt.savefig('Figuur-grove-delta.png',facecolor='w')


#%% Grove delta over tijd uitsplitsen...
df_dat = df_d[df_d['PROJECT'].isin(df_OHW_t['PROJECT'])] # subdataframe met alleen projecten die vallen onder OHW
df_dat = df_dat[~df_dat['ARTIKEL'].isin(df_codes_ew['ARTIKEL'].iloc[4:].astype('str').to_list())] # artikelen DP eruit filteren
=======
axes[0, 0].set_xlabel('delta (m)')
axes[0, 1].plot(-df_OHW_t['delta_1'].cumsum(), '-')  # euro
axes[0, 1].set_ylabel('delta OHW (m)')
axes[1, 0].plot(df_da[df_da['delta_1'] > 0]['delta_1'].cumsum(), '-')  # euro
axes[1, 0].set_ylabel('delta overfacturatie (m)')
axes[1, 1].plot(-df_da['delta_1'].cumsum(), '-')  # euro
axes[1, 1].set_ylabel('delta netto (m)')
plt.show()

# %% Grove delta over tijd uitsplitsen...
# subdataframe met alleen projecten die vallen onder OHW
df_dat = df_d[df_d['PROJECT'].isin(df_OHW_t['PROJECT'])]
df_dat = df_dat[~df_dat['ARTIKEL'].isin(df_codes_ew['ARTIKEL'].iloc[4:].astype(
    'str').to_list())]  # artikelen DP eruit filteren
>>>>>>> beb5f1ac7bdcfeffa9b26fdd75c6f1bcc92a518b

df_dati = df_dat.groupby(['PROJECT', 'INKOOPORDER', 'ARTIKEL'], as_index=False).agg(
    {'LEVERDATUM_ONTVANGST': 'first', 'Ontvangen': 'first'})
df_dati = df_dati.groupby(['LEVERDATUM_ONTVANGST'], as_index=False).agg(
    {'Ontvangen': 'sum'}).sort_values(by=['LEVERDATUM_ONTVANGST'], ascending=True)
df_dati = df_dati[~df_dati['LEVERDATUM_ONTVANGST'].isna()]

df_datf_t = df_dat.groupby(['Datum Revisie', 'PROJECT'], as_index=False).agg(
    {'Gefactureerd Revisie': 'first'}).sort_values(by=['Datum Revisie'], ascending=True)
list_rev_date = df_datf_t.pivot(index='Datum Revisie', columns='PROJECT', values='Gefactureerd Revisie').fillna(
    method='ffill').fillna(0).reset_index().drop(columns='Datum Revisie')
# filter out extreme values in revisions...errors from TPG..
list_rev_date = list_rev_date[~(list_rev_date > 200000)]
list_cumsum_rev_date = list_rev_date.sum(axis=1)
df_datf = pd.DataFrame(columns=['Datum Revisie', 'Gefactureerd Revisie'])
df_datf['Datum Revisie'] = df_datf_t['Datum Revisie'].unique()
df_datf['Gefactureerd Revisie'] = list_cumsum_rev_date

fac_tot = df_dat.groupby('PROJECT').agg({'Gefactureerd Totaal': 'first'}).sum()

df_datf['Datum Revisie'] = pd.to_datetime(df_datf['Datum Revisie'])
df_datf.set_index('Datum Revisie', inplace=True)

df_dati['LEVERDATUM_ONTVANGST'] = pd.to_datetime(
    df_dati['LEVERDATUM_ONTVANGST'])
df_dati.set_index('LEVERDATUM_ONTVANGST', inplace=True)

ingekocht = df_dati['Ontvangen'].cumsum().asfreq('D', 'ffill')
gefactureerd = df_datf['Gefactureerd Revisie'].asfreq('D', 'ffill')
delta_1_t = gefactureerd[ingekocht.index[0]:ingekocht.index[-1]] - ingekocht

<<<<<<< HEAD
fig, axes = plt.subplots(2,figsize=(20,15))
h1, = axes[0].plot(ingekocht,'-')
h2, = axes[0].plot(gefactureerd,'-') # zou al een cumsum moeten zijn!
h3, = axes[0].plot([df_datf.index[-1]], [fac_tot],'o')
axes[0].set_xlabel('Time (d)', FontSize=FS)
axes[0].set_ylabel('Totaal over projecten per dag (m)', FontSize=FS)
axes[0].legend([h1,h2,h3],['Ingekocht','Gefactureerd (op basis van deelrevisies)','Gefactureerd Totaal (op basis van Workflow)'],loc='upper left')
axes[1].plot(-delta_1_t,'-') # zou al een cumsum moeten zijn!
axes[1].set_xlabel('Time (d)', FontSize=FS)
axes[1].set_ylabel('OHW over projecten per dag (m)', FontSize=FS)
plt.rc('xtick',labelsize=FS)
plt.rc('ytick',labelsize=FS)
plt.rc('legend',fontsize=FS)
plt.savefig('Figuur-tijdserie-OHW.png',facecolor='w')
=======
fig, axes = plt.subplots(2, figsize=(10, 10))
h1, = axes[0].plot(ingekocht, '-')
h2, = axes[0].plot(gefactureerd, '-')  # zou al een cumsum moeten zijn!
h3, = axes[0].plot([df_datf.index[-1]], [fac_tot], 'o')
axes[0].set_xlabel('Time (d)')
axes[0].set_ylabel('(m)')
axes[0].legend([h1, h2, h3], ['Ingekocht', 'Gefactureerd (deelrevisie)',
                              'Gefactureerd (totaal)'], loc='upper left')
axes[1].plot(-delta_1_t, '-')  # zou al een cumsum moeten zijn!
axes[1].set_xlabel('Time (d)')
axes[1].set_ylabel('OHW (m)')
>>>>>>> beb5f1ac7bdcfeffa9b26fdd75c6f1bcc92a518b

# %% Indelen in verschillende bakjes
df_dat['LEVERDATUM_ONTVANGST'] = pd.to_datetime(df_dat['LEVERDATUM_ONTVANGST'])
df_OHW_p_t1 = df_dat.groupby(['PROJECT', 'INKOOPORDER', 'ARTIKEL'], as_index=False).agg(
    {'LEVERDATUM_ONTVANGST': 'max', 'Gefactureerd Totaal': 'first', 'Ingeschat': 'first', 'Ontvangen': 'first'})
df_OHW_p_t1 = df_OHW_p_t1.groupby('PROJECT', as_index=False).agg(
    {'LEVERDATUM_ONTVANGST': 'max', 'Gefactureerd Totaal': 'first', 'Ingeschat': 'first', 'Ontvangen': 'sum'})


df_OHW_p_t2 = list_rev_date.loc[len(list_rev_date.index)-1].reset_index(
).rename(columns={len(list_rev_date.index)-1: 'Gefactureerd Revisie'})
df_OHW_p = df_OHW_p_t1.merge(df_OHW_p_t2, on='PROJECT', how='left').rename(
    columns={'Ontvangen': 'Ingekocht'}).fillna(0)  # OHW op projectbasis

df_OHW_p['delta_it'] = df_OHW_p['Ingekocht'] - df_OHW_p['Gefactureerd Totaal']
df_OHW_p['delta_ir'] = df_OHW_p['Ingekocht'] - df_OHW_p['Gefactureerd Revisie']
df_OHW_p['delta_tr'] = df_OHW_p['Gefactureerd Totaal'] - \
    df_OHW_p['Gefactureerd Revisie']
df_OHW_p['delta_ii'] = df_OHW_p['Ingekocht'] - df_OHW_p['Ingeschat']

# verschillende bakken:
<<<<<<< HEAD
# bak 1 meer ingekocht dan gefactureerd & (deel revisie gefactureerd klopt niet met totaal gefactureerd) (Mark Beunk trapt op de rem): 
df_OHW_p_b1 = df_OHW_p[(df_OHW_p['Gefactureerd Totaal'] == 0) & (df_OHW_p['delta_tr'] == 0)] # niets gefactureerd en ook geen deelrevisies...fout bij invoer TPG?
df_OHW_p_b2 = df_OHW_p[(df_OHW_p['Gefactureerd Totaal'] == 0) & (df_OHW_p['delta_tr'] != 0)] # niets gefactureerd maar wel een deelrevisie...niet doorgezet WF of Mark Beunk rem?
# df_OHW_p_b2b = df_OHW_p[(df_OHW_p['Gefactureerd Totaal'] == 0) & (df_OHW_p['delta_tr'] != 0)  & (df_OHW_p['delta_ii'] < 0)] # niets gefactureerd maar wel een deelrevisie, inkoop minder dan ingeschat...niet doorgezet WF of Mark Beunk rem?
df_OHW_p_b3 = df_OHW_p[(df_OHW_p['Gefactureerd Totaal'] != 0) & (df_OHW_p['delta_tr'] == 0)] # wel gefactureerd en ook gelijk aan deelrevisies...doorvoer naar WF klopt maar te weinig? aannemer, TPG handmatig fout excel
df_OHW_p_b4 = df_OHW_p[(df_OHW_p['Gefactureerd Totaal'] != 0) & (df_OHW_p['delta_tr'] < 0)] # wel gefactureerd maar deels geremd door Mark Beunk? dit is te checken kolom gerealiseerd...
# df_OHW_p_b4b = df_OHW_p[(df_OHW_p['Gefactureerd Totaal'] != 0) & (df_OHW_p['delta_tr'] < 0) & (df_OHW_p['delta_ii'] < 0)] # wel gefactureerd maar deels geremd door Mark Beunk? inkoop minder dan ingeschat, dit is te checken kolom gerealiseerd...
df_OHW_p_b5 = df_OHW_p[(df_OHW_p['Gefactureerd Totaal'] != 0) & (df_OHW_p['delta_tr'] > 0)] # wel gefactureerd en meer dan deelrevisies? dit mag niet kunnen...fout in workflow of TPG?

print(str(len(df_OHW_p)) + ' -- ' + str(len(df_OHW_p_b1)+len(df_OHW_p_b2)+len(+df_OHW_p_b3)+len(df_OHW_p_b4)+len(df_OHW_p_b5)))

bakjes_perc = [len(df_OHW_p_b1), len(df_OHW_p_b2), len(df_OHW_p_b3), len(df_OHW_p_b4), len(df_OHW_p_b5)]
bakjes_percm = [df_OHW_p_b1['delta_it'].sum(), df_OHW_p_b2['delta_it'].sum(), df_OHW_p_b3['delta_it'].sum(), \
                df_OHW_p_b4['delta_it'].sum(), df_OHW_p_b5['delta_it'].sum()]
bakjes_desc = ['Oorzaak-1: niet gefactureerd, geen deelrevisie \n Actie: Invoer TPG controleren', \
               'Oorzaak-2: niet gefactureerd, wel deelrevisie \n Actie: Meerwerk naar KPN factureren & Invoer TPG controleren', \
               'Oorzaak-3: wel gefactureerd, gelijk aan deelrevisie \n Actie: Invoer TPG controleren', \
               'Oorzaak-4: wel gefactureerd, deelrevisie hoger \n Actie: Meerwerk naar KPN factureren & Invoer TPG controleren', \
               'Oorzaak-5: wel gefactureerd, deelrevisie lager \n Actie: Controleren invoer WorkFlow & Invoer TPG controleren']

fig1, axes1 = plt.subplots(figsize=(36,20))
axes1.pie(bakjes_perc, labels=bakjes_desc, autopct='%1.2f', startangle=90, textprops={'fontsize': FS})
axes1.axis('equal')
axes1.set_title('Projecten met een OHW [%], opgesplitst per oorzaak & opruim actie, totaal: ' + str(len(df_OHW_p)) + ' projecten', FontSize=FS)

plt.savefig('Figuur-bakjes-OHW-project.png',facecolor='w')

fig2, axes2 = plt.subplots(figsize=(36,20))
axes2.pie(bakjes_percm, labels=bakjes_desc, autopct='%1.2f', startangle=90, textprops={'fontsize': FS})
axes2.axis('equal')
axes2.set_title('Projecten met een OHW [%], opgesplitst per oorzaak & opruim actie, totaal: ' + str(df_OHW_p['delta_it'].sum()) + ' meters', FontSize=FS)
plt.savefig('Figuur-bakjes-OHW-meters.png',facecolor='w')
=======
# bak 1 meer ingekocht dan gefactureerd & (deel revisie gefactureerd klopt niet met totaal gefactureerd) (Mark Beunk trapt op de rem):
# niets gefactureerd en ook geen deelrevisies...fout bij invoer TPG?
df_OHW_p_b1 = df_OHW_p[(df_OHW_p['Gefactureerd Totaal']
                        == 0) & (df_OHW_p['delta_tr'] == 0)]
# niets gefactureerd maar wel een deelrevisie, inkoop meer dan ingeschat...niet doorgezet WF of Mark Beunk rem?
df_OHW_p_b2a = df_OHW_p[(df_OHW_p['Gefactureerd Totaal'] == 0) & (
    df_OHW_p['delta_tr'] != 0) & (df_OHW_p['delta_ii'] > 0)]
# niets gefactureerd maar wel een deelrevisie, inkoop minder dan ingeschat...niet doorgezet WF of Mark Beunk rem?
df_OHW_p_b2b = df_OHW_p[(df_OHW_p['Gefactureerd Totaal'] == 0) & (
    df_OHW_p['delta_tr'] != 0) & (df_OHW_p['delta_ii'] < 0)]
# wel gefactureerd en ook gelijk aan deelrevisies...doorvoer naar WF klopt maar te weinig? aannemer, TPG handmatig fout excel
df_OHW_p_b3 = df_OHW_p[(df_OHW_p['Gefactureerd Totaal']
                        != 0) & (df_OHW_p['delta_tr'] == 0)]
# wel gefactureerd maar deels geremd door Mark Beunk? inkoop meer dan ingeschat, dit is te checken kolom gerealiseerd...
df_OHW_p_b4a = df_OHW_p[(df_OHW_p['Gefactureerd Totaal'] != 0) & (
    df_OHW_p['delta_tr'] < 0) & (df_OHW_p['delta_ii'] > 0)]
# wel gefactureerd maar deels geremd door Mark Beunk? inkoop minder dan ingeschat, dit is te checken kolom gerealiseerd...
df_OHW_p_b4b = df_OHW_p[(df_OHW_p['Gefactureerd Totaal'] != 0) & (
    df_OHW_p['delta_tr'] < 0) & (df_OHW_p['delta_ii'] < 0)]
# wel gefactureerd en meer dan deelrevisies? dit mag niet kunnen...fout in workflow of TPG?
df_OHW_p_b5 = df_OHW_p[(df_OHW_p['Gefactureerd Totaal']
                        != 0) & (df_OHW_p['delta_tr'] > 0)]

print(str(len(df_OHW_p)) + ' -- ' + str(len(df_OHW_p_b1)+len(df_OHW_p_b2a) +
                                        len(df_OHW_p_b2b)+len(+df_OHW_p_b3)+len(df_OHW_p_b4a)+len(df_OHW_p_b4b)+len(df_OHW_p_b5)))

bakjes_perc = [len(df_OHW_p_b1)/len(df_OHW_p), len(df_OHW_p_b2a)/len(df_OHW_p), len(df_OHW_p_b2b)/len(df_OHW_p), len(df_OHW_p_b3) /
               len(df_OHW_p), len(df_OHW_p_b4a)/len(df_OHW_p), len(df_OHW_p_b4b)/len(df_OHW_p), len(df_OHW_p_b5)/len(df_OHW_p)]
bakjes_percm = [df_OHW_p_b1['delta_it'].sum()/df_OHW_p['delta_it'].sum(), df_OHW_p_b2a['delta_it'].sum()/df_OHW_p['delta_it'].sum(), df_OHW_p_b2b['delta_it'].sum()/df_OHW_p['delta_it'].sum(), df_OHW_p_b3['delta_it'].sum()/df_OHW_p['delta_it'].sum(),
                df_OHW_p_b4a['delta_it'].sum()/df_OHW_p['delta_it'].sum(), df_OHW_p_b4b['delta_it'].sum()/df_OHW_p['delta_it'].sum(), df_OHW_p_b5['delta_it'].sum()/df_OHW_p['delta_it'].sum()]
bakjes_desc = ['b1: niet gefactureerd, geen deelrevisie \n MELDEN BIJ TPG-FOUT INVOER',
               'b2a: niet gefactureerd, wel deelrevisie, inkoop meer dan ingeschat \n MEERWERK KPN|MARK BEUNK CONTROLE|KLOPT REVISIE WEL?',
               'b2b: niet gefactureerd, wel deelrevisie, inkoop minder dan ingeschat \n KLOPT REVISIE WEL?',
               'b3: wel gefactureerd, gelijk aan deelrevisie \n REVISIE LOOPT ACHTER OP INKOOP|KLOPT REVISIE WEL?',
               'b4a: wel gefactureerd, deelrevisie hoger, inkoop meer dan ingeschat \n MEERWERK KPN|MARK BEUNK CONTROLE|KLOPT REVISIE WEL?',
               'b4b: wel gefactureerd, deelrevisie hoger, inkoop minder dan ingeschat \n KLOPT REVISIE WEL?',
               'b5: wel gefactureerd, deelrevisie lager \n FOUT IN WORKFLOW?']

fig1, axes1 = plt.subplots(figsize=(10, 10))
axes1.pie(bakjes_perc, labels=bakjes_desc, autopct='%1.2f', startangle=90)
axes1.axis('equal')
axes1.set_title(
    'Alle projecten die vallen onder OHW: inkoop > gefactureerd, per project (totaal: ' + str(len(df_OHW_p)) + ')')

fig2, axes2 = plt.subplots(figsize=(10, 10))
axes2.pie(bakjes_percm, labels=bakjes_desc, autopct='%1.2f', startangle=90)
axes2.axis('equal')
axes2.set_title('Alle projecten die vallen onder OHW: inkoop > gefactureerd, per aantal meters (totaal: ' +
                str(df_OHW_p['delta_it'].sum()) + ')')
>>>>>>> beb5f1ac7bdcfeffa9b26fdd75c6f1bcc92a518b

# vervolg stappen: 1) check invoer TPG via excel zips... 2) automatisch inlezen dwg files... 3) toevoegen kolom gerealiseerd...om revisie-gerealiseerd-rem Mark checken...
# SMART acties vaststellen per bakje!

# %% check op meerwerk
df_dat_mw = df_d  # nieuw dataframe met alle projecten
df_t = pd.DataFrame()
acodes = df_codes_ew['Code'].iloc[0:4].astype('str').to_list()
for i in acodes:
    mask = df_dat_mw['ARTIKEL'].str.contains(
        i)  # ombouwen naar afgeleid artikel
    df_t = pd.concat([df_t, df_dat_mw[mask]], axis=0)
df_dat_mw = df_t  # project codes met meerwerk geul codes!
print('Totaal aantal meter meerwerk over alle projecten: ' +
      str(df_dat_mw.groupby('PROJECT').agg({'Ontvangen': 'sum'}).sum()))
print(df_dat_mw['PROJECT'].unique())  # projecten met meerwerk!
# project codes met ook DP codes, dit mag niet voorkomen, anders dubbel gerekend!
df_dat_mw = df_dat_mw[df_dat_mw['ARTIKEL'].isin(
    df_codes_ew['ARTIKEL'].iloc[4:].astype('str').to_list())]
# komt dus niet voor...
print('Projecten met meerwerk: ' + df_dat_mw['PROJECT'])

# %% per bakje lijst met meeste meters en meest recente data
df_OHW_p_b1.sort_values(by=['LEVERDATUM_ONTVANGST'], ascending=False).head(15)
# df_OHW_p_b1.describe()

# df_OHW_p_b2a.sort_values(by=['LEVERDATUM_ONTVANGST'],ascending=False).head(15)
# df_OHW_p_b2a.describe()

# df_OHW_p_b2b.sort_values(by=['LEVERDATUM_ONTVANGST'],ascending=False).head(15)
# df_OHW_p_b2b.describe()

# df_OHW_p_b3.sort_values(by=['LEVERDATUM_ONTVANGST'],ascending=False).head(15)
# df_OHW_p_b3.describe()

# df_OHW_p_b4a.sort_values(by=['LEVERDATUM_ONTVANGST'],ascending=False).head(15)
# df_OHW_p_b4a.describe()

# df_OHW_p_b4b.sort_values(by=['LEVERDATUM_ONTVANGST'],ascending=False).head(15)
# df_OHW_p_b4b.describe()

# df_OHW_p_b5.sort_values(by=['LEVERDATUM_ONTVANGST'],ascending=False).head(15)
# df_OHW_p_b5.describe()

# %% Vergelijking met dashboard Arend:
print('Aantal projecten: ' +
      str(len(df_d.groupby(['PROJECT']).agg({'Gefactureerd Totaal': 'first'}))))
ing = df_d.groupby(['PROJECT', 'INKOOPORDER', 'ARTIKEL']).agg(
    {'Ontvangen': 'first'}).groupby(['PROJECT']).agg({'Ontvangen': 'sum'}).sum()
gef = df_d.groupby(['PROJECT']).agg({'Gefactureerd Totaal': 'first'}).sum()
print('Verschil ingekocht - gefactureerd in meters: ' + str(ing[0]-gef[0]))

# %%
