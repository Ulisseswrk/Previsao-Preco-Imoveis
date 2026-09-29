import altair as alt
import streamlit as st

from comum import COR_CONTEXTO, COR_DESTAQUE, brl, carregar_dados, numero, secao

EIXO_REAIS = "'R$ ' + replace(format(datum.value, ',.0f'), ',', '.')"

df = carregar_dados()
bairro_destaque = st.session_state.get("bairro")
zonas = sorted(df["zona"].unique())
zona_padrao = (df.loc[df["bairro"] == bairro_destaque, "zona"].iat[0]
               if bairro_destaque in set(df["bairro"]) else "Zona Sul")

st.title("Mercado imobiliário")
st.caption("Preços de anúncios de apartamentos de revenda em São Paulo entre 2020 e 2026.")
st.write("")

zona = st.segmented_control("Zona", zonas, default=zona_padrao, required=True, key="zona_mercado")
dz = df[df["zona"] == zona]

c1, c2, c3 = st.columns(3)
c1.metric("Anúncios analisados", numero(len(dz)), border=True)
c2.metric("Preço mediano", brl(dz["price_brl"].median()), border=True)
c3.metric("Mediana do m²", brl(dz["preco_m2"].median()), border=True)
st.write("")

por_bairro = (dz.groupby("bairro")
              .agg(preco_m2=("preco_m2", "median"), anuncios=("preco_m2", "size"))
              .reset_index()
              .sort_values("preco_m2", ascending=False))
por_bairro["rotulo"] = por_bairro["preco_m2"].map(brl)
por_bairro["anuncios_fmt"] = por_bairro["anuncios"].map(numero)
tem_destaque = bairro_destaque in set(por_bairro["bairro"])
por_bairro["cor"] = [COR_DESTAQUE if (b == bairro_destaque or not tem_destaque) else COR_CONTEXTO
                     for b in por_bairro["bairro"]]

anual = dz.groupby("listing_year")["preco_m2"].median().reset_index()
anual["rotulo"] = anual["preco_m2"].map(brl)
ultimo_ano = anual["listing_year"].max()

eixo = dict(domain=False, ticks=False, labelFontSize=12)

col_bairros, col_anos = st.columns([1.2, 1], gap="large")

with col_bairros:
    secao("Preço mediano do m² por bairro")
    if tem_destaque:
        valor_destaque = por_bairro.loc[por_bairro["bairro"] == bairro_destaque, "rotulo"].iat[0]
        st.caption(f"Em destaque: {bairro_destaque}, {valor_destaque}/m², o bairro escolhido na avaliação.")
    base = alt.Chart(por_bairro).encode(
        y=alt.Y("bairro:N", sort=por_bairro["bairro"].tolist(), title=None,
                axis=alt.Axis(grid=False, labelLimit=200, **eixo)),
        x=alt.X("preco_m2:Q", title=None, axis=alt.Axis(tickCount=4, labelExpr=EIXO_REAIS, **eixo)),
        tooltip=[alt.Tooltip("bairro:N", title="Bairro"),
                 alt.Tooltip("rotulo:N", title="Mediana do m²"),
                 alt.Tooltip("anuncios_fmt:N", title="Anúncios")],
    )
    barras = base.mark_bar(size=14, cornerRadiusEnd=4).encode(color=alt.Color("cor:N", scale=None))
    st.altair_chart(barras.properties(height=len(por_bairro) * 24 + 20)
                    .configure_view(stroke=None), width="stretch")

with col_anos:
    secao("Evolução do preço mediano do m²")
    st.caption(f"Em {ultimo_ano}: {anual['rotulo'].iat[-1]}/m². 2026 considera anúncios até abril.")
    base = alt.Chart(anual).encode(
        x=alt.X("listing_year:O", title=None, axis=alt.Axis(labelAngle=0, grid=False, **eixo)),
        y=alt.Y("preco_m2:Q", title=None, scale=alt.Scale(zero=False, nice=True),
                axis=alt.Axis(tickCount=5, labelExpr=EIXO_REAIS, **eixo)),
    )
    linha = base.mark_line(strokeWidth=2, color=COR_DESTAQUE, strokeCap="round", strokeJoin="round")
    pontos = base.mark_point(filled=True, size=70, color=COR_DESTAQUE, opacity=1).encode(
        tooltip=[alt.Tooltip("listing_year:O", title="Ano"), alt.Tooltip("rotulo:N", title="Mediana do m²")])
    st.altair_chart((linha + pontos).properties(height=320).configure_view(stroke=None),
                    width="stretch")

with st.expander("Ver dados em tabela"):
    t1, t2 = st.columns([1.2, 1], gap="large")
    t1.dataframe(por_bairro[["bairro", "rotulo", "anuncios_fmt"]]
                 .rename(columns={"bairro": "Bairro", "rotulo": "Mediana do m²", "anuncios_fmt": "Anúncios"}),
                 hide_index=True, width="stretch")
    t2.dataframe(anual[["listing_year", "rotulo"]].astype(str)
                 .rename(columns={"listing_year": "Ano", "rotulo": "Mediana do m²"}),
                 hide_index=True, width="stretch")
