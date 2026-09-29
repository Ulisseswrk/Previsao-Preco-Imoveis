# Preditor de Preço de Imóveis em São Paulo

Modelo de regressão que estima o **preço de venda de apartamentos de revenda em São Paulo** a partir das características do imóvel: localização, área, padrão, conservação e infraestrutura. Três algoritmos de árvores (Random Forest, XGBoost e LightGBM) são comparados sob o mesmo protocolo experimental e ajustados com **Grid Search** e **Optuna**.

Projeto desenvolvido para o **CheckPoint 5** da disciplina *Data Science & Statistical Computing* (FIAP).

---

## Sumário

- [Resultado em resumo](#resultado-em-resumo)
- [O problema](#o-problema)
- [Base de dados](#base-de-dados)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Como executar](#como-executar)
- [Metodologia, exercício por exercício](#metodologia-exercício-por-exercício)
- [Modelo salvo](#modelo-salvo)
- [Aplicação Streamlit](#aplicação-streamlit)
- [Limitações](#limitações)
- [Equipe](#equipe)
- [Referências](#referências)

---

## Resultado em resumo

O modelo escolhido foi o **XGBoost ajustado com Optuna**. Ele foi avaliado **uma única vez** no conjunto de teste, que ficou isolado durante todo o desenvolvimento:

| Métrica (conjunto de teste) | Valor |
|---|---|
| **RMSE** (métrica principal) | R$ 114.403 |
| **MAE** | R$ 66.910 |
| **R²** | 0,975 |
| **Erro percentual mediano** | 7,4% |

- Metade das previsões fica a menos de **7,4%** do preço real, e o erro percentual é parecido em todas as faixas de preço (7,2% a 7,5%).
- O RMSE do teste ficou **5,3% abaixo** do RMSE da validação cruzada, uma diferença pequena. O modelo generaliza bem para dados que não viu.
- Para comparação, uma regra simples de mercado (mediana do R$/m² do bairro × área útil) erra **11,7%** na mediana, com RMSE de R$ 184.587.

---

## O problema

**Pergunta:** qual o preço de mercado de um apartamento usado em São Paulo, dadas as suas características?

- **Tipo de problema:** regressão supervisionada.
- **Variável-alvo ($y$):** `price_brl`, o preço anunciado em reais.
- **Previsão ($\hat{y}$):** o preço de mercado estimado para o imóvel.
- **Métrica principal:** **RMSE** (raiz do erro quadrático médio), em reais. Ele penaliza mais os erros grandes, que são os mais caros numa precificação, e fica na mesma unidade do preço. **MAE** e **R²** são métricas auxiliares.

---

## Base de dados

- **Fonte:** [*São Paulo Real Estate Sales and Rentals 2020-2026*](https://www.kaggle.com/datasets/sergionefedov/so-paulo-real-estate-sales-and-rentals-2020-2026), no Kaggle.
- **Arquivo utilizado:** `secondary_sales.csv`, com os anúncios de **revenda**.
- **Unidade observacional:** 1 linha = 1 apartamento de revenda anunciado em São Paulo entre 2020 e 2026.
- **Dimensões:** 50.000 linhas × 37 colunas na base original, e **47.829 linhas × 28 colunas** depois do tratamento.
- **Alvo:** preços de R$ 36 mil a R$ 8,7 milhões, com mediana de R$ 538 mil e forte assimetria à direita (assimetria de 2,55).

O dataset completo tem outras tabelas (aluguéis, lançamentos, preços mensais por bairro e estações). Elas **não foram usadas**:
- aluguéis e lançamentos são outros mercados, com outra lógica de preço;
- a tabela de preços por bairro resume os próprios preços que o modelo tenta prever e causaria vazamento de informação do alvo.

---

## Estrutura do repositório

```
.
├── cp5_algoritmo_imoveis.ipynb   # notebook principal: todo o desenvolvimento do modelo
├── modelo.pkl                    # modelo final salvo (pipeline completo + metadados)
├── data/
│   └── secondary_sales.csv       # base de dados de revenda
├── requirements.txt              # versões exatas das bibliotecas
├── app.py                        # aplicação Streamlit (entrada)
├── comum.py                      # funções compartilhadas pela aplicação
├── paginas/                      # páginas da aplicação
├── assets/                       # logo da aplicação
└── .streamlit/config.toml        # tema claro e escuro da aplicação
```

---

## Como executar

**Pré-requisitos:** Python 3.11.

```bash
pip install -r requirements.txt
jupyter notebook cp5_algoritmo_imoveis.ipynb
```

Depois, rode todas as células em ordem (*Restart & Run All*).

- **Tempo:** a execução completa leva **de 20 a 40 minutos**, dependendo da máquina. A maior parte é o Grid Search e o Optuna.
- **Reprodutibilidade:** toda divisão de dados, validação cruzada e busca usa semente fixa (`SEMENTE = 42`). Os resultados se repetem a cada execução.
- **Versões:** use as versões do `requirements.txt`, principalmente o **scikit-learn 1.8.0**. O `modelo.pkl` gerado com outra versão pode não carregar corretamente.

---

## Metodologia, exercício por exercício

O notebook segue os 7 exercícios do enunciado. Cada seção começa com uma breve explicação e termina com tabelas e gráficos.

### Exercício 1 — Problema e base de dados

Define o problema, apresenta a base (fonte, dimensões e dicionário das 37 colunas) e justifica o RMSE como métrica principal a partir da distribuição do alvo.

### Exercício 2 — Tratamento e análise exploratória

**Diagnóstico (2.1)**
- Não há valores ausentes nem linhas duplicadas.
- **2.171 linhas (4,3%)** têm ano de construção posterior ao ano do anúncio. Isso é impossível para um imóvel de revenda, e essas linhas foram removidas.
- O **IPTU é uma fração fixa do preço**: 0,665% do preço, com correlação de 1,000. Usá-lo seria entregar a resposta ao modelo, então ele foi removido como vazamento.
- O condomínio, ao contrário, varia bastante em relação ao preço (coeficiente de variação de 56%). Ele foi mantido como informação legítima.

**Tratamento (2.2)**
- Criação de `listing_year` (ano do anúncio) e `building_age` (idade do imóvel no anúncio).
- Conversão das variáveis booleanas para 0/1.
- Remoção de 11 colunas:

| Coluna(s) | Motivo |
|---|---|
| `iptu_brl_annual` | vazamento: é uma fração fixa do preço |
| `price_per_m2_util_brl`, `price_usd`, `price_per_m2_util_usd` | vazamento: são calculadas a partir do próprio preço |
| `brl_usd_rate_at_listing`, `selic_rate_at_listing`, `mortgage_rate_at_listing`, `ipca_yoy_at_listing` | indicadores macroeconômicos que dependem só da data do anúncio, já representada por `listing_year` |
| `id`, `date_listed` | identificador e data bruta, sem valor preditivo direto |
| `transit_station` | redundante com a linha e a distância até a estação |

**Análise exploratória (2.3)**
- **Log do preço (2.3.1):** o logaritmo do preço tem distribuição próxima da normal, o que justifica treinar em escala logarítmica.
- **Preço por zona (2.3.2):** a mediana vai de R$ 266 mil na Zona Leste a R$ 816 mil na Zona Oeste.
- **Área útil × preço (2.3.3):** o preço cresce com a área, com camadas bem separadas pelo padrão do imóvel.
- **Correlações (2.3.4):** as maiores são com o condomínio (0,84) e a área útil (0,70). A distância até a Faria Lima tem correlação negativa (−0,52).

**Base final (2.4)**
Traz as dimensões finais e a lista das transformações que ficam reservadas ao pipeline, ajustadas só com os dados de treino.

### Exercício 3 — Variáveis e protocolo experimental

- **Variáveis:** 27 preditoras, sendo 18 numéricas, o condomínio (com imputação), 7 categóricas com poucas categorias e o `bairro`, com 85 categorias.
- **Divisão:** 80% treino (38.263 imóveis) e 20% teste (9.566), com `random_state=42`. **O teste só é usado no Exercício 7.**
- **Validação cruzada:** `KFold` com 5 folds, embaralhado e com semente fixa. São os **mesmos folds para os três algoritmos**, em todas as etapas.

**Pipeline de pré-processamento (3.4)**

Todo o pré-processamento fica dentro de um `Pipeline`. Por isso ele é reajustado em cada fold da validação cruzada, sem vazamento de dados:

| Etapa | Variáveis | Transformação |
|---|---|---|
| Imputação | numéricas | mediana (proteção para campos vazios na aplicação) |
| Codificação do bairro | `bairro` | média do preço por bairro, suavizada em direção à média geral (`CodificadorBairro`) |
| One-hot | demais categóricas | uma coluna de sim/não por categoria |
| Alvo | `price_brl` | treino em $\log(1+y)$ via `TransformedTargetRegressor`, com previsão devolvida em reais |

**Por que treinar em escala logarítmica.** Em reais, o modelo se preocuparia quase só com os imóveis caros. Em log, o erro passa a ser medido em **percentual**: errar 10% num imóvel de R$ 300 mil pesa o mesmo que errar 10% num de R$ 3 milhões.

### Exercício 4 — Modelos de referência

Os três algoritmos com hiperparâmetros padrão, sob o mesmo protocolo:

| Modelo | RMSE treino | RMSE validação cruzada | Diferença (validação − treino) |
|---|---|---|---|
| Random Forest | R$ 63.054 | R$ 167.516 | 62% do erro de validação |
| XGBoost | R$ 94.418 | R$ 124.841 | 24% |
| LightGBM | R$ 105.272 | R$ 124.582 | 16% |

O Random Forest mostra **overfitting forte**: erra quase três vezes menos nos dados que viu do que nos que não viu. Os modelos de boosting generalizam bem melhor.

### Exercício 5 — Ajuste de hiperparâmetros

- **Grid Search (5.1):** uma grade de 2 × 2 × 2 = 8 combinações por modelo, variando número de árvores, complexidade e taxa de aprendizado, avaliadas nos 5 folds do treino completo.
- **Optuna (5.2):** **20 tentativas por modelo**, num espaço de busca contínuo com 4 a 6 hiperparâmetros.
  - Para caber no tempo, as tentativas rodam numa amostra de 10 mil imóveis do treino.
  - A melhor configuração é depois **reavaliada no treino completo, com os mesmos folds**. É esse resultado que entra na comparação.
- **Comparação (5.3):**
  - A diferença de RMSE entre Grid Search e Optuna ficou **abaixo de um desvio-padrão entre folds nos três modelos**. Nesta base, o ajuste de hiperparâmetros muda pouco o resultado.
  - O Optuna explora valores fora de uma grade fixa e aprende com as tentativas anteriores. O Grid Search testa todas as combinações, mas só os valores da grade.

### Exercício 6 — Escolha do modelo e análise de generalização

**Tabela das 9 configurações (6.1)**
- São 3 algoritmos × (padrão + Grid Search + Optuna), ordenados pelo RMSE médio de validação cruzada.
- A escolha usa **apenas a validação cruzada**, nunca o teste.

| Posição | Configuração | RMSE validação cruzada |
|---|---|---|
| 1º | **XGBoost (Optuna)** | **R$ 120.812** (± 3.420) |
| 2º | XGBoost (Grid Search) | R$ 121.389 |
| 3º | LightGBM (Grid Search) | R$ 122.787 |

O critério de escolha foi o menor RMSE de validação cruzada. A diferença entre o 1º e o 2º é de apenas 0,17 desvio-padrão, então os dois XGBoost são praticamente equivalentes.

**Curva de aprendizado (6.2)**
- Com mais dados, o erro de validação cai e se aproxima do erro de treino.
- A diferença final é de R$ 11.466, **9,5% do erro de validação**. É um sinal de boa generalização, sem overfitting relevante.

**Importância das variáveis e resíduos (6.3)**
- As variáveis mais importantes são o **bairro (37,6%)**, o **condomínio (16,9%)** e a **área útil (15,1%)**.
- Os resíduos foram calculados com as previsões da validação cruzada, em que cada imóvel é previsto por um modelo que não o viu no treino.
- O erro percentual mediano fica entre 7,2% e 7,5% em todas as faixas de preço.

### Exercício 7 — Teste final, consistência e entrega

- **Avaliação final (7.1):** o modelo é retreinado no treino completo e avaliado uma única vez no teste. Os resultados estão na tabela do [resumo](#resultado-em-resumo).
- **Teste de consistência (7.2):** cinco imóveis do teste, escolhidos assim:
  - o de **menor erro**: Vila Leopoldina, previsto a menos de R$ 20 do preço real;
  - o de **maior erro**: um apartamento de luxo de 251 m² em Moema, 38% acima do preço real. O imóvel foi anunciado por R$ 16.405/m², bem abaixo da mediana de R$ 19.414/m² de imóveis semelhantes no treino;
  - **três aleatórios**.
- **Modelo salvo (7.3):** o pipeline final é exportado para `modelo.pkl`. Depois de recarregado, ele reproduz exatamente as previsões do notebook.

---

## Modelo salvo

O arquivo `modelo.pkl` é um dicionário salvo com `pickle`:

| Chave | Conteúdo |
|---|---|
| `pipeline` | pipeline completo (pré-processamento + XGBoost + transformação logarítmica) |
| `colunas_x` | ordem das 27 colunas esperadas na entrada |
| `categorias` | valores válidos de cada variável categórica |
| `mapa_bairro`, `media_global_bairro` | codificação aprendida para cada bairro |
| `nome_modelo`, `estrategia_tuning` | `XGBoost` e `Optuna` |
| `metricas_teste` | RMSE, MAE, R² e erro percentual mediano no teste |

Para carregar o modelo fora do notebook, a classe `CodificadorBairro` precisa estar definida antes do `pickle.load`, porque o pipeline a utiliza:

```python
import pickle
import sys
from comum import CodificadorBairro  # mesma classe do notebook

sys.modules["__main__"].CodificadorBairro = CodificadorBairro
with open("modelo.pkl", "rb") as f:
    modelo_salvo = pickle.load(f)

previsao = modelo_salvo["pipeline"].predict(dados[modelo_salvo["colunas_x"]])
```

---

## Aplicação Streamlit

O projeto inclui uma aplicação web que usa o `modelo.pkl` para estimar o preço de um imóvel a partir de um formulário. Ela usa o mesmo pipeline do notebook, e as previsões são idênticas às do notebook.

```bash
streamlit run app.py
```

---

## Limitações

- A estimativa é estatística e parte de **preços anunciados**, não de preços de venda efetivos. Ela não substitui um laudo de avaliação.
- O modelo reflete o período de **2020 a 2026** da base e não acompanha o mercado depois disso.
- **Em reais**, o erro cresce com o valor do imóvel: o MAE vai de R$ 16 mil nos imóveis mais baratos a R$ 173 mil nos mais caros. Em termos percentuais, ele é parecido em todas as faixas.
- Como o modelo aprende em escala logarítmica, a previsão se aproxima da **mediana** dos preços de imóveis parecidos, e não da média. Isso gera uma leve tendência a prever abaixo da média.

---

## Equipe

| Integrante | RM |
|---|---|
| Ulisses Ribeiro Abreu | 562230 |
| Arthur Berlofa Bosi | 564438 |
| Davi Melo Muniz | 562828 |
| Mateus Saavedra | 563266 |
| Danilo dos Santos | 561657 |

---

## Referências

- BREIMAN, L. Random Forests. *Machine Learning*, v. 45, p. 5–32, 2001.
- CHEN, T.; GUESTRIN, C. XGBoost: A Scalable Tree Boosting System. *Proceedings of the 22nd ACM SIGKDD*, 2016.
- KE, G. et al. LightGBM: A Highly Efficient Gradient Boosting Decision Tree. *Advances in Neural Information Processing Systems*, 2017.
- AKIBA, T. et al. Optuna: A Next-generation Hyperparameter Optimization Framework. *Proceedings of the 25th ACM SIGKDD*, 2019.
- NEFEDOV, S. *São Paulo Real Estate Sales and Rentals 2020-2026*. Kaggle.
