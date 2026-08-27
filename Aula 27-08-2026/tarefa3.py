# achar o tempo médio das primitivas FOCA
from time import time
from matplotlib import pyplot as plt
import numpy as np

R = 100

lista_n = [1000, 10000, 100000]
t = []

for n in lista_n:
    tt = []

    for r in range(R):
        tic = time()

        for i in range(n):
            x = 1

        toc = time()
        tt.append(toc - tic)

    # ordenar os tempos
    tt = np.array(tt)
    tt = np.sort(tt)

    # testar valores de corte
    for tcorte in tt:
        tt_filtrado = tt[tt < tcorte]

        if len(tt_filtrado) > 1:
            media = np.mean(tt_filtrado)
            desvio = np.std(tt_filtrado)
            coef_variacao = desvio / media

            if coef_variacao < 0.15:
                break

    print(f"n = {n}")
    print(f"Tempo de corte = {tcorte}")
    print(f"Média = {media}")
    print(f"Desvio = {desvio}")
    print(f"Coeficiente de variação = {coef_variacao}")
    print(f"Quantidade de tempos = {len(tt_filtrado)}")
    print()

    t.append(tt_filtrado)

    plt.hist(tt_filtrado, bins=50)
    plt.title(f"n={n}")
    plt.savefig(f"tempos.n{n}.png")
    plt.show()