from time import time
import numpy as np

# Valores de n que serão testados
lista_n = [1000, 10000, 100000, 1000000]

# Número de experimentos para cada n
R = 100


# ==========================================================
# 1. ATRIBUIÇÃO
# ==========================================================

print("=== ATRIBUIÇÃO ===")

for n in lista_n:

    tempos = []

    for r in range(R):

        tic = time()

        for i in range(n):
            x = 1

        tac = time()

        tempos.append(tac - tic)

    media = np.mean(tempos)

    print(f"n = {n}")
    print(f"Tempo médio = {media} segundos")
    print()


# ==========================================================
# 2. COMPARAÇÃO
# ==========================================================

print("=== COMPARAÇÃO ===")

for n in lista_n:

    tempos = []
    x = 0

    for r in range(R):

        tic = time()

        for i in range(n):
            x < n

        tac = time()

        tempos.append(tac - tic)

    media = np.mean(tempos)

    print(f"n = {n}")
    print(f"Tempo médio = {media} segundos")
    print()


# ==========================================================
# 3. OPERAÇÃO
# ==========================================================

print("=== OPERAÇÃO ===")

for n in lista_n:

    tempos = []

    for r in range(R):

        tic = time()

        for i in range(n):
            x + 1

        tac = time()

        tempos.append(tac - tic)

    media = np.mean(tempos)

    print(f"n = {n}")
    print(f"Tempo médio = {media} segundos")
    print()