import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

"""
Reglas GoL
    * Any live cell with fewer than two live neighbors dies, as if caused by under population.
    * Any live cell with two or three live neighbors lives on to the next generation.
    * Any live cell with more than three live neighbors dies, as if by overpopulation.
    * Any dead cell with exactly three live neighbors becomes a live cell, as if by reproduction.
"""

dimension=int(sys.argv[1])
iteraciones=int(sys.argv[2])

#kernel=np.zeros([dimension, dimension], dtype = int)
#kernel[int((dimension-1)/2),int((dimension-1)/2)]=1

kernel = np.random.randint(2, size=(dimension, dimension))

class CellularAutomata2D:
    def __init__(self,dimension,matriz):
        self.dimension=dimension
        self.matriz_init=matriz

    def suma_vecinos(self,i,j,dimension,kernel):
        arriba=kernel[(i-1) % dimension, j]
        abajo=kernel[(i+1) % dimension, j]
        derecha=kernel[i,(j+1) % dimension]
        izquierda=kernel[i,(j-1) % dimension]

        d1=kernel[(i-1) % dimension,(j-1) % dimension]
        d2=kernel[(i-1) % dimension,(j+1) % dimension]
        d3=kernel[(i+1) % dimension, (j-1) % dimension]
        d4=kernel[(i+1) % dimension, (j+1) % dimension]

        suma = arriba+abajo+derecha+izquierda+d1+d2+d3+d4
        return suma

    def itera(self,kernel):
        lista_coor_permanecen=[]
        lista_coor_mueren=[]
        dimension=self.dimension

        for i in range(dimension):
            for j in range(dimension):
                if kernel[i,j]==1:

                    suma = self.suma_vecinos(i,j,dimension,kernel)

                    if (suma == 2) or (suma == 3):
                        lista_coor_permanecen.append([i,j])
                    else:
                        lista_coor_mueren.append([i,j])

                if kernel[i,j]==0:

                    suma = self.suma_vecinos(i,j,dimension,kernel)

                    if suma == 3:
                        lista_coor_permanecen.append([i,j])
                    else:
                        lista_coor_mueren.append([i,j])

        for coor in lista_coor_permanecen:
            self.matriz_init[coor[0],coor[1]]=1
        for coor in lista_coor_mueren:
            self.matriz_init[coor[0],coor[1]]=0



### Generamos una instancia de la clase
CA=CellularAutomata2D(dimension, kernel)

### Generamos un giff de las figuras de la matriz en las distintas iteraciones
fig = plt.figure()
ims = []
for i in range(iteraciones):
    CA.itera(CA.matriz_init)
    im = plt.imshow(CA.matriz_init, animated=True)
    ims.append([im])


ani = animation.ArtistAnimation(fig, ims, interval=200, blit=True,
                                repeat_delay=10)

plt.show()

writer = animation.PillowWriter(fps=10)
ani.save("demo_CA2D.gif", writer=writer)
