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

def trayectoria_agebs(zm_geoms,agebs_net):
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

def get_map(xmin,ymin,xmax,ymax ):
    try:
        return ox.graph_from_bbox(ymax, ymin, xmax, xmin, network_type='drive')
    except Exception:
        ymax = ymax*1.0002
        ymin = ymin*0.9998
        xmax = xmax  + (xmax*-0.0002)
        xmin = xmin*1.0002
        return get_map(xmin,ymin,xmax,ymax)

def trayectoria_agebs_chunks(agebs_net,agebs):
    print("%----------------------------------------------------------------------------------------%")
    print("Calculamos la trayectoria del centroide de cada ageb con el centroide de su ageb vecino")
    print("%----------------------------------------------------------------------------------------%")

    agebs_cuenta = 0
    total_agebs = len(agebs_net.agebs)

    for key, ageb in agebs_net.agebs.items():
        agebs_cuenta +=1
        print("%-----------------------------------------------------%")
        print("Obteniendo las rutas del ageb {} ({} de {})".format(ageb.cvegeo,agebs_cuenta,total_agebs))
        if len(ageb.vecinos)>0:
            # Obtenemos los límites de los agebs vecinos
            xmin,ymin,xmax,ymax = agebs[agebs["CVEGEO"].isin([vecino.cvegeo for vecino in ageb.vecinos])].total_bounds

            # Obtenemos la red de carreteras de los límites de la ZM
            print("Obteniendo la red de carreteras de la ZM")
            G = get_map(xmin,ymin,xmax,ymax)

            for vecino in ageb.vecinos:
                origen = get_coords(ageb.centroide.to_wkt())
                destino = get_coords(vecino.centroide.to_wkt())
                ageb.ruta_vecino[vecino.cvegeo]=shortest_path(G,origen,destino)
            print("%---------------------------------------------------%")


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
