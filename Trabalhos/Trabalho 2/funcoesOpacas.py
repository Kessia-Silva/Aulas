import numpy as np
import matplotlib.pyplot as plt
from time import perf_counter_ns
from pathlib import Path


# ============================================================
# CONFIGURAÇÕES DO EXPERIMENTO
# ============================================================

N_AMOSTRAS = 3000
R_GLOBAL = 3
N_EXECUCOES = 10000

CV_LIMITE = 0.15

P5 = 5
P95 = 95

PASTA_GRAFICOS = Path("graficos_F")
PASTA_GRAFICOS.mkdir(exist_ok=True)


# ============================================================
# FUNÇÕES DA EQUIPE
# ============================================================

def calcular_media(lista):
    soma = 0.0

    for valor in lista:
        soma += valor

    return soma / len(lista)


def soma_quadrados(lista):
    resultado = 0.0

    for valor in lista:
        resultado += valor * valor

    return resultado


# ============================================================
# DADOS UTILIZADOS PELAS FUNÇÕES
# ============================================================

LISTA_MEDIA = [
    1.0, 2.0, 3.0, 4.0, 5.0,
    6.0, 7.0, 8.0, 9.0, 10.0
]

LISTA_QUADRADOS = [
    1.0, 2.0, 3.0, 4.0, 5.0,
    6.0, 7.0, 8.0, 9.0, 10.0
]


# ============================================================
# FUNÇÕES OPACAS A SEREM CALIBRADAS
# ============================================================

FUNCOES = [
    (
        "Função 1: calcular_media(lista)",
        lambda: calcular_media(LISTA_MEDIA)
    ),

    (
        "Função 2: soma_quadrados(lista)",
        lambda: soma_quadrados(LISTA_QUADRADOS)
    ),
]


# ============================================================
# MEDIÇÃO DO CONTROLE
# ============================================================

def medir_controle():

    tempos = []

    for r in range(R_GLOBAL):

        print(f"  Repetição global {r + 1}/{R_GLOBAL}")

        for _ in range(N_AMOSTRAS):

            inicio = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                pass

            fim = perf_counter_ns()

            tempo = (fim - inicio) / N_EXECUCOES

            tempos.append(tempo)

    return np.array(tempos, dtype=float)


# ============================================================
# MEDIÇÃO DE UMA FUNÇÃO OPACA
# ============================================================

def medir_funcao(funcao):

    tempos = []

    for r in range(R_GLOBAL):

        print(f"  Repetição global {r + 1}/{R_GLOBAL}")

        for _ in range(N_AMOSTRAS):

            # ------------------------------------------------
            # CONTROLE
            # ------------------------------------------------

            inicio_controle = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                pass

            fim_controle = perf_counter_ns()

            tempo_controle = (
                (fim_controle - inicio_controle)
                / N_EXECUCOES
            )

            # ------------------------------------------------
            # FUNÇÃO
            # ------------------------------------------------

            inicio = perf_counter_ns()

            for _ in range(N_EXECUCOES):
                funcao()

            fim = perf_counter_ns()

            tempo_funcao = (
                (fim - inicio)
                / N_EXECUCOES
            )

            # ------------------------------------------------
            # CUSTO DA FUNÇÃO
            # ------------------------------------------------

            custo = tempo_funcao - tempo_controle

            tempos.append(custo)

    return np.array(tempos, dtype=float)


# ============================================================
# CÁLCULO DAS ESTATÍSTICAS
# ============================================================

def calcular_estatisticas(tempos):

    media_bruta = np.mean(tempos)
    sigma_bruta = np.std(tempos)

    if media_bruta != 0:
        cv_bruto = sigma_bruta / abs(media_bruta)
    else:
        cv_bruto = float("inf")

    p5 = np.percentile(tempos, P5)
    p95 = np.percentile(tempos, P95)

    mascara = (
        (tempos >= p5)
        &
        (tempos <= p95)
    )

    tempos_filtrados = tempos[mascara]

    media_filtrada = np.mean(tempos_filtrados)
    sigma_filtrada = np.std(tempos_filtrados)

    if media_filtrada != 0:
        cv_filtrado = (
            sigma_filtrada
            / abs(media_filtrada)
        )
    else:
        cv_filtrado = float("inf")

    homologada = cv_filtrado < CV_LIMITE

    return {
        "dados_brutos": tempos,
        "dados_filtrados": tempos_filtrados,

        "media_bruta": media_bruta,
        "sigma_bruta": sigma_bruta,
        "cv_bruto": cv_bruto,

        "p5": p5,
        "p95": p95,

        "media_filtrada": media_filtrada,
        "sigma_filtrada": sigma_filtrada,
        "cv_filtrado": cv_filtrado,

        "homologada": homologada
    }


# ============================================================
# GRÁFICOS
# ============================================================

def gerar_graficos(
    nome_arquivo,
    nome_funcao,
    resultados
):

    dados_brutos = resultados["dados_brutos"]
    dados_filtrados = resultados["dados_filtrados"]

    p5 = resultados["p5"]
    p95 = resultados["p95"]

    media_filtrada = resultados["media_filtrada"]

    # ========================================================
    # 1. GRÁFICO DE DISPERSÃO
    # ========================================================

    plt.figure(figsize=(12, 5))

    indices = np.arange(
        1,
        len(dados_brutos) + 1
    )

    plt.scatter(
        indices,
        dados_brutos,
        s=3,
        alpha=0.5
    )

    plt.axhline(
        p5,
        linestyle="--",
        label=f"P5 = {p5:.4f} ns"
    )

    plt.axhline(
        p95,
        linestyle="--",
        label=f"P95 = {p95:.4f} ns"
    )

    plt.axhline(
        media_filtrada,
        linestyle="-",
        label=f"μfil = {media_filtrada:.4f} ns"
    )

    plt.title(
        f"Dispersão das medições — {nome_funcao}"
    )

    plt.xlabel("Índice da medição")
    plt.ylabel("Tempo por execução (ns)")

    plt.legend()
    plt.grid(alpha=0.3)

    plt.tight_layout()

    caminho = (
        PASTA_GRAFICOS
        / f"{nome_arquivo}_dispersao.png"
    )

    plt.savefig(
        caminho,
        dpi=300
    )

    plt.close()

    # ========================================================
    # 2. HISTOGRAMA BRUTO
    # ========================================================

    plt.figure(figsize=(10, 5))

    plt.hist(
        dados_brutos,
        bins=50
    )

    plt.axvline(
        p5,
        linestyle="--",
        label=f"P5 = {p5:.4f} ns"
    )

    plt.axvline(
        p95,
        linestyle="--",
        label=f"P95 = {p95:.4f} ns"
    )

    plt.title(
        f"Histograma bruto — {nome_funcao}"
    )

    plt.xlabel("Tempo por execução (ns)")
    plt.ylabel("Frequência")

    plt.legend()
    plt.grid(alpha=0.3)

    plt.tight_layout()

    caminho = (
        PASTA_GRAFICOS
        / f"{nome_arquivo}_histograma_bruto.png"
    )

    plt.savefig(
        caminho,
        dpi=300
    )

    plt.close()

    # ========================================================
    # 3. HISTOGRAMA FILTRADO
    # ========================================================

    plt.figure(figsize=(10, 5))

    plt.hist(
        dados_filtrados,
        bins=50
    )

    plt.axvline(
        p5,
        linestyle="--",
        label=f"P5 = {p5:.4f} ns"
    )

    plt.axvline(
        p95,
        linestyle="--",
        label=f"P95 = {p95:.4f} ns"
    )

    plt.axvline(
        media_filtrada,
        linestyle="-",
        label=f"μfil = {media_filtrada:.4f} ns"
    )

    plt.title(
        f"Histograma filtrado — {nome_funcao}"
    )

    plt.xlabel("Tempo por execução (ns)")
    plt.ylabel("Frequência")

    plt.legend()
    plt.grid(alpha=0.3)

    plt.tight_layout()

    caminho = (
        PASTA_GRAFICOS
        / f"{nome_arquivo}_histograma_filtrado.png"
    )

    plt.savefig(
        caminho,
        dpi=300
    )

    plt.close()


# ============================================================
# INÍCIO DO EXPERIMENTO
# ============================================================

print("=" * 100)
print("CALIBRAÇÃO DE FUNÇÕES OPACAS — F")
print("=" * 100)

print()
print("Parâmetros:")
print(f"n = {N_AMOSTRAS}")
print(f"r = {R_GLOBAL}")
print(
    f"Execuções internas por medição = "
    f"{N_EXECUCOES}"
)
print("Filtro = Percentis P5/P95")
print(
    "Critério de homologação = CVfil < 0,15"
)
print()


# ============================================================
# CONTROLE T0
# ============================================================

print("=" * 100)
print("MEDINDO CONTROLE T0")
print("=" * 100)

dados_t0 = medir_controle()

estat_t0 = calcular_estatisticas(
    dados_t0
)

print()
print("=" * 100)
print("CONTROLE T0")
print("=" * 100)

print(
    f"Quantidade bruta:    "
    f"{len(dados_t0)}"
)

print(
    f"Quantidade filtrada: "
    f"{len(estat_t0['dados_filtrados'])}"
)

print()
print(
    f"μbruta T0:  "
    f"{estat_t0['media_bruta']:.6f} ns"
)

print(
    f"σbruta T0:  "
    f"{estat_t0['sigma_bruta']:.6f} ns"
)

print(
    f"CVbruto T0: "
    f"{estat_t0['cv_bruto']:.6f}"
)

print()
print(
    f"P5  T0 = "
    f"{estat_t0['p5']:.6f} ns"
)

print(
    f"P95 T0 = "
    f"{estat_t0['p95']:.6f} ns"
)

print()
print(
    f"μfil T0:  "
    f"{estat_t0['media_filtrada']:.6f} ns"
)

print(
    f"σfil T0:  "
    f"{estat_t0['sigma_filtrada']:.6f} ns"
)

print(
    f"CVfil T0: "
    f"{estat_t0['cv_filtrado']:.6f}"
)


# ============================================================
# MEDIÇÃO DAS DUAS FUNÇÕES
# ============================================================

resultados = []

for nome_funcao, funcao in FUNCOES:

    print()
    print("=" * 100)
    print(
        f"MEDINDO: {nome_funcao}"
    )
    print("=" * 100)

    dados = medir_funcao(
        funcao
    )

    estat = calcular_estatisticas(
        dados
    )

    resultados.append(
        (
            nome_funcao,
            estat
        )
    )

    print()
    print("=" * 100)
    print(nome_funcao)
    print("=" * 100)

    print(
        f"Quantidade bruta:    "
        f"{len(dados)}"
    )

    print(
        f"Quantidade filtrada: "
        f"{len(estat['dados_filtrados'])}"
    )

    print()
    print(
        f"μbruta  = "
        f"{estat['media_bruta']:.6f} ns"
    )

    print(
        f"σbruta  = "
        f"{estat['sigma_bruta']:.6f} ns"
    )

    print(
        f"CVbruto = "
        f"{estat['cv_bruto']:.6f}"
    )

    print()
    print(
        f"P5  = "
        f"{estat['p5']:.6f} ns"
    )

    print(
        f"P95 = "
        f"{estat['p95']:.6f} ns"
    )

    print()
    print(
        f"μfil  = "
        f"{estat['media_filtrada']:.6f} ns"
    )

    print(
        f"σfil  = "
        f"{estat['sigma_filtrada']:.6f} ns"
    )

    print(
        f"CVfil = "
        f"{estat['cv_filtrado']:.6f}"
    )

    if estat["homologada"]:
        print("STATUS = HOMOLOGADA")
    else:
        print("STATUS = REPROVADA")


# ============================================================
# TABELA FINAL
# ============================================================

print()
print("=" * 115)
print("TABELA FINAL — CALIBRAÇÃO F")
print("=" * 115)

print(
    f"{'Função':42}"
    f"{'μbruta':>13}"
    f"{'σbruta':>13}"
    f"{'CVbruto':>13}"
    f"{'μfil (τf)':>15}"
    f"{'σfil':>13}"
    f"{'CVfil':>13}"
    f"{'Status':>15}"
)

print("-" * 115)

for nome_funcao, estat in resultados:

    status = (
        "HOMOLOGADA"
        if estat["homologada"]
        else
        "REPROVADA"
    )

    print(
        f"{nome_funcao:42}"
        f"{estat['media_bruta']:13.6f}"
        f"{estat['sigma_bruta']:13.6f}"
        f"{estat['cv_bruto']:13.6f}"
        f"{estat['media_filtrada']:15.6f}"
        f"{estat['sigma_filtrada']:13.6f}"
        f"{estat['cv_filtrado']:13.6f}"
        f"{status:>15}"
    )


# ============================================================
# GRÁFICOS
# ============================================================

# Uma função representa graficamente a macroprimitiva F.
# Função escolhida: calcular_media(lista)

nome_representante, estat_representante = resultados[0]

gerar_graficos(
    "F_representante_calcular_media",
    nome_representante,
    estat_representante
)


# ============================================================
# FINALIZAÇÃO
# ============================================================

print()
print("=" * 100)
print("GRÁFICOS GERADOS")
print("=" * 100)

print(
    "Macroprimitiva F — "
    "função representativa: "
    "calcular_media(lista)"
)

print()

print(
    "- F_representante_calcular_media_dispersao.png"
)

print(
    "- F_representante_calcular_media_histograma_bruto.png"
)

print(
    "- F_representante_calcular_media_histograma_filtrado.png"
)

print()
print(
    f"Gráficos salvos em: "
    f"{PASTA_GRAFICOS}"
)

print("=" * 100)
print("EXPERIMENTO FINALIZADO")
print("=" * 100)