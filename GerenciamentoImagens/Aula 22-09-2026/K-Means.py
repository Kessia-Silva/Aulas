import time
import matplotlib.pyplot as plt
import cv2
import numpy as np

img = cv2.imread('gato.png')
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

n, m, c = img.shape
print(f'linhas: {n} colunas: {m} canais: {c}')

# Parte de inicialização:
faixa = []
plano = []

for cor in range(c):
    plano.append(img[:, :, cor])
    faixa.append(plano[-1].flatten())
    plt.scatter(np.arange(len(faixa[-1])), faixa[-1])

K = 2
centroid = []
n_pixels = len(faixa[0])

for k in range(K):
    px = np.random.randint(0, n_pixels)

    v = []

    for f in faixa:
        v.append(f[px])

    centroid.append(np.array(v))
    print(centroid[-1])


MAX_ITER = 200
iter = 0
CLUSTER = [[] for _ in range(K)]
while True:

    # Parte de Agrupamento:
    tic = time.time()

    for px in range(n_pixels):

        v = [
            faixa[0][px],
            faixa[1][px],
            faixa[2][px]
        ]

        d = []

        for k in range(K):
            d.append(
                np.linalg.norm(
                    np.array(v) - np.array(centroid[k])
                )
            )

        cluster = np.argmin(d)
        CLUSTER[cluster].append(px)

    print(len(CLUSTER[0]), len(CLUSTER[1]))
    print(f'(temp: {time.time() - tic})S')


    # Parte do Centroid:
    novo_centroid = []

    for k in range(K):

        L = len(CLUSTER[k])
        S = np.zeros(3)

        for px in CLUSTER[k]:
            S += [
                faixa[0][px],
                faixa[1][px],
                faixa[2][px]
            ]

        novo_centroid.append([
            int(S[0] / L),
            int(S[1] / L),
            int(S[2] / L)
        ])


    # Verificação
    conv = True

    for k in range(K):

        for c in range(3):

            if centroid[k][c] != novo_centroid[k][c]:
                conv = False
                break


    print(f'Convergiu: {conv}')


    # Controle das iterações
    if not conv:

        centroid = novo_centroid
        iter += 1
        print(f'Iterações {iter}')

        if iter >= MAX_ITER:
            print(f'não convergiram em {MAX_ITER} iterações')
            break

    else:

        print(f'Convergiu em {iter} iterações')
        break