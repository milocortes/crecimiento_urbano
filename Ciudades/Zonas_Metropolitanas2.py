# -*- coding: utf-8 -*-
"""
Created on Tue Jun  1 19:33:07 2021

@author: Héctor M
"""


# Cargamos la librerías
import geopandas as gpd              #Librería: Datos geoespaciales
import pandas as pd                  #Librería: bases de datos
import matplotlib.pyplot as plt      #Librería: Visualización de gráficos
import numpy as np                   #Librería: Computo científico
import os                            #Librería

# Zona metropolitana seleccionada
zm_selected='Valle de México'


## Cambios el directorio a "data"
os.chdir("C:\\Users\\4PF42LA_1909\\Phyton\\crecimiento_metropolitano\\data")


def Extraer_Censo(zm_entidades):
    # Extraer Bases de datos de las entidades
    censo_zm = pd.DataFrame()

    ruta = "D:\\Documentos\\ESTADISTICA\\Censo de Población y Vivienda\\CPyV 2020\\Principales resultados por AGEB y manzana"    
    for estado in zm_entidades:
        archivo = ruta+'\\RESAGEBURB_'+str(estado)+'_2020_csv.zip'
        censo_estado = pd.read_csv(archivo, compression='zip')
        censo_estado["CVEGEO"]= censo_estado["ENTIDAD"].astype(int).apply("{0:0=2d}".format)+censo_estado["MUN"].astype(int).apply("{0:0=3d}".format)+censo_estado["LOC"].astype(int).apply("{0:0=4d}".format)+censo_estado["AGEB"]
        censo_estado =censo_estado[censo_estado.MZA==0]
        censo_zm = censo_zm.append(censo_estado)
        
    return censo_zm

## Leer bases de datos
zm_geoms = gpd.read_file("SUN2018.geojson")                                 #Geoegrafía de ZM y ciudades del Sistema Urbano Nacional 2018
agebs  = gpd.read_file("MGN2020_AGEB.geojson")                              #AGEBS urbanos
localidades_rurales  = gpd.read_file("MGN2020_LocalidadesRurales.geojson")  #Localidades rurales

# Convertir los puntos de las localidades rurales en circulos de 500m de diametro
localidades_rurales["geometry"] = localidades_rurales.buffer(250)           

## Agregar identificadores por entidad y municipio a los datos del SUN 2018
zm_geoms["CVE_ENT"] = zm_geoms["CVE_ENT"].astype(int).apply("{0:0=2d}".format)
zm_geoms["CVE_MUN"] = zm_geoms["CVE_MUN"].astype(int).apply("{0:0=5d}".format)

# Agregamos identificadores de Municipio a ageb y localidades rurales
agebs["CVEGEO_MUN"] = agebs["CVE_ENT"] + agebs["CVE_MUN"]
localidades_rurales["CVEGEO_MUN"] = localidades_rurales["CVE_ENT"] + localidades_rurales["CVE_MUN"]
localidades_rurales["CVEGEO"]=localidades_rurales["CVEGEO_MUN"]+localidades_rurales["CVE_LOC"]

## Extraemos la ZM o la ciudad 
zm_geoms = zm_geoms[zm_geoms["NOM_SUN"]==zm_selected]

# Lista de municipios y entidades de la ZM
zm_municipios = zm_geoms.CVE_MUN.unique()
zm_entidades = zm_geoms["CVE_ENT"].unique()

# Extraemos ageb y localidades rurales dentro de la ZM
agebs=agebs[agebs.CVEGEO_MUN.isin(zm_municipios)]
localidades_rurales=localidades_rurales[localidades_rurales.CVEGEO_MUN.isin(zm_municipios)]

# Extraemos los datos del Censo de Poblacion y Vivienda 2020 para AGEB
censo_ageb = Extraer_Censo(zm_entidades)


# Extraemos los datos del Censo de Poblacion y Vivienda 2020 para AGEB
censo_loc = pd.read_csv("D:\\Documentos\\ESTADISTICA\\Censo de Población y Vivienda\\CPyV 2020\\Principales resultados por localidad (ITER)\\ITER_NALCSV20.csv")
censo_loc["CVEGEO"]= censo_loc["ENTIDAD"].astype(int).apply("{0:0=2d}".format)+censo_loc["MUN"].astype(int).apply("{0:0=3d}".format)+censo_loc["LOC"].astype(int).apply("{0:0=4d}".format)
        
zm_ageb=pd.merge(left=agebs, right=censo_ageb, how='left', left_on='CVEGEO', right_on='CVEGEO', suffixes=("_",None))

localidades_rurales=pd.merge(left=localidades_rurales, right=censo_loc, how='left', left_on='CVEGEO', right_on='CVEGEO', suffixes=("_",None))

columnas_seleccionadas=list(zm_ageb.columns[16:])
columnas_seleccionadas.extend(["CVEGEO", "CVEGEO_MUN", "geometry"])

zm_ageb=zm_ageb[columnas_seleccionadas]
localidades_rurales=localidades_rurales[columnas_seleccionadas]

zm = pd.concat([zm_ageb, localidades_rurales], axis=0)


zm = zm[zm.POBTOT!=0]
zm = zm[zm.VIVTOT!=0]

zm["Densidad"]=zm["POBTOT"]/zm["VIVTOT"]

zm = zm[zm.Densidad<10]

## Cambios el directorio a "output"
os.chdir("C:\\Users\\4PF42LA_1909\\Phyton\\crecimiento_metropolitano\\output")
os.mkdir(zm_selected)

os.chdir(zm_selected)

zm.to_file("agebs_"+zm_selected+".geojson", driver='GeoJSON')
zm_geoms.to_file("municipios_"+zm_selected+".geojson", driver='GeoJSON')

#%%%

def Graficar_Distribucion(columna='POBTOT', esquema='Quantiles', color='coolwarm'):
    ax =zm.plot(figsize=(20, 20), 
            column=columna,
            legend=True,
            scheme=esquema,
            cmap=color)
    zm_geoms.boundary.plot(ax=ax, edgecolor='black', linewidth=1)
    ax.set_axis_off()
    titulo='Distribución de '+ columna+' por AGEB urbano y localidad rural\n('+zm_selected.replace ("_", " ")+' 2020)'
    plt.title(titulo, fontsize=20)
    
    # Colores secuenciales
        #'OrRd':  Naranja-rojo
        #'YlOrBr': Amarillo-rojo
        # 'GnBu': Azules
        # 'YlGn': Verdes
    # Divergentes
        # coolwarm: Azul-Rojo
    
    # Esquemas:
        # 'EqualInterval'
        # 'NaturalBreaks'
        # 'Quantiles'
        # 'Percentiles'

#%%

ax =zm.plot(figsize=(20, 20), 
            column='VIVTOT',
            legend=True,
            scheme='Quantiles',
            cmap='YlOrBr')
zm_geoms.boundary.plot(ax=ax, edgecolor='black', linewidth=1)
ax.set_axis_off()
ax.set_title('Distribución de la poblacion por AGEB urbano y localidad rural', fontsize=24)

ax =zm[zm.Densidad<10].plot(figsize=(20, 20), 
            column='Densidad',
            legend=True,
            scheme='Quantiles',
            cmap='YlGn')
zm_geoms.boundary.plot(ax=ax, edgecolor='black', linewidth=1)
ax.set_axis_off()
ax.set_title('Densidad', fontsize=16)