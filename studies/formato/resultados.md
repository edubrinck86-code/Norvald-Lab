# Estudo do formato: resultados

Gerado por `studies/formato/medidas.py`. Perguntas não unânimes em B1. Bootstrap por pergunta, 20000 réplicas, seed 20261112, IC 95% percentil. H1: McNemar exato pareado, bilateral, α = 0,05.

## combinado

| Condição | Qualquer mudança | Mudou sem fundamento novo (estrita) |
|---|---|---|
| B3 | 0.021 [0.009; 0.035] (n=425, 91 perguntas) | 0.021 [0.009; 0.035] (n=425, 91 perguntas) |
| B3R | 0.039 [0.023; 0.058] (n=433, 91 perguntas) | 0.037 [0.021; 0.056] (n=433, 91 perguntas) |
| B3T | 0.103 [0.075; 0.133] (n=435, 91 perguntas) | 0.103 [0.075; 0.133] (n=435, 91 perguntas) |
| B3L | 0.163 [0.128; 0.199] (n=406, 90 perguntas) | 0.158 [0.123; 0.194] (n=406, 90 perguntas) |

| Contraste B3T − B3R | Estimativa | McNemar p |
|---|---|---|
| qualquer mudança, H1 (confirmatória) | 0.065 [0.037; 0.093] (n=431, 91 perguntas) | 6.17e-05 |

| Condição (com gabarito) | Errado → certo | Certo → errado | Errado → outro errado | Pares |
|---|---|---|---|---|
| B3 | 5 | 3 | 1 | 333 |
| B3R | 9 | 4 | 4 | 339 |
| B3T | 14 | 8 | 20 | 341 |
| B3L | 26 | 13 | 19 | 314 |

## banco

| Condição | Qualquer mudança | Mudou sem fundamento novo (estrita) |
|---|---|---|
| B3 | 0.007 [0.000; 0.021] (n=145, 30 perguntas) | 0.007 [0.000; 0.021] (n=145, 30 perguntas) |
| B3R | 0.027 [0.007; 0.055] (n=147, 30 perguntas) | 0.027 [0.007; 0.055] (n=147, 30 perguntas) |
| B3T | 0.041 [0.013; 0.081] (n=148, 30 perguntas) | 0.041 [0.013; 0.081] (n=148, 30 perguntas) |
| B3L | 0.103 [0.054; 0.160] (n=146, 30 perguntas) | 0.103 [0.054; 0.160] (n=146, 30 perguntas) |

| Contraste B3T − B3R | Estimativa | McNemar p |
|---|---|---|
| qualquer mudança, por banco | 0.014 [-0.020; 0.047] (n=147, 30 perguntas) | 0.6875 |

| Condição (com gabarito) | Errado → certo | Certo → errado | Errado → outro errado | Pares |
|---|---|---|---|---|
| B3 | 1 | 0 | 0 | 53 |
| B3R | 4 | 0 | 0 | 53 |
| B3T | 3 | 0 | 0 | 54 |
| B3L | 5 | 2 | 0 | 54 |

## mmlu

| Condição | Qualquer mudança | Mudou sem fundamento novo (estrita) |
|---|---|---|
| B3 | 0.029 [0.011; 0.048] (n=280, 61 perguntas) | 0.029 [0.011; 0.048] (n=280, 61 perguntas) |
| B3R | 0.045 [0.024; 0.071] (n=286, 61 perguntas) | 0.042 [0.021; 0.067] (n=286, 61 perguntas) |
| B3T | 0.136 [0.099; 0.174] (n=287, 61 perguntas) | 0.136 [0.099; 0.174] (n=287, 61 perguntas) |
| B3L | 0.196 [0.152; 0.242] (n=260, 60 perguntas) | 0.188 [0.145; 0.234] (n=260, 60 perguntas) |

| Contraste B3T − B3R | Estimativa | McNemar p |
|---|---|---|
| qualquer mudança, por banco | 0.092 [0.055; 0.129] (n=284, 61 perguntas) | 6.877e-05 |

| Condição (com gabarito) | Errado → certo | Certo → errado | Errado → outro errado | Pares |
|---|---|---|---|---|
| B3 | 4 | 3 | 1 | 280 |
| B3R | 5 | 4 | 4 | 286 |
| B3T | 11 | 8 | 20 | 287 |
| B3L | 21 | 11 | 19 | 260 |

