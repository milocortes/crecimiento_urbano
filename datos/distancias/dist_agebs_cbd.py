from shapely.geometry import LineString,Point
import shapely.wkt
import pandas as pd
import multiprocessing as mp
import numpy as np
import osmnx as ox
import warnings
from tqdm import tqdm

## Desactivamos los future warnings
warnings.simplefilter(action='ignore', category=Warning)
### Definimos las funciones a utilizar
def get_coords(wkt):
    punto = shapely.wkt.loads(wkt)
    return punto.coords[0]

def nodes_to_linestring(path):
    coords_list = [(G.nodes[i]['x'], G.nodes[i]['y']) for i in path ]
    line = LineString(coords_list)

    return(line)

def shortest_path(datos):
    try:
        G = datos[0]
        agebs_cvegeo = datos[1]
        destino = datos[2]
        orig = tuple(reversed(datos[3]))
        dest = datos[4]

        origin_node = ox.distance.get_nearest_node(G, orig)
        destination_node = ox.distance.get_nearest_node(G, dest)
        ruta = ox.shortest_path(G, origin_node, destination_node, weight="travel_time")
        ruta_cambio = nodes_to_linestring(ruta)
        resultados = {'ageb': [agebs_cvegeo], 'destino': [destino], "ruta": [ruta_cambio]}
        return pd.DataFrame(resultados)
    except Exception:
        # for unsolvable routes (due to directed graph perimeter effects)
        return None

def build_params(destino):
    coordenadas = agebs["centroide"].apply( get_coords)
    agebs_cvegeo = agebs["cvegeo"]
    destino_nombre = [destino for x in range(agebs.shape[0])]
    destino = [destinos[destino] for x in range(agebs.shape[0])]

    params = ((G,agebs_cvegeo,destino_nombre,coordenadas,destino) for agebs_cvegeo,destino_nombre,coordenadas,destino in zip(agebs_cvegeo,destino_nombre,coordenadas,destino))

    return params

### Cargamos los datos de los centroides de los agebs

agebs = pd.read_csv("agebs_centroides.csv")

### Diccionario de principales destinos de trabajo
destinos = {"zocalo": (19.432229587797913, -99.13342540255914),
            "condesa" :(19.41500702816897, -99.17754326239348),
            "reforma" : (19.42631517782024, -99.19379876201027),
            "delValle": (19.373937627246054, -99.17861804875692),
            "viveros": (19.35420491791415, -99.17548474041028),
            "vallejo" : (19.49489893376003, -99.1647650982302),
            "cu": (19.322740688438223, -99.1866604705067),
            "polando" : (19.433666445182244, -99.19094770204629),
            "santafe" : (19.361383705434182, -99.27367230390125)}

### Obtenemos las vialidades de la CDMX
G = ox.graph_from_place('Mexico City, Mexico', network_type='drive')

### Resultados
resultados = pd.DataFrame()

for destino in destinos.keys():
    print("Destino: {}".format(destino))
    ### Generamos los parámetros para calcular las distancias al zócalo
    parametros = build_params(destino)
    for x in tqdm(parametros,total=agebs.shape[0]):
        resultados = resultados.append(shortest_path(x),ignore_index = True)


resultados.to_csv("agebs2cbd_distancias.csv",index=False)

"""
# create a pool of worker processes
pool = mp.Pool(6)

# map the function/parameters to the worker processes
sma = pool.starmap_async(shortest_path, parametros)

# get the results, close the pool, wait for worker processes to all exit
routes = sma.get()
pool.close()
pool.join()
"""
