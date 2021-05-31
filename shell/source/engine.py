from shapely.geometry import Polygon, Point,LineString,MultiPolygon
from shapely.geometry.base import BaseMultipartGeometry
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

def nodes_to_linestring(G,path):
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
        ruta_cambio = nodes_to_linestring(G,ruta)
        print("Se obtuvo ruta correctamente")
        return ruta_cambio
    except Exception:
        # for unsolvable routes (due to directed graph perimeter effects)
        return None

def touches_geometria(evalua,geometria):
    if isinstance(evalua,BaseMultipartGeometry):
        resultados = []
        for objetos in evalua:
            resultados.append(touches_geometria(objetos,geometria))
        return any(resultados)
    else:
        evalua_status = evalua.is_valid
        geometria_status = geometria.is_valid

        if isinstance(geometria,BaseMultipartGeometry):
            geometria = geometria.buffer(0)
            geometria_status = geometria.is_valid
        if (geometria_status == False and evalua_status == False ):
            return geometria.boundary.touches(evalua.boundary)
        elif (geometria_status == True and evalua_status == False ):
            return geometria.touches(evalua.boundary)
        elif (geometria_status == False and evalua_status == True ):
            return geometria.boundary.touches(evalua)
        else:
            return geometria.touches(evalua)


def layer2net(capa):
    almacena = {}
    agebs_total = capa.shape[0]

    for geometria in tqdm(range(agebs_total)):
        cvegeo=capa.loc[geometria,"CVEGEO"]
        vecinos = np.array(capa['geometry'].apply(lambda x: touches_geometria(x,capa.loc[geometria,"geometry"])),dtype=int)
        #vecinos = np.array(capa['geometry'].boundary.touches(capa.loc[geometria,"geometry"]),dtype=int)
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
