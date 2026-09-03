from time import perf_counter
from matplotlib import pyplot as plt
import numpy as np

R = 100

n = 100000
tt = []

for r in range(R):
    tic = perf_counter()

    for i in range(n):
        x = 1

    toc = perf_counter()
    tt.append(toc - tic)

# ordenar os tempos
tt = np.array(tt)
tt = np.sort(tt)

# calcular média e desvio
media = np.mean(tt)
desvio = np.std(tt)

# testar x = 2 e x = 3
for x in [2, 3]:

    # calcular tempo de corte
    tcorte = media + x * desvio

    # filtrar os tempos
    tt_filtrado = tt[tt < tcorte]

    # calcular estatísticas dos tempos filtrados
    media_filtrada = np.mean(tt_filtrado)
    desvio_filtrado = np.std(tt_filtrado)
    coef_variacao = desvio_filtrado / media_filtrada

    print(f"x = {x}")
    print(f"Tempo de corte = {tcorte}")
    print(f"Média = {media_filtrada}")
    print(f"Desvio = {desvio_filtrado}")
    print(f"Coeficiente de variação = {coef_variacao}")
    print(f"Quantidade de tempos = {len(tt_filtrado)}")
    print()

  
print(f"n = {n}")
print(f"x = {x}")
print(f"Tempo de corte = {tcorte}")
print(f"Média = {media_filtrada}")
print(f"Desvio = {desvio_filtrado}")
print(f"Coeficiente de variação = {coef_variacao}")
print(f"Quantidade de tempos = {len(tt_filtrado)}")
