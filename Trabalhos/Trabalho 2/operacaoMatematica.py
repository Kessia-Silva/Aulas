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
# MEDIÇÃO DE UMA OPERAÇÃO MATEMÁTICA
# ============================================================

def medir_operacao(tipo):

    tempos = []

    # Valores utilizados nas operações
    a = 10
    b = 3

    x = 10.0
    y = 3.0

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
        # OPERAÇÃO MATEMÁTICA
        # ----------------------------------------------------

        if tipo == "soma_int_cte":

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = a + 5

            tac = perf_counter_ns()

        elif tipo == "soma_int_var":

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = a + b

            tac = perf_counter_ns()

        elif tipo == "soma_float":

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = x + y

            tac = perf_counter_ns()

        elif tipo == "sub_int":

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = a - b

            tac = perf_counter_ns()

        elif tipo == "mult_int":

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = a * b

            tac = perf_counter_ns()

        elif tipo == "mult_float":

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = x * y

            tac = perf_counter_ns()

        elif tipo == "div_float":

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = x / y

            tac = perf_counter_ns()

        elif tipo == "div_int_piso":

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = a // b

            tac = perf_counter_ns()

        elif tipo == "modulo":

            tic = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                resultado = a % b

            tac = perf_counter_ns()

        else:
            raise ValueError("Tipo de operação inválido.")

        tempo_operacao = (
            (tac - tic) / N_EXECUCOES
        )

        # ----------------------------------------------------
        # CUSTO DA OPERAÇÃO
        # ----------------------------------------------------

        tempo = tempo_operacao - tempo_controle

        if tempo > 0:
            tempos.append(tempo)

    return np.array(tempos)


# ============================================================
# ANÁLISE DE UMA OPERAÇÃO
# ============================================================

def analisar_resultado(nome, tipo):

    tempos = medir_operacao(tipo)

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
        f"{nome:<45}"
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

corte_t0_inf = np.percentile(
    tempos_t0,
    P_LOW
)

corte_t0_sup = np.percentile(
    tempos_t0,
    P_HIGH
)

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
# OPERAÇÕES MATEMÁTICAS
# ============================================================

resultados = []

resultado_soma_int_cte = analisar_resultado(
    "Soma Int: var int + cte int",
    "soma_int_cte"
)

resultados.append(resultado_soma_int_cte)

resultados.append(
    analisar_resultado(
        "Soma Int: var int + var int",
        "soma_int_var"
    )
)

resultados.append(
    analisar_resultado(
        "Soma Float: var float + var float",
        "soma_float"
    )
)

resultados.append(
    analisar_resultado(
        "Subtração Int: var int - var int",
        "sub_int"
    )
)

resultados.append(
    analisar_resultado(
        "Multiplicação Int: var int * var int",
        "mult_int"
    )
)

resultados.append(
    analisar_resultado(
        "Multiplicação Float: var float * var float",
        "mult_float"
    )
)

resultados.append(
    analisar_resultado(
        "Divisão Float: var float / var float",
        "div_float"
    )
)

resultados.append(
    analisar_resultado(
        "Divisão Int (Piso): var int // var int",
        "div_int_piso"
    )
)

resultados.append(
    analisar_resultado(
        "Módulo (Resto): var int % var int",
        "modulo"
    )
)


# ============================================================
# TABELA FINAL
# ============================================================

print("\n\n")
print("=" * 130)
print("CUSTO DE OPERAÇÕES MATEMÁTICAS (τo)")
print("=" * 130)

print(
    f"{'Operação':<45}"
    f"{'μbruta':>14}"
    f"{'σbruta':>14}"
    f"{'CVbruto':>14}"
    f"{'μfil (τo)':>14}"
    f"{'σfil':>14}"
    f"{'CVfil':>14}"
    f"{'Status':>15}"
)

print("-" * 130)

for resultado in resultados:

    print(
        f"{resultado['nome']:<45}"
        f"{resultado['media_bruta']:>14.6f}"
        f"{resultado['desvio_bruto']:>14.6f}"
        f"{resultado['cv_bruto']:>14.6f}"
        f"{resultado['media_fil']:>14.6f}"
        f"{resultado['desvio_fil']:>14.6f}"
        f"{resultado['cv_fil']:>14.6f}"
        f"{resultado['status']:>15}"
    )

print("=" * 130)


# ============================================================
# GRÁFICOS DA MACROPRIMITIVA τo
# ============================================================
#
# Operação representativa:
# Soma Int: var int + cte int
#
# As outras operações permanecem na tabela.
# ============================================================

tempos_brutos = resultado_soma_int_cte["tempos"]
tempos_filtrados = resultado_soma_int_cte["tempos_filtrados"]

corte_inf = resultado_soma_int_cte["corte_inf"]
corte_sup = resultado_soma_int_cte["corte_sup"]

media_fil = resultado_soma_int_cte["media_fil"]


# ============================================================
# GRÁFICO 1 — DISPERSÃO TEMPORIZADA
# ============================================================

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
    "Dispersão temporizada — τo\n"
    "Soma Int: var int + cte int"
)

plt.xlabel("Índice da medição")
plt.ylabel("Tempo por execução (ns)")

plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    "tau_o_dispersao.png",
    dpi=300
)

plt.show()


# ============================================================
# GRÁFICO 2 — HISTOGRAMA BRUTO
# ============================================================

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
    "Histograma dos dados brutos — τo\n"
    "Soma Int: var int + cte int"
)

plt.xlabel("Tempo por execução (ns)")
plt.ylabel("Frequência")

plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    "tau_o_histograma_bruto.png",
    dpi=300
)

plt.show()


# ============================================================
# GRÁFICO 3 — HISTOGRAMA PÓS-FILTRAGEM
# ============================================================

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
    "Histograma pós-filtragem — τo\n"
    "Soma Int: var int + cte int"
)

plt.xlabel("Tempo por execução (ns)")
plt.ylabel("Frequência")

plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    "tau_o_histograma_filtrado.png",
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
print("- tau_o_dispersao.png")
print("- tau_o_histograma_bruto.png")
print("- tau_o_histograma_filtrado.png")