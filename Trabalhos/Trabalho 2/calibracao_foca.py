# -*- coding: utf-8 -*-
"""
Calibração Empírica F.O.C.A. — tau_a, tau_c, tau_o (+ F opcional)
Engenharia de Programas 2026.2 — Prof. Diego Frias

METODOLOGIA (conforme "Filtragem de Outliers em Engenharia de Programas"):

Para cada primitiva:
  1. Coleta-se uma amostra BRUTA de n medições individuais (tic; primitiva; tac).
  2. Calcula-se mu_bruta, sigma_bruta, CV_bruto sobre essa amostra crua.
  3. Aplica-se o filtro de PERCENTIL (Técnica 2 do material): mantém-se apenas
     as medições entre o percentil 5 e o percentil 95, descartando as caudas
     -- imune à magnitude dos outliers (ao contrário do corte por
     média +/- n*sigma, que é corrompido por eles).
  4. Recalcula-se mu_fil, sigma_fil, CV_fil sobre a amostra filtrada.
  5. O tempo de CONTROLE (T0 -- overhead de chamar a função e medir o tempo,
     sem nenhuma primitiva real dentro) é medido e filtrado da MESMA forma,
     e subtraído: tau = mu_fil(primitiva) - mu_fil(controle).
     Isso isola o custo da primitiva em si, removendo o custo fixo de
     instrumentação (chamada de função + tic/tac), igual ao que o script
     das colegas já fazia com T0, mas agora com filtragem robusta.

O processo é repetido r vezes (repetições globais) para checar reprodutibilidade.

IMPORTANTE -- BATCHING (lote) além da filtragem por percentil:
A resolução real do temporizador do sistema (medida empiricamente) costuma
ficar na casa de dezenas a centenas de nanossegundos, MESMO quando
time.perf_counter() anuncia resolução de 1ns. Como várias primitivas (ex.:
comparações, somas) custam poucos nanossegundos, uma medição de disparo
único (tic; primitiva; tac) fica abaixo do "tique" do relógio -- e nenhuma
filtragem de outliers resolve isso, pois o problema não são picos
esporádicos, e sim quantização do próprio instrumento de medição.
A correção é medir um LOTE de K execuções da primitiva por amostra (tic;
laço de K vezes; tac), dividindo o tempo por K. Isso eleva a duração
medida bem acima da resolução do relógio. A filtragem por percentil
continua sendo aplicada depois, sobre essas amostras já em lote, para
remover os picos causados por Scheduler/GC/Throttling (conforme a
apresentação). As duas técnicas resolvem problemas DIFERENTES e por isso
são usadas em conjunto.
"""

import time
import math
import platform
import statistics
import csv
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# =========================================================================
# 1. PARÂMETROS METODOLÓGICOS (Seção 2 do template)
# =========================================================================
N_SAMPLES = 3000     # amostra interna (n): medições (em lote) individuais por primitiva
R_GLOBAL = 3          # repetições globais (r): rodadas independentes p/ reprodutibilidade
P_LOW, P_HIGH = 5, 95  # percentis de corte (Técnica 2: Corte Robusto por Percentis)
CV_LIMIT = 0.15
TARGET_BATCH_NS = 3000.0   # duração mínima alvo de cada amostra em lote (ns), bem acima
                            # da resolução real do relógio (medida em ~150-200ns nesta VM)
MAX_K = 200_000             # trava de segurança para o tamanho do lote

OUT_DIR = "outputs"
PLOT_DIR = "plots"


# =========================================================================
# 2. VARIÁVEIS DE APOIO E DEFINIÇÃO DAS PRIMITIVAS
# =========================================================================
class _Vars:
    pass


v = _Vars()
v.i1, v.f1, v.b1 = 0, 0.0, False

a_int, b_int = 7, 13
a_float, b_float = 3.1415, 2.7182
lista_apoio = [1, 2, 3, 4, 5]


def _noop():
    """Controle T0: mesma sobrecarga de chamada de função, sem primitiva real."""
    pass


# ---- 4.1 Custo de Atribuições (tau_a) -----------------------------------
TAU_A = [
    ("var int <- cte int (a = 5)",        lambda: setattr(v, "i1", 5)),
    ("var float <- cte float",            lambda: setattr(v, "f1", 3.14)),
    ("var bool <- cte bool",              lambda: setattr(v, "b1", True)),
    ("var int <- var int (a = b)",        lambda: setattr(v, "i1", b_int)),
    ("var float <- var float",            lambda: setattr(v, "f1", b_float)),
]

# ---- 4.2 Custo de Comparações (tau_c) ------------------------------------
TAU_C = [
    ("Igualdade: cte int == cte int",      lambda: 5 == 5),
    ("Igualdade: var int == cte int",      lambda: a_int == 5),
    ("Igualdade: var int == var int",      lambda: a_int == b_int),
    ("Igualdade: var float == var float",  lambda: a_float == b_float),
    ("Desigualdade: var int != var int",   lambda: a_int != b_int),
    ("Relacional: var int > var int",      lambda: a_int > b_int),
    ("Relacional: var float < cte float",  lambda: a_float < 3.14),
]

# ---- 4.3 Custo de Operações Matemáticas (tau_o) --------------------------
TAU_O = [
    ("Soma Int: var int + cte int",              lambda: a_int + 5),
    ("Soma Int: var int + var int",               lambda: a_int + b_int),
    ("Soma Float: var float + var float",         lambda: a_float + b_float),
    ("Subtração Int: var int - var int",          lambda: a_int - b_int),
    ("Multiplicação Int: var int * var int",      lambda: a_int * b_int),
    ("Multiplicação Float: var float * var float",lambda: a_float * b_float),
    ("Divisão Float: var float / var float",      lambda: a_float / b_float),
    ("Divisão Int (Piso): var int // var int",    lambda: a_int // b_int),
    ("Módulo (Resto): var int % var int",         lambda: a_int % b_int),
]

# ---- 4.4 Custo de Funções Opacas (F) — opcional, bônus -------------------
TAU_F = [
    ("math.sqrt(var float)",  lambda: math.sqrt(a_float)),
    ("abs(var int)",          lambda: abs(-a_int)),
    ("len(lista_apoio)",      lambda: len(lista_apoio)),
    ("round(var float, 2)",   lambda: round(a_float, 2)),
]

TODAS_MATRIZES = [
    ("tau_a", "Custo de Atribuições", TAU_A),
    ("tau_c", "Custo de Comparações", TAU_C),
    ("tau_o", "Custo de Operações Matemáticas", TAU_O),
    ("F", "Custo de Funções Opacas (bônus)", TAU_F),
]


# =========================================================================
# 3. MEDIÇÃO + FILTRAGEM POR PERCENTIL
# =========================================================================
def calibrar_k(func, target_ns=TARGET_BATCH_NS):
    """Descobre o tamanho de lote K necessário para que uma janela de
    medição (K execuções seguidas de func) dure pelo menos target_ns."""
    k = 1
    while True:
        t0 = time.perf_counter()
        for _ in range(k):
            func()
        dt_ns = (time.perf_counter() - t0) * 1e9
        if dt_ns >= target_ns or k >= MAX_K:
            k_ideal = max(1, int(k * (target_ns / dt_ns) * 1.2)) if dt_ns > 0 else k
            return min(k_ideal, MAX_K)
        k *= 2


def medir_raw(func, n=N_SAMPLES, k=None):
    """Coleta n medições em LOTE de K execuções de func (tic; K execuções; tac),
    dividindo por K -- resultado em segundos por chamada individual."""
    if k is None:
        k = calibrar_k(func)
    tempos = np.empty(n)
    for i in range(n):
        tic = time.perf_counter()
        for _ in range(k):
            func()
        tac = time.perf_counter()
        tempos[i] = (tac - tic) / k
    return tempos, k


def filtrar_percentil(tempos, p_low=P_LOW, p_high=P_HIGH):
    lo, hi = np.percentile(tempos, [p_low, p_high])
    return tempos[(tempos >= lo) & (tempos <= hi)]


def estatisticas(arr):
    mu = float(np.mean(arr))
    sigma = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    cv = sigma / mu if mu > 0 else float("inf")
    return mu, sigma, cv


def calibrar_primitiva(func, controle_fil_mu, n=N_SAMPLES):
    raw, k_usado = medir_raw(func, n)
    mu_bruta, sigma_bruta, cv_bruto = estatisticas(raw)

    filt = filtrar_percentil(raw)
    mu_fil_raw, sigma_fil, _ = estatisticas(filt)

    tau = mu_fil_raw - controle_fil_mu       # subtrai overhead de instrumentação
    cv_fil = sigma_fil / tau if tau > 0 else float("inf")

    return {
        "raw": raw, "filt": filt, "k": k_usado,
        "mu_bruta": mu_bruta, "sigma_bruta": sigma_bruta, "cv_bruto": cv_bruto,
        "mu_fil": tau, "sigma_fil": sigma_fil, "cv_fil": cv_fil,
    }


def medir_controle(n=N_SAMPLES):
    raw, k_usado = medir_raw(_noop, n)
    filt = filtrar_percentil(raw)
    mu_fil, _, _ = estatisticas(filt)
    return mu_fil, raw, filt, k_usado


# =========================================================================
# 4. AMBIENTE
# =========================================================================
def coletar_specs_ambiente():
    specs = {
        "sistema_operacional": f"{platform.system()} {platform.release()} ({platform.version()})",
        "linguagem": f"Python {platform.python_version()} ({platform.python_implementation()})",
        "arquitetura": platform.machine(),
        "processador_platform": platform.processor(),
    }
    try:
        with open("/proc/cpuinfo") as f:
            cpuinfo = f.read()
        modelo = [l for l in cpuinfo.splitlines() if l.startswith("model name")]
        specs["cpu_modelo"] = modelo[0].split(":", 1)[1].strip() if modelo else specs["processador_platform"]
        specs["cpu_nucleos_logicos"] = cpuinfo.count("processor\t:")
        mhz = [l for l in cpuinfo.splitlines() if l.startswith("cpu MHz")]
        specs["cpu_freq_atual_mhz"] = mhz[0].split(":", 1)[1].strip() if mhz else "N/D"
    except FileNotFoundError:
        specs["cpu_modelo"] = specs["processador_platform"]
        specs["cpu_nucleos_logicos"] = os.cpu_count()
        specs["cpu_freq_atual_mhz"] = "N/D (rode 'wmic cpu get MaxClockSpeed' no Windows)"
    try:
        with open("/proc/meminfo") as f:
            meminfo = f.read()
        total_kb = int([l for l in meminfo.splitlines() if l.startswith("MemTotal")][0].split()[1])
        specs["ram_total_gb"] = round(total_kb / (1024 ** 2), 2)
    except FileNotFoundError:
        specs["ram_total_gb"] = "N/D"
    return specs


# =========================================================================
# 5. GRÁFICOS (painel de 3 por macroprimitiva)
# =========================================================================
def gerar_painel(nome_macro, label_op, raw, filt, tau_ns, out_dir=PLOT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    raw_ns = raw * 1e9
    filt_ns = filt * 1e9
    lo, hi = np.percentile(raw_ns, [P_LOW, P_HIGH])

    # Gráfico 1: Dispersão temporizada (iteração x tempo)
    plt.figure(figsize=(8, 4.5))
    plt.plot(raw_ns, ".", markersize=2, alpha=0.5, color="#1f6f5c")
    plt.axhline(lo, color="orange", linestyle="--", linewidth=1, label=f"P{P_LOW}")
    plt.axhline(hi, color="red", linestyle="--", linewidth=1, label=f"P{P_HIGH}")
    plt.xlabel("Iteração (r)")
    plt.ylabel("Tempo (ns)")
    plt.title(f"[{nome_macro}] Dispersão Temporizada — {label_op}")
    plt.legend()
    plt.tight_layout()
    fname1 = f"{out_dir}/{nome_macro}_1_dispersao.png"
    plt.savefig(fname1, dpi=150)
    plt.close()

    # Gráfico 2: Histograma bruto
    plt.figure(figsize=(8, 4.5))
    plt.hist(raw_ns, bins=50, color="#c96a3a", alpha=0.85)
    plt.axvline(lo, color="orange", linestyle="--", linewidth=1.5, label=f"P{P_LOW}")
    plt.axvline(hi, color="red", linestyle="--", linewidth=1.5, label=f"P{P_HIGH}")
    plt.xlabel("Tempo (ns)")
    plt.ylabel("Frequência")
    plt.title(f"[{nome_macro}] Histograma de Dados Brutos — {label_op}")
    plt.legend()
    plt.tight_layout()
    fname2 = f"{out_dir}/{nome_macro}_2_hist_bruto.png"
    plt.savefig(fname2, dpi=150)
    plt.close()

    # Gráfico 3: Histograma pós-filtragem
    plt.figure(figsize=(8, 4.5))
    plt.hist(filt_ns, bins=40, color="#1f6f5c", alpha=0.85)
    plt.xlabel("Tempo (ns)")
    plt.ylabel("Frequência")
    plt.title(f"[{nome_macro}] Histograma Pós-Filtragem (P{P_LOW}-P{P_HIGH}) — {label_op}")
    plt.tight_layout()
    fname3 = f"{out_dir}/{nome_macro}_3_hist_filtrado.png"
    plt.savefig(fname3, dpi=150)
    plt.close()

    return fname1, fname2, fname3


# =========================================================================
# 6. LATEX HELPER — gera linha pronta pra colar no template do Overleaf
# =========================================================================
def fmt_ns(segundos):
    return f"{segundos * 1e9:.2f} ns"


def fmt_pct(x):
    return f"{x * 100:.2f}\\%"


def linha_latex(label, r):
    return (f"{label} & {fmt_ns(r['mu_bruta'])} & {fmt_ns(r['sigma_bruta'])} & "
            f"{fmt_pct(r['cv_bruto'])} & {fmt_ns(r['mu_fil'])} & {fmt_ns(r['sigma_fil'])} & "
            f"{fmt_pct(r['cv_fil'])} \\\\")


# =========================================================================
# MAIN
# =========================================================================
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PLOT_DIR, exist_ok=True)

    print("=" * 70)
    print("CALIBRAÇÃO EMPÍRICA F.O.C.A. — tau_a, tau_c, tau_o, F")
    print(f"n (amostra interna) = {N_SAMPLES} | r (repetições globais) = {R_GLOBAL}")
    print(f"Filtragem: percentil [{P_LOW}, {P_HIGH}]  |  Limite CV = {CV_LIMIT}")
    print("=" * 70)

    specs = coletar_specs_ambiente()
    print("\nAmbiente detectado:")
    for k, val in specs.items():
        print(f"   {k}: {val}")

    resultados_globais = {g: [] for g, _, _ in TODAS_MATRIZES}
    csv_rows = []
    latex_rows = {g: [] for g, _, _ in TODAS_MATRIZES}
    reprovados = []

    for rodada in range(1, R_GLOBAL + 1):
        print(f"\n--- Repetição global {rodada}/{R_GLOBAL} ---")
        controle_mu, controle_raw, controle_filt, controle_k = medir_controle()
        print(f"   T0 (controle) filtrado: {fmt_ns(controle_mu)}  (K={controle_k})")

        for grupo, titulo, primitivas in TODAS_MATRIZES:
            for label, func in primitivas:
                r = calibrar_primitiva(func, controle_mu)
                status = "OK" if r["cv_fil"] < CV_LIMIT else "REPROVADO"
                if status == "REPROVADO":
                    reprovados.append((rodada, grupo, label, r["cv_fil"]))
                print(f"   [{grupo:6s}] {label:42s} tau={fmt_ns(r['mu_fil']):>12s} "
                      f"CVfil={r['cv_fil']*100:6.2f}%  K={r['k']:<6d} {status}")

                csv_rows.append({
                    "rodada": rodada, "grupo": grupo, "primitiva": label,
                    "mu_bruta_ns": r["mu_bruta"] * 1e9, "sigma_bruta_ns": r["sigma_bruta"] * 1e9,
                    "cv_bruto_pct": r["cv_bruto"] * 100,
                    "mu_fil_ns": r["mu_fil"] * 1e9, "sigma_fil_ns": r["sigma_fil"] * 1e9,
                    "cv_fil_pct": r["cv_fil"] * 100, "status": status,
                })

                if rodada == R_GLOBAL:  # usa a última rodada como oficial p/ LaTeX e gráficos
                    latex_rows[grupo].append(linha_latex(label, r))
                    resultados_globais[grupo].append((label, r))

    # ---- Gráficos: um painel por macroprimitiva, usando uma linha representativa ----
    print("\nGerando painéis gráficos (1 representante por macroprimitiva)...")
    representantes = {
        "tau_a": "var int <- var int (a = b)",
        "tau_c": "Igualdade: var int == var int",
        "tau_o": "Soma Int: var int + var int",
        "F": "math.sqrt(var float)",
    }
    for grupo, label_alvo in representantes.items():
        for label, r in resultados_globais[grupo]:
            if label == label_alvo:
                gerar_painel(grupo, label, r["raw"], r["filt"], r["mu_fil"])
                break

    # ---- Salvar CSV completo ----
    with open(f"{OUT_DIR}/matriz_completa.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)

    # ---- Salvar linhas LaTeX prontas (última rodada = oficial) ----
    with open(f"{OUT_DIR}/linhas_latex.txt", "w", encoding="utf-8") as f:
        for grupo, titulo, _ in TODAS_MATRIZES:
            f.write(f"\n% ===== {titulo} ({grupo}) =====\n")
            for linha in latex_rows[grupo]:
                f.write(linha + "\n")

    # ---- Salvar specs do ambiente ----
    with open(f"{OUT_DIR}/specs_ambiente.json", "w", encoding="utf-8") as f:
        json.dump(specs, f, indent=2, ensure_ascii=False)

    # ---- Benchmark: primitiva mais lenta homologada (Questão 5) ----
    homologadas = [(g, l, r) for g, l, r in
                   [(g, l, r) for g in resultados_globais for l, r in resultados_globais[g]]
                   if r["cv_fil"] < CV_LIMIT]
    if homologadas:
        pior = max(homologadas, key=lambda x: x[2]["mu_fil"])
        g_pior, l_pior, r_pior = pior
        tau_pior = r_pior["mu_fil"]
        ips = 1 / tau_pior if tau_pior > 0 else float("inf")
        print("\n" + "=" * 70)
        print(f"PIOR CASO HOMOLOGADO: [{g_pior}] {l_pior}")
        print(f"tau_pior = {fmt_ns(tau_pior)}")
        print(f"Benchmark: 1/tau_pior = {ips:,.0f} instruções/segundo "
              f"(~{ips/1e6:.2f} milhões de instruções/segundo, MIPS)")
        print("=" * 70)
        with open(f"{OUT_DIR}/benchmark_pior_caso.json", "w", encoding="utf-8") as f:
            json.dump({"grupo": g_pior, "primitiva": l_pior, "tau_segundos": tau_pior,
                       "ips": ips}, f, indent=2, ensure_ascii=False)

    if reprovados:
        print(f"\n⚠️  {len(reprovados)} caso(s) REPROVADO(S) (CVfil >= 15%) em alguma rodada:")
        for rodada, grupo, label, cv in reprovados:
            print(f"   Rodada {rodada} [{grupo}] {label}: CVfil={cv*100:.2f}%")
    else:
        print("\n✅ Todas as primitivas, em todas as rodadas, homologadas (CVfil < 15%).")

    print(f"\nArquivos gerados em '{OUT_DIR}/' e gráficos em '{PLOT_DIR}/'.")


if __name__ == "__main__":
    main()