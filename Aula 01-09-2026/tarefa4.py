#FOCAlaço = (0, n+1, n+1, n + 5)
# FOCA = (0, n+1, n+1, n+5 +n)

from time import time
import numpy as np

R = 100
TOU_A = []
n = 100000

for r in range(R):
    t=0
    for i in range(n):
        tic = time()
        x = 1 
        tac = time()
        t += tac - tic
    TOU_A.append(t/n)
    #controle
    media = np.mean(TOU_A)
    sigma = np.std(TOU_A)
    cv = sigma/media
    if cv < 0.15:
        break
