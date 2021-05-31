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

## Cargamos la geometría de las zonas metropolitanas
print("%-----------------------------------------%")
print("Cargamos la geometría de las zonas metropolitanas")
print("%-----------------------------------------%")

zm_geoms = gpd.read_file("zm_geom.geojson")
## Cargamos la geometría de las agebs
print("%-----------------------------------------%")
print("Cargamos la geometría de las agebs")
print("%-----------------------------------------%")
agebs = gpd.read_file("MGN2020_AGEB.zip")
## Cargamos la geometría de las localidades urbanas
print("%-----------------------------------------%")
print("Cargamos la geometría de las localidades urbanas")
print("%-----------------------------------------%")
localidades =  gpd.read_file("MGN2020_LocalidadesRurales.zip")

## Nos quedamos con los estados que cubre la ZM seleccionada
zm_geoms = zm_geoms[zm_geoms["zm"]==zm_selected]

## Utilizamos el método overlay de geopandas para quedarnos con las agebs de la ZM seleccionada
zm_geoms = zm_geoms.to_crs("EPSG:6372")
agebs_zm = gpd.overlay(zm_geoms.dissolve("zm")[['NOM_MUN','clave','geometry']],agebs,how='intersection',keep_geom_type = False)
agebs_zm["CVEGEO"]= agebs_zm['CVE_ENT']+agebs_zm['CVE_MUN']+agebs_zm["CVE_LOC"]+agebs_zm["CVE_AGEB"]
agebs_zm.plot()
plt.show()

## Utilizamos el método overlay de geopandas para quedarnos con las localidades de la ZM seleccionada
localidades_zm = gpd.overlay(zm_geoms.dissolve("zm")[['geometry']],localidades,how='intersection', keep_geom_type = False)

## Descargamos los datos correspondientes a las agebs de los estados de la ZM seleccionada
print("%-----------------------------------------%")
print("Descargamos los datos correspondientes a las agebs de los estados de la ZM seleccionada")
print("%-----------------------------------------%")

## Nos cambiamos al directorio de descargas
os.chdir("../downloads")


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

## Reproyectamos las geometrías
agebs_zm_censo = agebs_zm_censo.to_crs("EPSG:4326")
localidades_zm = localidades_zm.to_crs("EPSG:4326")
zm_geoms = zm_geoms.to_crs("EPSG:4326")

agebs_zm_censo.to_file("agebs_"+zm_selected+".geojson", driver='GeoJSON')
localidades_zm.to_file("localidades_"+zm_selected+".geojson", driver='GeoJSON')
zm_geoms.to_file("municipios_"+zm_selected+".geojson", driver='GeoJSON')
