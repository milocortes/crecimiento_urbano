# Cargamos la librerías
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon, Point,LineString
import matplotlib.pyplot as plt
from tqdm import tqdm
import requests

import os
import sys

zm_selected = sys.argv[1]

## Nos cambiamos al directorio geometries
os.chdir("geometries")

## Cargamos la geometría de las zonas metropolitanas (2018)
print("%-----------------------------------------%")
print("Cargamos la geometría de las zonas metropolitanas")
print("%-----------------------------------------%")
zm_geoms = gpd.read_file("SUN2018.geojson")

## Cargamos la geometría de las agebs
print("%-----------------------------------------%")
print("Cargamos la geometría de las agebs")
print("%-----------------------------------------%")
agebs = gpd.read_file("MGN2020_AGEB.geojson")

## Cargamos la geometría de las localidades urbanas
print("%-----------------------------------------%")
print("Cargamos la geometría de las localidades urbanas")
print("%-----------------------------------------%")
localidades =  gpd.read_file("MGN2020_LocalidadesRurales.geojson")

## Nos quedamos con los estados que cubre la ZM seleccionada
zm_geoms = zm_geoms[zm_geoms["NOM_SUN"]==zm_selected]

## Agregar identificadores por entidad y municipio a los datos del SUN 2018
zm_geoms["CVE_ENT"] = zm_geoms["CVE_ENT"].astype(int).apply("{0:0=2d}".format)
zm_geoms["CVE_MUN"] = zm_geoms["CVE_MUN"].astype(int).apply("{0:0=5d}".format)

# Agregamos identificadores de Municipio a ageb y localidades rurales
agebs["CVEGEO_MUN"] = agebs["CVE_ENT"] + agebs["CVE_MUN"]
localidades["CVEGEO_MUN"] = localidades["CVE_ENT"] + localidades["CVE_MUN"]
localidades["CVEGEO"] = localidades["CVEGEO_MUN"] + localidades["CVE_LOC"]


## Descargamos los datos correspondientes a las localidade de los estados de la ZM seleccionada
print("%-----------------------------------------%")
print("Descargamos los datos correspondientes a las localidade de los estados de la ZM seleccionada")
print("%-----------------------------------------%")
censo_loc = pd.read_csv("ITER_NALCSV20.zip")
censo_loc["CVEGEO"]= censo_loc["ENTIDAD"].astype(int).apply("{0:0=2d}".format)+censo_loc["MUN"].astype(int).apply("{0:0=3d}".format)+censo_loc["LOC"].astype(int).apply("{0:0=4d}".format)

## Unimos las geometrías de localidades rurales con los datos del censo
localidades=pd.merge(left=localidades, right=censo_loc, how='left', left_on='CVEGEO', right_on='CVEGEO', suffixes=("_",None))



## Descargamos los datos correspondientes a las agebs de los estados de la ZM seleccionada
print("%-----------------------------------------%")
print("Descargamos los datos correspondientes a las agebs de los estados de la ZM seleccionada")
print("%-----------------------------------------%")

## Nos cambiamos al directorio de descargas
os.chdir("../Descargas")


url = "https://www.inegi.org.mx/contenidos/programas/ccpv/2020/microdatos/ageb_manzana/RESAGEBURB_"
censo2020 = {"{:02d}".format(estado+1):(url+"{:02d}".format(estado+1)+"_2020_csv.zip") for estado in range(32)}
entidades = []
for estado in agebs_zm["CVE_ENT"].unique():
    entidades.append(estado)
    print("%-----------------------------------------%")
    response = requests.get(censo2020[estado], stream=True)
    with open((estado+".zip"), "wb") as handle:
        for data in tqdm(response.iter_content()):
            handle.write(data)

## Por cada descarga, cargamos los datos
dic_entidades={}

for entidad in entidades:
    dic_entidades[entidad]=pd.read_csv(entidad+".zip")
    dic_entidades[entidad]["CVEGEO"]= dic_entidades[entidad]["ENTIDAD"].apply("{0:0=2d}".format)+dic_entidades[entidad]["MUN"].apply("{0:0=3d}".format)+dic_entidades[entidad]["LOC"].apply("{0:0=4d}".format)+dic_entidades[entidad]["AGEB"]
    dic_entidades[entidad] =dic_entidades[entidad][dic_entidades[entidad].MZA==0]
    dic_entidades[entidad] =pd.merge(left=agebs_zm, right=dic_entidades[entidad], how='inner', left_on='CVEGEO', right_on='CVEGEO')
    dic_entidades[entidad].plot(column="POBTOT", legend=True)
    plt.show()

agebs_zm_censo = gpd.GeoDataFrame()

for entidad in entidades:
    agebs_zm_censo = agebs_zm_censo.append(dic_entidades[entidad], ignore_index=True)

## Nos cambiamos al directorio de data para guardar los datos
os.chdir("../../data")

## Seleccionamos las columnas que utilizaremos
columnas_seleccionadas=list(agebs_zm_censo .columns[16:])
columnas_seleccionadas.extend(["CVEGEO", "CVEGEO_MUN", "geometry"])

agebs_zm_censo = agebs_zm_censo[columnas_seleccionadas]
localidades=localidades[columnas_seleccionadas]

zm = pd.concat([agebs_zm_censo, localidades], axis=0)

## Reproyectamos las geometrías
zm= zm.to_crs("EPSG:4326")
zm_geoms = zm_geoms.to_crs("EPSG:4326")

zm.to_file("agebs_"+zm_selected+".geojson", driver='GeoJSON')
zm_geoms.to_file("municipios_"+zm_selected+".geojson", driver='GeoJSON')
