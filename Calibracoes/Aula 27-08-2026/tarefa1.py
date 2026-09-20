 
# achar o tempo médio das primitivas FOCA
from time import time as time
 
lista_n = [1000,10000,100000]
t = []
 
for n in lista_n:
 tic = time()
 for i in range(n):
  x=1
 toc = time() 
 t.append(toc-tic)
 print(f"f(n)= {n} tempo : {t[-1]}")
 