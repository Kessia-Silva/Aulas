from time import perf_counter_ns
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# PARÂMETROS DO EXPERIMENTO
# ============================================================

N_EXECUCOES = 10_000
N_AMOSTRAS = 3_000
R_GLOBAL = 3

P_LOW = 5
P_HIGH = 95
CV_LIMIT = 0.15


# ============================================================
# ESTATÍSTICAS
# ============================================================

def estatisticas(tempos):
    media = np.mean(tempos)
    desvio = np.std(tempos)

    if media != 0:
        cv = desvio / media
    else:
        cv = np.inf

    return media, desvio, cv


# ============================================================
# MEDIÇÃO DO CONTROLE
# ============================================================

def medir_controle():
    tempos = []

    for _ in range(N_AMOSTRAS * R_GLOBAL):

        tic = perf_counter_ns()

        for _ in range(N_EXECUCOES):
            pass

        tac = perf_counter_ns()

        tempo = (tac - tic) / N_EXECUCOES
        tempos.append(tempo)

    return np.array(tempos)


# ============================================================
# MEDIÇÃO DE UMA COMPARAÇÃO
#
# O controle e a operação são medidos separadamente, mas
# dentro da mesma amostra.
# ============================================================

def medir_comparacao(tipo):

    tempos = []

    for _ in range(N_AMOSTRAS * R_GLOBAL):

        # ----------------------------------------------------
        # CONTROLE
        # ----------------------------------------------------

        tic = perf_counter_ns()

        for _ in range(N_EXECUCOES):
            pass

        tac = perf_counter_ns()

        tempo_controle = (
            (tac - tic) / N_EXECUCOES
        )

        # ----------------------------------------------------
        # COMPARAÇÃO
        # ----------------------------------------------------

        if tipo == "cte_int":

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = (5 == 5)

            tac = perf_counter_ns()

        elif tipo == "var_int_cte":

            a = 5

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = (a == 5)

            tac = perf_counter_ns()

        elif tipo == "var_int_var":

            a = 5
            b = 5

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = (a == b)

            tac = perf_counter_ns()

        elif tipo == "var_float_var":

            x = 5.0
            y = 5.0

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = (x == y)

            tac = perf_counter_ns()

        elif tipo == "var_int_diferente":

            a = 5
            b = 5

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = (a != b)

            tac = perf_counter_ns()

        elif tipo == "var_int_maior":

            a = 5
            b = 5

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = (a > b)

            tac = perf_counter_ns()

        elif tipo == "var_float_cte":

            x = 5.0

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = (x < 5.0)

            tac = perf_counter_ns()

        else:
            raise ValueError("Tipo de comparação inválido.")

        tempo_comparacao = (
            (tac - tic) / N_EXECUCOES
        )

        # ----------------------------------------------------
        # CUSTO DA COMPARAÇÃO
        # ----------------------------------------------------

        tempo = tempo_comparacao - tempo_controle

        if tempo > 0:
            tempos.append(tempo)

    return np.array(tempos)


# ============================================================
# FILTRAGEM E ANÁLISE
# ============================================================

def analisar_resultado(nome, tipo):

    tempos = medir_comparacao(tipo)

    # --------------------------------------------------------
    # ESTATÍSTICAS BRUTAS
    # --------------------------------------------------------

    media_bruta, desvio_bruto, cv_bruto = estatisticas(tempos)

    # --------------------------------------------------------
    # FILTRO P5/P95
    # --------------------------------------------------------

    corte_inf = np.percentile(tempos, P_LOW)
    corte_sup = np.percentile(tempos, P_HIGH)

    tempos_filtrados = tempos[
        (tempos >= corte_inf) &
        (tempos <= corte_sup)
    ]

    # --------------------------------------------------------
    # ESTATÍSTICAS FILTRADAS
    # --------------------------------------------------------

    media_fil, desvio_fil, cv_fil = estatisticas(
        tempos_filtrados
    )

    status = (
        "HOMOLOGADA"
        if cv_fil < CV_LIMIT
        else "REPROVADA"
    )

    print(
        f"{nome:<38}"
        f"{media_bruta:>14.6f}"
        f"{desvio_bruto:>14.6f}"
        f"{cv_bruto:>14.6f}"
        f"{media_fil:>14.6f}"
        f"{desvio_fil:>14.6f}"
        f"{cv_fil:>14.6f}"
        f"{status:>15}"
    )

    return {
        "nome": nome,
        "tempos": tempos,
        "tempos_filtrados": tempos_filtrados,
        "media_bruta": media_bruta,
        "desvio_bruto": desvio_bruto,
        "cv_bruto": cv_bruto,
        "corte_inf": corte_inf,
        "corte_sup": corte_sup,
        "media_fil": media_fil,
        "desvio_fil": desvio_fil,
        "cv_fil": cv_fil,
        "status": status
    }


# ============================================================
# CONTROLE T0
# ============================================================

tempos_t0 = medir_controle()

media_t0_bruta, desvio_t0_bruto, cv_t0_bruto = (
    estatisticas(tempos_t0)
)

corte_t0_inf = np.percentile(tempos_t0, P_LOW)
corte_t0_sup = np.percentile(tempos_t0, P_HIGH)

tempos_t0_filtrados = tempos_t0[
    (tempos_t0 >= corte_t0_inf) &
    (tempos_t0 <= corte_t0_sup)
]

media_t0_fil, desvio_t0_fil, cv_t0_fil = (
    estatisticas(tempos_t0_filtrados)
)


print("\n" + "=" * 100)
print("CONTROLE T0")
print("=" * 100)

print(f"μ T0 bruto = {media_t0_bruta:.6f} ns")
print(f"σ T0 bruto = {desvio_t0_bruto:.6f} ns")
print(f"CV T0 bruto = {cv_t0_bruto:.6f}")

print(f"P{P_LOW} = {corte_t0_inf:.6f} ns")
print(f"P{P_HIGH} = {corte_t0_sup:.6f} ns")

print(f"μ T0 filtrado = {media_t0_fil:.6f} ns")
print(f"σ T0 filtrado = {desvio_t0_fil:.6f} ns")
print(f"CV T0 filtrado = {cv_t0_fil:.6f}")


# ============================================================
# COMPARAÇÕES
# ============================================================

resultados = []

resultado_cte_int = analisar_resultado(
    "cte int == cte int",
    "cte_int"
)

resultados.append(resultado_cte_int)

resultados.append(
    analisar_resultado(
        "var int == cte int",
        "var_int_cte"
    )
)

resultados.append(
    analisar_resultado(
        "var int == var int",
        "var_int_var"
    )
)

resultados.append(
    analisar_resultado(
        "var float == var float",
        "var_float_var"
    )
)

resultados.append(
    analisar_resultado(
        "var int != var int",
        "var_int_diferente"
    )
)

resultados.append(
    analisar_resultado(
        "var int > var int",
        "var_int_maior"
    )
)

resultados.append(
    analisar_resultado(
        "var float < cte float",
        "var_float_cte"
    )
)


# ============================================================
# TABELA FINAL
# ============================================================

print("\n\n")
print("=" * 125)
print("CUSTO DE COMPARAÇÕES (τc)")
print("=" * 125)

print(
    f"{'Operação':<38}"
    f"{'μbruta':>14}"
    f"{'σbruta':>14}"
    f"{'CVbruto':>14}"
    f"{'μfil (τc)':>14}"
    f"{'σfil':>14}"
    f"{'CVfil':>14}"
    f"{'Status':>15}"
)

print("-" * 125)

for resultado in resultados:

    print(
        f"{resultado['nome']:<38}"
        f"{resultado['media_bruta']:>14.6f}"
        f"{resultado['desvio_bruto']:>14.6f}"
        f"{resultado['cv_bruto']:>14.6f}"
        f"{resultado['media_fil']:>14.6f}"
        f"{resultado['desvio_fil']:>14.6f}"
        f"{resultado['cv_fil']:>14.6f}"
        f"{resultado['status']:>15}"
    )

print("=" * 125)


# ============================================================
# GRÁFICOS
# ============================================================

tempos_brutos = resultado_cte_int["tempos"]
tempos_filtrados = resultado_cte_int["tempos_filtrados"]

corte_inf = resultado_cte_int["corte_inf"]
corte_sup = resultado_cte_int["corte_sup"]

media_fil = resultado_cte_int["media_fil"]


# ------------------------------------------------------------
# 1. DISPERSÃO
# ------------------------------------------------------------

plt.figure(figsize=(12, 5))

plt.scatter(
    np.arange(len(tempos_brutos)),
    tempos_brutos,
    s=8
)

plt.axhline(
    corte_inf,
    linestyle="--",
    label=f"P{P_LOW} = {corte_inf:.2f} ns"
)

plt.axhline(
    corte_sup,
    linestyle="--",
    label=f"P{P_HIGH} = {corte_sup:.2f} ns"
)

plt.axhline(
    media_fil,
    linestyle="-",
    label=f"μfil = {media_fil:.2f} ns"
)

plt.title(
    "Dispersão temporizada — τc\n"
    "cte int == cte int"
)

plt.xlabel("Índice da medição")
plt.ylabel("Tempo por execução (ns)")

plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    "tau_c_dispersao.png",
    dpi=300
)

plt.show()


# ------------------------------------------------------------
# 2. HISTOGRAMA BRUTO
# ------------------------------------------------------------

plt.figure(figsize=(10, 5))

plt.hist(
    tempos_brutos,
    bins=30
)

plt.axvline(
    corte_inf,
    linestyle="--",
    label=f"P{P_LOW} = {corte_inf:.2f} ns"
)

plt.axvline(
    corte_sup,
    linestyle="--",
    label=f"P{P_HIGH} = {corte_sup:.2f} ns"
)

plt.axvline(
    media_fil,
    linestyle="-",
    label=f"μfil = {media_fil:.2f} ns"
)

plt.title(
    "Histograma dos dados brutos — τc\n"
    "cte int == cte int"
)

plt.xlabel("Tempo por execução (ns)")
plt.ylabel("Frequência")

plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    "tau_c_histograma_bruto.png",
    dpi=300
)

plt.show()


# ------------------------------------------------------------
# 3. HISTOGRAMA PÓS-FILTRAGEM
# ------------------------------------------------------------

plt.figure(figsize=(10, 5))

plt.hist(
    tempos_filtrados,
    bins=30
)

plt.axvline(
    corte_inf,
    linestyle="--",
    label=f"P{P_LOW} = {corte_inf:.2f} ns"
)

plt.axvline(
    corte_sup,
    linestyle="--",
    label=f"P{P_HIGH} = {corte_sup:.2f} ns"
)

plt.axvline(
    media_fil,
    linestyle="-",
    label=f"μfil = {media_fil:.2f} ns"
)

plt.title(
    "Histograma pós-filtragem — τc\n"
    "cte int == cte int"
)

plt.xlabel("Tempo por execução (ns)")
plt.ylabel("Frequência")

plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    "tau_c_histograma_filtrado.png",
    dpi=300
)

plt.show()


# ============================================================
# PARÂMETROS
# ============================================================

print("\nParâmetros do experimento:")
print(f"n = {N_AMOSTRAS}")
print(f"r = {R_GLOBAL}")
print(f"Execuções internas por medição = {N_EXECUCOES}")
print(f"Filtro = Percentis P{P_LOW}/P{P_HIGH}")
print(f"Critério de homologação = CVfil < {CV_LIMIT}")

print("\nGráficos gerados:")
print("- tau_c_dispersao.png")
print("- tau_c_histograma_bruto.png")
print("- tau_c_histograma_filtrado.png")