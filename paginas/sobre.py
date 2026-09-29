import pandas as pd
import streamlit as st

from comum import ESTRATEGIA, brl, carregar_dados, carregar_modelo, numero, secao

EQUIPE = [
    ("Ulisses Ribeiro Abreu", "562230"),
    ("Arthur Berlofa Bosi", "564438"),
    ("Davi Melo Muniz", "562828"),
    ("Mateus Saavedra", "563266"),
    ("Danilo dos Santos", "561657"),
]

modelo_salvo = carregar_modelo()
metricas = modelo_salvo["metricas_teste"]
n_anuncios = len(carregar_dados())
estrategia = ESTRATEGIA.get(modelo_salvo["estrategia_tuning"], modelo_salvo["estrategia_tuning"])

st.title("Sobre o projeto")
st.markdown("Uma ferramenta para estimar o preço de mercado de apartamentos de revenda em São Paulo "
            "a partir das características do imóvel, desenvolvida no CheckPoint 5 da disciplina "
            "Data Science & Statistical Computing (FIAP).")
st.write("")

secao("Como a estimativa é feita")
c1, c2, c3 = st.columns(3, gap="medium")
with c1.container(border=True, height="stretch"):
    st.markdown("**Dados**")
    st.markdown(f"{numero(n_anuncios)} anúncios de apartamentos de revenda de 2020 a 2026, do dataset "
                "público *São Paulo Real Estate Sales and Rentals* (Kaggle).")
with c2.container(border=True, height="stretch"):
    st.markdown("**Modelo**")
    st.markdown(f"Random Forest, XGBoost e LightGBM foram comparados e ajustados com Grid Search e "
                f"Optuna. O vencedor foi o {modelo_salvo['nome_modelo']} ajustado via {estrategia}.")
with c3.container(border=True, height="stretch"):
    st.markdown("**Validação**")
    st.markdown("Validação cruzada com 5 folds nos dados de treino e avaliação final em 20% dos "
                "anúncios, que o modelo nunca viu durante o desenvolvimento.")
st.write("")

secao("Precisão no conjunto de teste")
m1, m2, m3 = st.columns(3)
m1.metric("Erro percentual típico", f"{numero(metricas['erro_pct_mediano'] * 100, 1)}%", border=True,
          help="Mediana de |preço real − estimativa| / preço real.")
m2.metric("Variância explicada (R²)", numero(metricas["R2"], 3), border=True)
m3.metric("Erro médio absoluto", brl(metricas["MAE"]), border=True)
st.write("")

secao("Limitações")
st.markdown(
    "- A estimativa é estatística e parte de anúncios; não substitui um laudo de avaliação.\n"
    "- Os preços refletem o período de 2020 a 2026 da base e não acompanham o mercado depois disso.\n"
    "- Em reais, o erro cresce com o valor do imóvel; em termos percentuais, é parecido em todas "
    "as faixas de preço."
)
st.write("")

secao("Equipe")
st.dataframe(pd.DataFrame(EQUIPE, columns=["Integrante", "RM"]), hide_index=True, width=420)
