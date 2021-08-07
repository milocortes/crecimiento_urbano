import geopandas as gpd
from engine import *
from tqdm import tqdm
import geopy.distance
import matplotlib.pyplot as plt
import imageio
import os
### Cargamos datos
agebs = gpd.read_file("agebs_ZM_del_Valle_de_México.geojson")
## Calculamos el centroide de cada ageb
agebs["centroide"] = agebs["geometry"].centroid

## Removemos *
agebs['PRESOE15']=agebs['PRESOE15'].apply(lambda x : float(str(x).replace("*","1.5")))

## Obtenemos la matriz de adjacencia de los vecinos de los agebs
print("%-------------------------------------------------------------%")
print("Obtenemos la matriz de adjacencia de los vecinos de los agebs")
print("%--------------------------------------------------------------%")

adyacencia_dic = layer2net(agebs)

### Definimos las clases y sus atributos
class Ageb:
    def __init__(self,cvegeo,poblacion,geometria,vivienda,inmigrantes,centroide):
        self.cvegeo = cvegeo
        self.poblacion = {0 : poblacion}
        self.vivienda = {0 : vivienda}
        self.inmigrantes = {0 : inmigrantes}
        self.densidad_poblacional = {}
        self.vecinos = []
        self.geometria  = geometria
        self.centroide = centroide
        self.proba_ocupacion_inicial = {}
        self.proba_ocupacion_min = 0
        self.distancia_vecino = {}
        self.ruta_vecino = {}
        self.distancias_cbd = {}
        self.distancias_min_cbd = 0
        self.poblacion_migrante = {}
        self.probabilidad_inmigracion = {}
        self.probabilidad_ocup_total = {}

    def crec_nat_pob_log_continuo(self,k,K,t):
        try:
            A=(K-self.poblacion[t-1])/self.poblacion[t-1]
            P=K/(1+A*np.exp(-k*t))
            self.poblacion[t] = P
        except Exception as e:
            self.poblacion[t] = 0

    def crec_nat_viv_log_continuo(self,k,K,t):
        try:
            A=(K-self.vivienda[t-1])/self.vivienda[t-1]
            P=K/(1+A*np.exp(-k*t))
            self.vivienda[t] = P
        except Exception as e:
            self.vivienda[t] = self.vivienda[t-1]

    def verifica_umbral(self,rho_critica,Delta_r1,Delta_r2,t):
        # Calculamos el indicador de saturación rho

        rho = self.calcula_rho(t)

        if rho >rho_critica:
            p_r = self.poblacion[t] -(rho_critica*self.vivienda[t])
            p_re=p_r*np.random.uniform(Delta_r1,Delta_r2)
            self.poblacion[t] = self.poblacion[t]-p_re
            self.poblacion_migrante[t]=p_re

            return p_re

        return 0

    def calcula_proba_inmigracion(self,t):
        try:
            p_I= self.inmigrantes[t]/self.poblacion[t]
            self.probabilidad_inmigracion[t] = p_I

            #return p_I

        except Exception as e:
            self.probabilidad_inmigracion[t] = 0

            #return 0

    def calcula_probabilidad_ocupacion(self,t):
        p_O = self.probabilidad_inmigracion[t] +  self.proba_ocupacion_min
        self.probabilidad_ocup_total[t]= p_O

        return p_O

    def actualiza_probabilidad_ocupacion(self,t,p_O_suma):
        p_O = self.probabilidad_ocup_total[t]
        self.probabilidad_ocup_total[t] = p_O/p_O_suma

        #return p_O/p_O_suma


    def calcula_rho(self,t):
        try:
            rho = self.poblacion[t]/self.vivienda[t]
            self.densidad_poblacional[t] = rho

            return rho
        except Exception as e:
            self.densidad_poblacional[t] = 0
            return 0

    def reparte_poblacion_migrante(self,t,p_re):
        self.poblacion[t]= self.poblacion[t] + (self.probabilidad_ocup_total[t]*p_re)

class Network:

    def __init__(self):
        self.agebs ={}

    def plot_poblacion(self,t,delta_1,delta_2):
        poblacion_lista = []
        cvegeo_lista = []
        geometria_lista = []
        for ageb_cvegeo,ageb in self.agebs.items():
            geometria_lista.append(ageb.geometria)
            poblacion_lista.append(ageb.poblacion[t])
            cvegeo_lista.append(ageb_cvegeo)
        df = pd.DataFrame({"cvegeo":cvegeo_lista,'poblacion': poblacion_lista,"geometry":geometria_lista})
        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        gdf.plot(column='poblacion',figsize=(15, 15), legend=True)
        plt.title(r'$t$={},$\Delta_{}={}, \Delta_{}={}$'.format(t,"{emin}",delta_1,"{emax}",delta_2), fontsize=20)
        nombre = "delta1_{}_delta2_{}_zmvm_{:02d}.jpg".format(Delta_r1,Delta_r2,t)
        plt.savefig(nombre)
        plt.close()

# Instancia de la clase Network()
agebs_net = Network()

# Agregamos las instancias de cada ageb en el diccionacio de agebs_net
print("%-------------------------------------------------------------%")
print("Agregamos las instancias de cada ageb en el diccionacio de agebs_net")
print("%--------------------------------------------------------------%")
for ageb in tqdm(list(adyacencia_dic.keys())):
    poblacion = agebs[agebs["CVEGEO"]==ageb]["POBTOT"].item()
    geometria = agebs[agebs["CVEGEO"]==ageb]["geometry"].item()
    vivtot = agebs[agebs["CVEGEO"]==ageb]["VIVTOT"].item()
    inmigrantes = agebs[agebs['CVEGEO']==ageb]["PRESOE15"].item()
    centroide = agebs[agebs["CVEGEO"]==ageb]["centroide"].item()
    agebs_net.agebs[ageb]=Ageb(ageb,poblacion,geometria,vivtot,inmigrantes,centroide)

# Agregamos los vecinos de cada ageb
print("%-------------------------------------------------------------%")
print("Agregamos los vecinos de cada ageb")
print("%--------------------------------------------------------------%")
for ageb in tqdm(list(adyacencia_dic.keys())):
    lista_vecinos = list(np.where((adyacencia_dic[ageb]==1))[0])
    ref_vecinos = []

    if len(lista_vecinos)==0:
        pass
    else:
        for vecino in np.take(list(agebs_net.agebs.keys()),lista_vecinos):
            ref_vecinos.append(agebs_net.agebs[vecino])
        agebs_net.agebs[ageb].vecinos=ref_vecinos

### Diccionario de principales destinos de trabajo
destinos = {"zocalo": (19.432229587797913, -99.13342540255914),
            "condesa" :(19.41500702816897, -99.17754326239348),
            "reforma" : (19.42631517782024, -99.19379876201027),
            "delValle": (19.373937627246054, -99.17861804875692),
            "viveros": (19.35420491791415, -99.17548474041028),
            "vallejo" : (19.49489893376003, -99.1647650982302),
            "cu": (19.322740688438223, -99.1866604705067),
            "polanco" : (19.433666445182244, -99.19094770204629),
            "santafe" : (19.361383705434182, -99.27367230390125)}


### Definimos función para calcular distancia geodésica
def get_distancias(origen,destino):
    origen = tuple(reversed(origen.centroide.coords[0]))
    dist = geopy.distance.geodesic(origen,destino)

    return dist.meters

### Obtenemos las distancias con respecto a los centros laborales
for key_ageb,ageb in tqdm(agebs_net.agebs.items()):
    for k,v in destinos.items():
        ageb.distancias_cbd[k]=get_distancias(ageb,v)

for key_ageb,ageb in tqdm(agebs_net.agebs.items()):
    ageb.distancias_min_cbd= min(ageb.distancias_cbd.values())

### Calculamos la probabilidad inicial de cada ageb
b = 15
for key_ageb,ageb in tqdm(agebs_net.agebs.items()):
    r = ageb.distancias_min_cbd/100000
    ageb.proba_ocupacion_min=np.exp(-b*r)

### Main
T=100
#r=4
k_pob= 0.1
K_pob= 6500
k_viv= 0.01
K_viv= 1000
rho_critica=6
b = 30
l_pob = []
l_viv = []
l_p_re = []
l_p_O_suma = []

for b in [15,30,50,100]:
    print(str(b))
    for deltas in tqdm([(0.4,0.4),(0.4,0.5),(0.4,0.9)] ):
        Delta_r1= deltas[0]
        Delta_r2= deltas[1]
        # Iteraciones del periodo 1 a 100
        for t in tqdm(range(1,T)):
            suma_pob = 0
            suma_viv = 0
            suma_p_re = 0
            p_O_suma = 0
            suma_probabilidad_ocupacion=0
            for ageb in agebs_net.agebs:
                if (t-1)==0:
                    r = agebs_net.agebs[ageb].distancias_min_cbd/100000
                    agebs_net.agebs[ageb].proba_ocupacion_min=np.exp(-b*r)
                ### Crecimiento natural
                ### Crecimiento natural
                # Logístico Continuo para población
                agebs_net.agebs[ageb].crec_nat_pob_log_continuo(k_pob,K_pob,t)
                # Logístico Continuo para vivienda
                agebs_net.agebs[ageb].crec_nat_viv_log_continuo(k_viv,K_viv,t)
                suma_pob+=agebs_net.agebs[ageb].poblacion[t]
                suma_viv+=agebs_net.agebs[ageb].vivienda[t]
                # Checar criterio de expulsión
                suma_p_re+=agebs_net.agebs[ageb].verifica_umbral(rho_critica,Delta_r1,Delta_r2,t)
                # Calcular probabilidad de inmigración
                agebs_net.agebs[ageb].calcula_proba_inmigracion(t)
                # Calcula probalidiad de ocupación
                p_O = agebs_net.agebs[ageb].calcula_probabilidad_ocupacion(t)
                p_O_suma += p_O
            # Normaliza probabilidad de ocupación
            for ageb in agebs_net.agebs:
                agebs_net.agebs[ageb].actualiza_probabilidad_ocupacion(t,p_O_suma)
                suma_probabilidad_ocupacion+=agebs_net.agebs[ageb].probabilidad_ocup_total[t]
                ## Se reparte población expulsada
                agebs_net.agebs[ageb].reparte_poblacion_migrante(t,suma_p_re)


            l_pob.append(suma_pob)
            l_viv.append(suma_viv)
            l_p_re.append(suma_p_re)
        os.chdir("resultados")

        imagenes = []
        for i in tqdm(range(T)):
            agebs_net.plot_poblacion(i,Delta_r1,Delta_r2)
            nombre = "delta1_{}_delta2_{}_zmvm_{:02d}.jpg".format(Delta_r1,Delta_r2,i)
            imagenes.append(nombre)
        nombre_gif = "delta1_{}_delta2_{}_b_{}_zmvm.gif".format(Delta_r1,Delta_r2,b)
        with imageio.get_writer(nombre_gif, mode='I') as writer:
            for filename in tqdm(imagenes):
                image = imageio.imread(filename)
                writer.append_data(image)
        os.chdir("..")
