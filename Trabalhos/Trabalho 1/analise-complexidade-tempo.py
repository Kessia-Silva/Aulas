from time import time
import numpy as np

# Quantidade de vezes que cada primitiva será executada
n = 10**6

# Número máximo de experimentos
R = 500


# ==========================================================
# 1. TEMPO DE CONTROLE
# ==========================================================
# Mede somente o custo de iniciar e terminar a medição.
# Não existe uma primitiva entre tic e tac.

T0 = []

for r in range(R):

    t = 0

    for i in range(n):

        tic = time()
        tac = time()

        t += tac - tic

    T0.append(t / n)

    media = np.mean(T0)
    sigma = np.std(T0)

    if sigma / media < 0.15:
        break

T0 = np.mean(T0)


# ==========================================================
# 2. ATRIBUIÇÃO
# ==========================================================
# Primitiva: x = 1

TA = []

for r in range(R):

    t = 0

    for i in range(n):

        tic = time()

        x = 1

        tac = time()

        t += tac - tic

    TA.append(t / n)

    media = np.mean(TA)
    sigma = np.std(TA)

    if sigma / media < 0.15:
        break

TA = np.mean(TA)

# Tempo da atribuição:
tau_a = TA - T0


# ==========================================================
# 3. COMPARAÇÃO
# ==========================================================
# Primitiva: x < n

TC = []

for r in range(R):

    t = 0
    x = 0

    for i in range(n):

        tic = time()

        x < n

        tac = time()

        t += tac - tic

    TC.append(t / n)

    media = np.mean(TC)
    sigma = np.std(TC)

    if sigma / media < 0.15:
        break

TC = np.mean(TC)

# Tempo da comparação:
tau_c = TC - T0


# ==========================================================
# 4. OPERAÇÃO
# ==========================================================
# Primitiva: x + 1

TO = []

for r in range(R):

    t = 0
    x = 0

    for i in range(n):

        tic = time()

        x + 1

        tac = time()

        t += tac - tic

    TO.append(t / n)

    media = np.mean(TO)
    sigma = np.std(TO)

    if sigma / media < 0.15:
        break

TO = np.mean(TO)

# Tempo da operação:
tau_o = TO - T0


# ==========================================================
# RESULTADOS
# ==========================================================

print("T0 =", T0, "segundos")

print()
print("τo =", tau_o, "segundos/operação")
print("τc =", tau_c, "segundos/comparação")
print("τa =", tau_a, "segundos/atribuição")


# ==========================================================
# BENCHMARK
# ==========================================================
# Se T está em segundos/primitiva,
# 1/T dá primitivas/segundo.

print()
print("Benchmark:")

print("1/τo =", 1 / tau_o, "operações/segundo")
print("1/τc =", 1 / tau_c, "comparações/segundo")
print("1/τa =", 1 / tau_a, "atribuições/segundo")