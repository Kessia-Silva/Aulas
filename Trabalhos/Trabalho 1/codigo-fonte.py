import numpy as np

n = 100000
valores = np.arange(n)

soma = 0

for i in range(n):
    soma = soma + valores[i]

print(soma)