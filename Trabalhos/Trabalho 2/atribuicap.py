from time import perf_counter_ns
import numpy as np
import matplotlib.pyplot as plt
import os


# ==========================================================
# CONFIGURAÇÃO DO EXPERIMENTO
# ==========================================================

# Instrumentação da captura:
# quantidade de execuções da primitiva dentro de cada medição
N_EXECUCOES = 10_000

# Tamanho da amostra interna (n)
N_AMOSTRAS = 3000

# Número de repetições globais (r)
R_GLOBAL = 3

# Estratégia de filtragem
P_LOW = 5
P_HIGH = 95

# Critério de homologação
CV_LIMIT = 0.15

# Pasta onde os 3 gráficos de τa serão salvos
PASTA_GRAFICOS = "graficos_tau_a"

os.makedirs(PASTA_GRAFICOS, exist_ok=True)


# ==========================================================
# 1. TEMPO DE CONTROLE T0
# ==========================================================

def medir_controle():

    T0 = []

    for i in range(N_AMOSTRAS):

        t = 0

        for j in range(N_EXECUCOES):

            tic = perf_counter_ns()

            tac = perf_counter_ns()

            t += tac - tic

        # Tempo médio de uma captura
        T0.append(t / N_EXECUCOES)

    return np.array(T0, dtype=float)


print("=" * 80)
print("CALIBRAÇÃO DAS ATRIBUIÇÕES — τa")
print("=" * 80)

print()
print("Medindo controle T0...")

T0_GLOBAL = []

for r in range(R_GLOBAL):

    print(f"Repetição global {r + 1}/{R_GLOBAL}")

    T0 = medir_controle()

    T0_GLOBAL.extend(T0)


T0_GLOBAL = np.array(T0_GLOBAL, dtype=float)


# ==========================================================
# ESTATÍSTICAS BRUTAS DO T0
# ==========================================================

mu_T0_bruta = np.mean(T0_GLOBAL)

sigma_T0_bruta = np.std(
    T0_GLOBAL,
    ddof=1
)

cv_T0_bruto = sigma_T0_bruta / mu_T0_bruta


# ==========================================================
# FILTRAGEM DO T0 — P5/P95
# ==========================================================

corte_T0_inferior = np.percentile(
    T0_GLOBAL,
    P_LOW
)

corte_T0_superior = np.percentile(
    T0_GLOBAL,
    P_HIGH
)

T0_FILTRADO = T0_GLOBAL[
    (T0_GLOBAL >= corte_T0_inferior) &
    (T0_GLOBAL <= corte_T0_superior)
]


# ==========================================================
# ESTATÍSTICAS FILTRADAS DO T0
# ==========================================================

mu_T0 = np.mean(T0_FILTRADO)

sigma_T0 = np.std(
    T0_FILTRADO,
    ddof=1
)

cv_T0 = sigma_T0 / mu_T0


print()
print("=" * 80)
print("CONTROLE T0")
print("=" * 80)

print(f"Quantidade bruta:    {len(T0_GLOBAL)}")
print(f"Quantidade filtrada: {len(T0_FILTRADO)}")

print()
print(f"μbruta T0:  {mu_T0_bruta:.6f} ns")
print(f"σbruta T0:  {sigma_T0_bruta:.6f} ns")
print(f"CVbruto T0: {cv_T0_bruto:.6f}")

print()
print(f"P5  T0 = {corte_T0_inferior:.6f} ns")
print(f"P95 T0 = {corte_T0_superior:.6f} ns")

print()
print(f"μfil T0:  {mu_T0:.6f} ns")
print(f"σfil T0:  {sigma_T0:.6f} ns")
print(f"CVfil T0: {cv_T0:.6f}")


# ==========================================================
# FUNÇÃO SOMENTE PARA ANÁLISE
# ==========================================================
# Esta função NÃO gera gráficos.
# Ela apenas calcula as estatísticas da primitiva.
# ==========================================================

def analisar_tempos(nome, tempos, T0):

    # ------------------------------------------------------
    # Subtração do controle
    # ------------------------------------------------------
    #
    # T0 representa o custo médio filtrado da instrumentação.
    # ------------------------------------------------------

    tempos_liquidos = tempos - T0

    # Mantém somente tempos positivos
    tempos_liquidos = tempos_liquidos[
        tempos_liquidos > 0
    ]

    # ------------------------------------------------------
    # ESTATÍSTICAS BRUTAS
    # ------------------------------------------------------

    mu_bruta = np.mean(tempos_liquidos)

    sigma_bruta = np.std(
        tempos_liquidos,
        ddof=1
    )

    cv_bruto = sigma_bruta / mu_bruta

    # ------------------------------------------------------
    # FILTRAGEM P5 - P95
    # ------------------------------------------------------

    corte_inferior = np.percentile(
        tempos_liquidos,
        P_LOW
    )

    corte_superior = np.percentile(
        tempos_liquidos,
        P_HIGH
    )

    tempos_filtrados = tempos_liquidos[
        (tempos_liquidos >= corte_inferior) &
        (tempos_liquidos <= corte_superior)
    ]

    # ------------------------------------------------------
    # ESTATÍSTICAS FILTRADAS
    # ------------------------------------------------------

    mu_fil = np.mean(tempos_filtrados)

    sigma_fil = np.std(
        tempos_filtrados,
        ddof=1
    )

    cv_fil = sigma_fil / mu_fil

    homologada = cv_fil < CV_LIMIT

    # ------------------------------------------------------
    # RESULTADOS NO TERMINAL
    # ------------------------------------------------------

    print()
    print("=" * 80)
    print(nome)
    print("=" * 80)

    print(f"Quantidade bruta:    {len(tempos_liquidos)}")
    print(f"Quantidade filtrada: {len(tempos_filtrados)}")

    print()
    print(f"μbruta  = {mu_bruta:.6f} ns")
    print(f"σbruta  = {sigma_bruta:.6f} ns")
    print(f"CVbruto = {cv_bruto:.6f}")

    print()
    print(f"P5  = {corte_inferior:.6f} ns")
    print(f"P95 = {corte_superior:.6f} ns")

    print()
    print(f"μfil  = {mu_fil:.6f} ns")
    print(f"σfil  = {sigma_fil:.6f} ns")
    print(f"CVfil = {cv_fil:.6f}")

    if homologada:
        print("STATUS = HOMOLOGADA")
    else:
        print("STATUS = REPROVADA")

    return {
        "nome": nome,
        "tempos_liquidos": tempos_liquidos,
        "tempos_filtrados": tempos_filtrados,
        "corte_inferior": corte_inferior,
        "corte_superior": corte_superior,
        "mu_bruta": mu_bruta,
        "sigma_bruta": sigma_bruta,
        "cv_bruto": cv_bruto,
        "mu_fil": mu_fil,
        "sigma_fil": sigma_fil,
        "cv_fil": cv_fil,
        "homologada": homologada
    }


# ==========================================================
# 2. var int ← cte int
# ==========================================================

TA_INT_CTE = []

print()
print("Medindo: var int ← cte int")

for r in range(R_GLOBAL):

    print(f"  Repetição global {r + 1}/{R_GLOBAL}")

    for i in range(N_AMOSTRAS):

        t = 0

        for j in range(N_EXECUCOES):

            tic = perf_counter_ns()

            a = 5

            tac = perf_counter_ns()

            t += tac - tic

        TA_INT_CTE.append(t / N_EXECUCOES)


TA_INT_CTE = np.array(
    TA_INT_CTE,
    dtype=float
)


# ==========================================================
# 3. var float ← cte float
# ==========================================================

TA_FLOAT_CTE = []

print()
print("Medindo: var float ← cte float")

for r in range(R_GLOBAL):

    print(f"  Repetição global {r + 1}/{R_GLOBAL}")

    for i in range(N_AMOSTRAS):

        t = 0

        for j in range(N_EXECUCOES):

            tic = perf_counter_ns()

            a = 5.0

            tac = perf_counter_ns()

            t += tac - tic

        TA_FLOAT_CTE.append(t / N_EXECUCOES)


TA_FLOAT_CTE = np.array(
    TA_FLOAT_CTE,
    dtype=float
)


# ==========================================================
# 4. var bool ← cte bool
# ==========================================================

TA_BOOL_CTE = []

print()
print("Medindo: var bool ← cte bool")

for r in range(R_GLOBAL):

    print(f"  Repetição global {r + 1}/{R_GLOBAL}")

    for i in range(N_AMOSTRAS):

        t = 0

        for j in range(N_EXECUCOES):

            tic = perf_counter_ns()

            a = True

            tac = perf_counter_ns()

            t += tac - tic

        TA_BOOL_CTE.append(t / N_EXECUCOES)


TA_BOOL_CTE = np.array(
    TA_BOOL_CTE,
    dtype=float
)


# ==========================================================
# 5. var int ← var int
# ==========================================================

TA_INT_VAR = []

b = 5

print()
print("Medindo: var int ← var int")

for r in range(R_GLOBAL):

    print(f"  Repetição global {r + 1}/{R_GLOBAL}")

    for i in range(N_AMOSTRAS):

        t = 0

        for j in range(N_EXECUCOES):

            tic = perf_counter_ns()

            a = b

            tac = perf_counter_ns()

            t += tac - tic

        TA_INT_VAR.append(t / N_EXECUCOES)


TA_INT_VAR = np.array(
    TA_INT_VAR,
    dtype=float
)


# ==========================================================
# 6. var float ← var float
# ==========================================================

TA_FLOAT_VAR = []

b = 5.0

print()
print("Medindo: var float ← var float")

for r in range(R_GLOBAL):

    print(f"  Repetição global {r + 1}/{R_GLOBAL}")

    for i in range(N_AMOSTRAS):

        t = 0

        for j in range(N_EXECUCOES):

            tic = perf_counter_ns()

            a = b

            tac = perf_counter_ns()

            t += tac - tic

        TA_FLOAT_VAR.append(t / N_EXECUCOES)


TA_FLOAT_VAR = np.array(
    TA_FLOAT_VAR,
    dtype=float
)


# ==========================================================
# 7. ANÁLISE DOS RESULTADOS
# ==========================================================

resultado_int_cte = analisar_tempos(
    "var int ← cte int",
    TA_INT_CTE,
    mu_T0
)

resultado_float_cte = analisar_tempos(
    "var float ← cte float",
    TA_FLOAT_CTE,
    mu_T0
)

resultado_bool_cte = analisar_tempos(
    "var bool ← cte bool",
    TA_BOOL_CTE,
    mu_T0
)

resultado_int_var = analisar_tempos(
    "var int ← var int",
    TA_INT_VAR,
    mu_T0
)

resultado_float_var = analisar_tempos(
    "var float ← var float",
    TA_FLOAT_VAR,
    mu_T0
)


# ==========================================================
# 8. PAINEL GRÁFICO DE ESTABILIDADE — τa
# ==========================================================
#
# O professor solicita exatamente 3 gráficos para
# cada macroprimitiva.
#
# Para τa, utilizamos uma atribuição representativa:
#
# var int ← cte int
#
# As outras atribuições continuam sendo utilizadas
# normalmente na tabela de calibração.
# ==========================================================

dados_grafico = resultado_int_cte

tempos = dados_grafico["tempos_liquidos"]

tempos_filtrados = dados_grafico[
    "tempos_filtrados"
]

corte_inferior = dados_grafico[
    "corte_inferior"
]

corte_superior = dados_grafico[
    "corte_superior"
]


# ----------------------------------------------------------
# GRÁFICO 1 — DISPERSÃO TEMPORIZADA
# ----------------------------------------------------------

plt.figure(figsize=(10, 5))

plt.scatter(
    range(1, len(tempos) + 1),
    tempos,
    s=4
)

plt.axhline(
    corte_inferior,
    linestyle="--",
    label="P5"
)

plt.axhline(
    corte_superior,
    linestyle="--",
    label="P95"
)

plt.xlabel("Índice da medição")
plt.ylabel("Tempo médio por atribuição (ns)")
plt.title("τa — Dispersão temporizada")

plt.legend()
plt.grid(True, alpha=0.3)

plt.savefig(
    os.path.join(
        PASTA_GRAFICOS,
        "tau_a_dispersao.png"
    ),
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ----------------------------------------------------------
# GRÁFICO 2 — HISTOGRAMA DOS DADOS BRUTOS
# ----------------------------------------------------------

plt.figure(figsize=(10, 5))

plt.hist(
    tempos,
    bins=40
)

plt.axvline(
    corte_inferior,
    linestyle="--",
    label="P5"
)

plt.axvline(
    corte_superior,
    linestyle="--",
    label="P95"
)

plt.xlabel("Tempo médio por atribuição (ns)")
plt.ylabel("Frequência")
plt.title("τa — Histograma dos dados brutos")

plt.legend()
plt.grid(True, alpha=0.3)

plt.savefig(
    os.path.join(
        PASTA_GRAFICOS,
        "tau_a_histograma_bruto.png"
    ),
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ----------------------------------------------------------
# GRÁFICO 3 — HISTOGRAMA PÓS-FILTRAGEM
# ----------------------------------------------------------

plt.figure(figsize=(10, 5))

plt.hist(
    tempos_filtrados,
    bins=40
)

plt.axvline(
    corte_inferior,
    linestyle="--",
    label="P5"
)

plt.axvline(
    corte_superior,
    linestyle="--",
    label="P95"
)

plt.xlabel("Tempo médio por atribuição (ns)")
plt.ylabel("Frequência")
plt.title("τa — Histograma pós-filtragem")

plt.legend()
plt.grid(True, alpha=0.3)

plt.savefig(
    os.path.join(
        PASTA_GRAFICOS,
        "tau_a_histograma_filtrado.png"
    ),
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ==========================================================
# 9. TABELA FINAL
# ==========================================================

resultados = [
    resultado_int_cte,
    resultado_float_cte,
    resultado_bool_cte,
    resultado_int_var,
    resultado_float_var
]

nomes_tabela = [
    "var int ← cte int",
    "var float ← cte float",
    "var bool ← cte bool",
    "var int ← var int",
    "var float ← var float"
]


print()
print()
print("=" * 120)
print("TABELA FINAL — CALIBRAÇÃO τa")
print("=" * 120)

print(
    f"{'Operação':35}"
    f"{'μbruta':>14}"
    f"{'σbruta':>14}"
    f"{'CVbruto':>14}"
    f"{'μfil':>14}"
    f"{'σfil':>14}"
    f"{'CVfil':>14}"
    f"{'Status':>16}"
)

print("-" * 120)


for nome_tabela, resultado in zip(
    nomes_tabela,
    resultados
):

    status = (
        "HOMOLOGADA"
        if resultado["homologada"]
        else "REPROVADA"
    )

    print(
        f"{nome_tabela:35}"
        f"{resultado['mu_bruta']:14.6f}"
        f"{resultado['sigma_bruta']:14.6f}"
        f"{resultado['cv_bruto']:14.6f}"
        f"{resultado['mu_fil']:14.6f}"
        f"{resultado['sigma_fil']:14.6f}"
        f"{resultado['cv_fil']:14.6f}"
        f"{status:>16}"
    )


print()
print("=" * 80)
print("EXPERIMENTO FINALIZADO")
print("=" * 80)
print()
print("Macroprimitiva: τa — Atribuições")
print(f"n = {N_AMOSTRAS}")
print(f"r = {R_GLOBAL}")
print(f"Execuções por captura (instrumentação) = {N_EXECUCOES}")
print("Estratégia de filtragem = P5/P95")
print(
    "Total de medições por atribuição =",
    N_AMOSTRAS * R_GLOBAL
)
print("Gráficos gerados: 3")
print(f"Gráficos salvos em: {PASTA_GRAFICOS}")
print("Os gráficos não foram exibidos na tela.")