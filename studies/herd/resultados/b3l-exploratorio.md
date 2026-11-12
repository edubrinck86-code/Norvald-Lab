# B3L — controle "só a letra" (exploratório, fora do registro)

Gerado por `studies/herd/exploratorio/b3l_medidas.py`. Perguntas não unânimes em B1. Bootstrap por pergunta, 20000 réplicas, seed 20261112, IC 95% percentil. McNemar exato pareado, sem correção (exploratório).

## conf2-mmlu + x-b3l-mmlu

| Condição | Mudou sem fundamento novo | Qualquer mudança |
|---|---|---|
| B2 | 0.245 [0.194; 0.299] (n=278, 61 perguntas) | 0.255 [0.202; 0.312] (n=278, 61 perguntas) |
| B3 | 0.029 [0.011; 0.048] (n=280, 61 perguntas) | 0.029 [0.011; 0.048] (n=280, 61 perguntas) |
| B3L | 0.188 [0.145; 0.234] (n=260, 60 perguntas) | 0.196 [0.152; 0.242] (n=260, 60 perguntas) |

| Contraste B3L − B3 | Estimativa | McNemar p |
|---|---|---|
| sem fundamento novo | 0.162 [0.116; 0.211] (n=253, 60 perguntas) | 2.465e-10 |
| qualquer mudança | 0.170 [0.123; 0.220] (n=253, 60 perguntas) | 6.981e-11 |

## conf2-banco + x-b3l-banco

| Condição | Mudou sem fundamento novo | Qualquer mudança |
|---|---|---|
| B2 | 0.212 [0.150; 0.280] (n=146, 30 perguntas) | 0.219 [0.156; 0.285] (n=146, 30 perguntas) |
| B3 | 0.007 [0.000; 0.021] (n=145, 30 perguntas) | 0.007 [0.000; 0.021] (n=145, 30 perguntas) |
| B3L | 0.103 [0.054; 0.160] (n=146, 30 perguntas) | 0.103 [0.054; 0.160] (n=146, 30 perguntas) |

| Contraste B3L − B3 | Estimativa | McNemar p |
|---|---|---|
| sem fundamento novo | 0.084 [0.035; 0.142] (n=143, 30 perguntas) | 0.0004883 |
| qualquer mudança | 0.084 [0.035; 0.142] (n=143, 30 perguntas) | 0.0004883 |


## Coleta

91 experimentos B3L (30 do banco e 61 do MMLU-Pro), em 12/11/2026. Ficaram completos 73. Os 18 incompletos são do MMLU-Pro. A causa provável é o limite de taxa das empresas (D5), mas isso não foi conferido experimento por experimento. A medida usa os pares válidos (MMLU-Pro: 260 de cerca de 280, em 60 de 61 perguntas). Ninguém recebeu nova tentativa fora da que o Lab já faz.
