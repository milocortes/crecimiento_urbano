from shapely.geometry import LineString,Point
import shapely.wkt
import pandas as pd
import multiprocessing as mp
import numpy as np
import osmnx as ox

### Cargamos los datos de los centroides de los agebs

agebs = pd.read_csv("agebs_centroides.csv")

### Diccionario de principales destinos de trabajo
destinos = {"zocalo": (19.432229587797913, -99.13342540255914),
            "condesa" :(19.41500702816897, -99.17754326239348)}

### Obtenemos las vialidades de la CDMX
G = ox.graph_from_place('Mexico City, Mexico', network_type='drive')

P = shapely.wkt.loads('POLYGON ((51.0 3.0, 51.3 3.61, 51.3 3.0, 51.0 3.0))')
