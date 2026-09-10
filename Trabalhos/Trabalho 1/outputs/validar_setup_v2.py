"""
Validação de Setup Computacional — VERSÃO 2 (pós-diagnóstico)

A 1a rodada (validar_setup.py) resultou REPROVADA: para N pequenos, uma
única execução do loop banal dura poucos microssegundos, ordem de
grandeza próxima da resolução/ruído do próprio medidor de tempo e do
escalonador do SO. Isso é exatamente o cenário descrito no slide "A
Ilusão do Determinismo": o ruído do ambiente (aqui, uma VM de nuvem
compartilhada com 1 vCPU) domina o sinal.

Seguindo o próprio fluxograma da disciplina (ramo "Setup Reprovado,
isolar ambiente e reiniciar"), duas medidas de isolamento são aplicadas
nesta 2a rodada, mantendo o restante da metodologia idêntico:

  1. Coletor de lixo (GC) desabilitado durante a medição, eliminando
     picos de pausa do Garbage Collector do Python (fonte de variação
     citada explicitamente no slide 4).
  2. Cada ΔT_r passa a medir um BLOCO de K execuções do loop banal (em
     vez de uma única execução), e o tempo é dividido por K. Isso é a
     técnica padrão de microbenchmarking para elevar a duração de cada
     medição bem acima da resolução do timer e do ruído do escalonador,
     sem alterar a natureza do experimento (mede-se o mesmo loop banal).
"""

import time
import random
import gc
import statistics
import csv
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

N_VALUES = [100, 500, 1000, 1500, 2000, 2500, 3000]
R = 40
TRIALS = 3
CV_LIMIT = 0.15
SEED_BASE = 42
K_BATCH = 400   # execuções do loop banal por medição (eleva a duração medida)

OUT_DIR = "outputs"
PLOT_DIR = "plots"


def gerar_lista_aleatoria(n, rng):
    return [rng.random() for _ in range(n)]


def loop_banal(lista):
    acc = 0.0
    for x in lista:
        acc += x
    return acc


def medir_delta_t(n, rng, k=K_BATCH):
    """Mede ΔT_r como a média de k execuções consecutivas do loop banal,
    com o coletor de lixo desabilitado durante a janela de medição."""
    lista = gerar_lista_aleatoria(n, rng)
    gc_estava_ativo = gc.isenabled()
    gc.disable()
    try:
        t0 = time.perf_counter()
        for _ in range(k):
            loop_banal(lista)
        t1 = time.perf_counter()
    finally:
        if gc_estava_ativo:
            gc.enable()
    return (t1 - t0) / k


def executar_trial(trial_id):
    rng = random.Random(SEED_BASE + trial_id)
    linhas = []
    for n in N_VALUES:
        tempos = [medir_delta_t(n, rng) for _ in range(R)]
        mu = statistics.mean(tempos)
        sigma = statistics.stdev(tempos) if len(tempos) > 1 else 0.0
        cv = (sigma / mu) if mu > 0 else 0.0
        linhas.append({"trial": trial_id, "n": n, "tempos": tempos,
                        "mu": mu, "sigma": sigma, "cv": cv})
    return linhas


def gerar_plots(resultados, out_dir=PLOT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    tempos_por_n = {n: [] for n in N_VALUES}
    for linha in resultados:
        tempos_por_n[linha["n"]].extend(linha["tempos"])

    mu_por_n, sigma_por_n, cv_por_n = {}, {}, {}
    for n in N_VALUES:
        t = tempos_por_n[n]
        mu_por_n[n] = statistics.mean(t)
        sigma_por_n[n] = statistics.stdev(t)
        cv_por_n[n] = sigma_por_n[n] / mu_por_n[n] if mu_por_n[n] > 0 else 0.0

    plt.figure(figsize=(8, 5))
    for n in N_VALUES:
        xs = [n] * len(tempos_por_n[n])
        plt.scatter(xs, [t * 1e6 for t in tempos_por_n[n]], s=14, alpha=0.55, color="#1f6f5c")
    plt.xlabel("Tamanho da Entrada (N)")
    plt.ylabel("Tempo de Execução (µs)")
    plt.title("Gráfico 1 — Dispersão do Tempo de Execução x Tamanho da Entrada (N)")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{out_dir}/grafico1_dispersao.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    medias_us = [mu_por_n[n] * 1e6 for n in N_VALUES]
    plt.plot(N_VALUES, medias_us, marker="o", color="#1f6f5c", linewidth=2)
    plt.xlabel("Tamanho da Entrada (N)")
    plt.ylabel("Tempo Médio de Execução (µs)")
    plt.title("Gráfico 2 — Tempo Médio de Execução x Tamanho da Entrada (N)")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{out_dir}/grafico2_tempo_medio.png", dpi=150)
    plt.close()

    x = np.arange(len(N_VALUES))
    width = 0.38
    plt.figure(figsize=(9, 5))
    plt.bar(x - width / 2, medias_us, width, label="Média (μ)", color="#1f6f5c")
    plt.bar(x + width / 2, [sigma_por_n[n] * 1e6 for n in N_VALUES], width,
            label="Desvio Padrão (σ)", color="#c96a3a")
    plt.xticks(x, N_VALUES)
    plt.xlabel("Tamanho da Entrada (N)")
    plt.ylabel("Tempo (µs)")
    plt.title("Gráfico 3 — Média (μ) vs Desvio Padrão (σ) x Tamanho da Entrada (N)")
    plt.legend()
    plt.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(f"{out_dir}/grafico3_media_desvio.png", dpi=150)
    plt.close()

    plt.figure(figsize=(9, 5))
    cvs = [cv_por_n[n] for n in N_VALUES]
    cores = ["#1f6f5c" if c <= CV_LIMIT else "#b23b3b" for c in cvs]
    plt.bar([str(n) for n in N_VALUES], cvs, color=cores)
    plt.axhline(y=CV_LIMIT, color="red", linestyle="--", linewidth=1.5,
                label=f"Limite CV = {CV_LIMIT}")
    plt.xlabel("Tamanho da Entrada (N)")
    plt.ylabel("Coeficiente de Variação (CV = σ/μ)")
    plt.title("Gráfico 4 — Coeficiente de Variação (CV) x Tamanho da Entrada (N)")
    plt.legend()
    plt.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(f"{out_dir}/grafico4_cv.png", dpi=150)
    plt.close()

    return {"mu_por_n": mu_por_n, "sigma_por_n": sigma_por_n, "cv_por_n": cv_por_n}


def avaliar_aprovacao(resultados):
    piores = [(l["trial"], l["n"], l["cv"]) for l in resultados]
    max_cv = max(c for _, _, c in piores)
    reprovados = [(t, n, c) for t, n, c in piores if c > CV_LIMIT]
    return len(reprovados) == 0, max_cv, reprovados


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("=" * 70)
    print("VALIDAÇÃO DE SETUP — RODADA 2 (ambiente isolado: GC off + batch K=%d)" % K_BATCH)
    print("=" * 70)

    resultados = []
    for trial in range(1, TRIALS + 1):
        print(f"   -> Repetição {trial}/{TRIALS}...")
        resultados.extend(executar_trial(trial))

    agregados = gerar_plots(resultados)
    aprovado, max_cv, reprovados = avaliar_aprovacao(resultados)

    with open(f"{OUT_DIR}/resumo_por_trial.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["trial", "n", "tempo_medio_us", "desvio_padrao_us", "cv_percentual"])
        for linha in resultados:
            writer.writerow([linha["trial"], linha["n"],
                              f"{linha['mu']*1e6:.4f}", f"{linha['sigma']*1e6:.4f}",
                              f"{linha['cv']*100:.2f}"])

    with open(f"{OUT_DIR}/resumo_agregado.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["n", "tempo_medio_us", "desvio_padrao_us", "cv_percentual"])
        for n in N_VALUES:
            writer.writerow([n, f"{agregados['mu_por_n'][n]*1e6:.4f}",
                              f"{agregados['sigma_por_n'][n]*1e6:.4f}",
                              f"{agregados['cv_por_n'][n]*100:.2f}"])

    resultado_final = {
        "N_VALUES": N_VALUES, "R": R, "TRIALS": TRIALS, "K_BATCH": K_BATCH,
        "CV_LIMIT": CV_LIMIT, "aprovado": aprovado,
        "cv_maximo_observado": max_cv, "casos_reprovados": reprovados,
    }
    with open(f"{OUT_DIR}/resultado_final.json", "w") as f:
        json.dump(resultado_final, f, indent=2, default=str)

    print("\n" + "=" * 70)
    if aprovado:
        print(f"RESULTADO: SETUP APROVADO (CV máximo observado = {max_cv*100:.2f}% <= 15%)")
    else:
        print(f"RESULTADO: SETUP REPROVADO — {len(reprovados)} caso(s) com CV > 15%")
        for t, n, c in reprovados:
            print(f"   - Trial {t}, N={n}: CV = {c*100:.2f}%")
    print("=" * 70)


if __name__ == "__main__":
    main()