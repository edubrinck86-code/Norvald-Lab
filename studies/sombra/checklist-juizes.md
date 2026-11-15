# Checklist de leitura: estudos que usam LLM como juiz ou painel

Nasceu da crítica do Eduardo ao Zero-CoT (15/11/2026). Cada item vem de um texto nosso. Serve para ler qualquer artigo, e também para conferir os nossos.

| # | Pergunta | De onde vem |
|---|---|---|
| 1 | Quantos juízes, de quais empresas? Qual a correlação de erro entre eles? Dois juízes da mesma geração valem perto de um. | Texto 2 (N_eff de 1,2 a 1,4 no MMLU-Pro) |
| 2 | Os juízes se veem? Em que ordem? O que cada um vê do outro: só o veredito, ou a justificativa também? | Texto 1 (a exposição aos pares muda a resposta) |
| 3 | O juiz vê o texto, o raciocínio ou os dois? O artigo declara o que é passo de raciocínio e o que é resposta? | Textos 1 e 3 |
| 4 | Em que formato a entrada e a saída circulam: texto livre ou estruturado? | Texto 3 (o formato muda a estabilidade: 10,3% contra 3,9%) |
| 5 | Há linha de base de mudança espontânea (repetição às cegas)? | Texto 1 (B2) |
| 6 | O gabarito do banco foi conferido? Opções acrescentadas podem estar certas. | Texto 2, §4.1 (resíduo do MMLU-Pro) |

Aplicado ao Zero-CoT (2605.21856): itens 1, 2, 3 e 4 não declarados, até onde li. Ressalva: os juízes deles validam se duas perguntas são equivalentes, não deliberam. O efeito manada (item 2) só vale se um viu o outro, e o artigo não diz. O item 1 vale de qualquer modo.
