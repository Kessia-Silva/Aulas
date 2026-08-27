 
# achar o tempo médio das primitivas FOCA
from time import time as time
from matplotlib import pyplot as plt
 
R = 100
 
lista_n = [1000,10000,100000]
t = []
 
for n in lista_n:
  tt = []
  for r in range(R):
   tic = time()
   for i in range(n):
    x=1
 
   toc = time()
   tt.append(toc-tic)
 
  t.append(tt)
  plt.plot(tt)
  plt.title(f"n={n}")
  plt.savefig(f"tempos.n{n}.png")
  plt.show()
 
 