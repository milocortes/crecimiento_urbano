from engine import *
import geopandas as gpd
import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import warnings
import os
import sys

zm_selected = sys.argv[1]

## Nos cambiamos al directorio data
os.chdir("../data")
## Desactivamos los future warnings
warnings.simplefilter(action='ignore', category=Warning)

## Cargamos los agebs y localidades
agebs = gpd.read_file("agebs_"+zm_selected+".geojson")
localidades = gpd.read_file("localidades_"+zm_selected+".geojson")
zm_geoms = gpd.read_file("municipios_"+zm_selected+".geojson")
## Calculamos el centroide de cada ageb
agebs["centroide"] = agebs["geometry"].centroid

## Obtenemos la matriz de adjacencia de los vecinos de los agebs
adyacencia_dic = layer2net(agebs)

# Instancia de la clase Network()
agebs_net = Network()

# Agregamos las instancias de cada ageb en el diccionacio de agebs_net
for ageb in list(adyacencia_dic.keys()):
    poblacion = agebs[agebs["CVEGEO"]==ageb]["POBTOT"].item()
    geometria = agebs[agebs["CVEGEO"]==ageb]["geometry"].item()
    centroide = agebs[agebs["CVEGEO"]==ageb]["centroide"].item()
    agebs_net.agebs[ageb]=Ageb(ageb,poblacion,geometria,centroide)

# Agregamos los vecinos de cada ageb
for ageb in list(adyacencia_dic.keys()):
    lista_vecinos = list(np.where((adyacencia_dic[ageb]==1))[0])
    ref_vecinos = []

    if len(lista_vecinos)==0:
        pass
    else:
        for vecino in np.take(list(agebs_net.agebs.keys()),lista_vecinos):
            ref_vecinos.append(agebs_net.agebs[vecino])
        agebs_net.agebs[ageb].vecinos=ref_vecinos

# Obtenemos los límites de la ZM
xmin,ymin,xmax,ymax = zm_geoms.total_bounds

# Obtenemos la red de carreteras de los límites de la ZM
print("%----------------------------------------%")
print("Obteniendo la red de carreteras de la ZM")
print("(Esto puede tardar algunos minutos)")
print("%----------------------------------------%")

G = ox.graph_from_bbox(ymax, ymin, xmax, xmin, network_type='drive')

# Calculamos la trayectoria del centroide de cada ageb con el centride de su ageb vecino
print("%----------------------------------------------------------------------------------------%")
print("Calculamos la trayectoria del centroide de cada ageb con el centride de su ageb vecino")
print("%----------------------------------------------------------------------------------------%")

agebs_cuenta = 0
total_agebs = len(agebs_net.agebs)

for key, ageb in agebs_net.agebs.items():
    agebs_cuenta +=1
    print("Obteniendo las rutas del ageb {} ({} de {})".format(ageb.cvegeo,agebs_cuenta,total_agebs))
    if len(ageb.vecinos)>0:
        for vecino in ageb.vecinos:
            origen = get_coords(ageb.centroide.to_wkt())
            destino = get_coords(vecino.centroide.to_wkt())
            ageb.ruta_vecino[vecino.cvegeo]=shortest_path(G,origen,destino)


## Convertimos los resultados a un GeoDataFrame
print("%----------------------------------------------------------------------------------------%")
print("Convertimos los resultados a un GeoDataFrame")
print("%----------------------------------------------------------------------------------------%")

origen_list = []
destino_list = []
trayectorias_list = []
agebs_cuenta = 0
total_agebs = len(agebs_net.agebs)

for key, ageb in agebs_net.agebs.items():
    agebs_cuenta +=1
    print("({} de {})".format(agebs_cuenta,total_agebs))
    if len(ageb.vecinos)>0:
        for vecino in ageb.vecinos:
            origen_list.append(ageb.cvegeo)
            destino_list.append(vecino.cvegeo)
        for k,v in ageb.ruta_vecino.items():
            if v is None:
                trayectorias_list.append('')
            else:
                trayectorias_list.append(v.to_wkt())


df = pd.DataFrame({"origen":origen_list,"destino":destino_list,"coordinates":trayectorias_list})
df['coordinates'] = gpd.GeoSeries.from_wkt(df['coordinates'])
gdf = gpd.GeoDataFrame(df, geometry='coordinates')
gdf = gdf.set_crs('EPSG:4326')

gdf.to_file("rutas_"+zm_selected+".geojson", driver='GeoJSON')
