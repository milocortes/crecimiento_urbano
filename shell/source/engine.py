from shapely.geometry import Polygon, Point,LineString
import shapely.wkt
import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nx
from tqdm import tqdm

### Definimos las funciones a utilizar
def get_coords(wkt):
    punto = shapely.wkt.loads(wkt)
    return punto.coords[0]

def nodes_to_linestring(path):
    coords_list = [(G.nodes[i]['x'], G.nodes[i]['y']) for i in path ]
    line = LineString(coords_list)

    return(line)

def shortest_path(G,origen,destino):
    try:
        orig = tuple(reversed(origen))
        dest = tuple(reversed(destino))

        origin_node = ox.distance.get_nearest_node(G, orig)
        destination_node = ox.distance.get_nearest_node(G, dest)
        ruta = ox.shortest_path(G, origin_node, destination_node, weight="travel_time")
        ruta_cambio = nodes_to_linestring(ruta)
        return ruta_cambio
    except Exception:
        # for unsolvable routes (due to directed graph perimeter effects)
        return None

def build_params(destino):
    coordenadas = agebs["centroide"].apply( get_coords)
    agebs_cvegeo = agebs["CVEGEO"]
    destino_nombre = [destino for x in range(agebs.shape[0])]
    destino = [destinos[destino] for x in range(agebs.shape[0])]

    params = ((G,agebs_cvegeo,destino_nombre,coordenadas,destino) for agebs_cvegeo,destino_nombre,coordenadas,destino in zip(agebs_cvegeo,destino_nombre,coordenadas,destino))

    return params

def layer2net(capa):
    almacena = {}

    for geometria in range(capa.shape[0]):
        if (geometria % 500)==0:
            print("{} agebs procesados".format(geometria))
        cvegeo=capa.loc[geometria,"CVEGEO"]
        vecinos = np.array(capa['geometry'].touches(capa.loc[geometria,"geometry"]),dtype=int)
        almacena[cvegeo]= vecinos

    return almacena

class Ageb:
    def __init__(self,cvegeo,poblacion,geometria,centroide):
        self.cvegeo = cvegeo
        self.poblacion = {0 : poblacion}
        self.vecinos = []
        self.geometria  = geometria
        self.centroide = centroide
        self.distancia_vecino = {}
        self.ruta_vecino = {}



class Network:
    def __init__(self):
        self.agebs ={}
