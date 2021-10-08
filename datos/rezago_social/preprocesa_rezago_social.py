import pandas as pd
import re

variables = pd.read_excel("rezago_social_en_ageb_2010_vf.xls",skiprows=2, nrows=1)
variables = [i.lower().replace(" ","_") for i in variables.columns[1:]]
datos = pd.read_excel("rezago_social_en_ageb_2010_vf.xls",skiprows=4, nrows=51034)
datos.drop(columns=['Unnamed: 0'], inplace=True)
datos.rename(columns = {i:j for i,j in zip(datos.columns,variables)}, inplace=True)

datos.to_csv("rezago_social.csv", index=False)
