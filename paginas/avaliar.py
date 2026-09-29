import pandas as pd
import streamlit as st

from comum import (CONSERVACAO, DORMITORIOS, DORMITORIOS_ROTULO, ESTRATEGIA, PADRAO, SOL, TRAJETO, brl,
                   carregar_modelo, carregar_referencias, numero, secao)

ALTURA_PREDIO = [4, 8, 15, 25, 40]
ANOS_ANUNCIO = list(range(2020, 2027))
PROPORCAO_AREA_TOTAL = 1.225


def ordenar(valores, ordem):
    return [v for v in ordem if v in valores] + sorted(v for v in valores if v not in ordem)


def aplicar_bairro():
    ref = carregar_referencias().loc[st.session_state.bairro]
    st.session_state.lat = round(float(ref.lat), 5)
    st.session_state.lon = round(float(ref.lon), 5)
    st.session_state.to_paulista_km = round(float(ref.to_paulista_km), 2)
    st.session_state.to_faria_lima_km = round(float(ref.to_faria_lima_km), 2)
    st.session_state.transit_line = ref.transit_line
    st.session_state.transit_distance_min = int(ref.transit_distance_min)
    st.session_state.transit_distance_type = ref.transit_distance_type


def aplicar_area_util():
    st.session_state.area_total_m2 = round(st.session_state.area_util_m2 * PROPORCAO_AREA_TOTAL, 1)


def limitar_andar():
    st.session_state.floor = min(st.session_state.floor, st.session_state.total_floors)


def limitar_ano_construcao():
    st.session_state.year_built = min(st.session_state.year_built, st.session_state.listing_year)


modelo_salvo = carregar_modelo()
referencias = carregar_referencias()
categorias = modelo_salvo["categorias"]

bairros = sorted(categorias["bairro"])
linhas = ordenar(categorias["transit_line"], [f"Linha {i}" for i in range(1, 16)])

if "bairro" not in st.session_state:
    st.session_state.bairro = "Pinheiros" if "Pinheiros" in bairros else bairros[0]
    aplicar_bairro()
    st.session_state.update({
        "dormitorios": "2_dorm",
        "area_util_m2": 70.0,
        "area_total_m2": round(70.0 * PROPORCAO_AREA_TOTAL, 1),
        "vagas_garagem": 1,
        "floor": 5,
        "total_floors": 15,
        "year_built": 2005,
        "condition": "seminovo",
        "sun_facing": "face_norte",
        "tier": "mid",
        "condominio_brl_monthly": int(round(referencias.loc[st.session_state.bairro, "condominio"], -1)),
        "seguranca_24h": True,
        "varanda_gourmet": False,
        "lazer_completo": False,
        "in_eixo_plano_diretor": False,
        "listing_year": ANOS_ANUNCIO[-1],
    })

st.title("Quanto vale esse apartamento?")
st.caption("Estimativa de preço de mercado para apartamentos de revenda, "
           "com base em anúncios de 2020 a 2026.")
st.write("")

col_form, col_resultado = st.columns([1.55, 1], gap="large")

with col_form:
    with st.container(border=True):
        secao("Localização")
        st.selectbox("Bairro", bairros, key="bairro", on_change=aplicar_bairro)
        c1, c2, c3 = st.columns([1.1, 1, 1.15])
        c1.selectbox("Linha mais próxima", linhas, key="transit_line",
                     help="Linha de metrô ou trem mais próxima do imóvel.")
        c2.number_input("Minutos até a estação", min_value=1, max_value=240, step=1,
                        key="transit_distance_min")
        c3.segmented_control("Trajeto", list(TRAJETO), format_func=TRAJETO.get, required=True,
                             key="transit_distance_type")

    with st.container(border=True):
        secao("Imóvel")
        st.segmented_control("Dormitórios", list(DORMITORIOS), format_func=DORMITORIOS_ROTULO.get,
                             required=True, key="dormitorios")
        c1, c2, c3 = st.columns(3)
        c1.number_input("Área útil (m²)", min_value=20.0, max_value=400.0, step=1.0, format="%.1f",
                        key="area_util_m2", on_change=aplicar_area_util)
        c2.selectbox("Vagas de garagem", [0, 1, 2, 3, 4], key="vagas_garagem")
        c3.number_input("Ano de construção", min_value=1960, max_value=st.session_state.listing_year,
                        step=1, key="year_built")
        c1, c2, c3 = st.columns(3)
        c1.number_input("Andar", min_value=1, max_value=st.session_state.total_floors, step=1, key="floor")
        c2.selectbox("Andares do prédio", ALTURA_PREDIO, key="total_floors", on_change=limitar_andar)
        c3.selectbox("Face do sol", list(SOL), format_func=SOL.get, key="sun_facing")
        st.segmented_control("Conservação", list(CONSERVACAO), format_func=CONSERVACAO.get,
                             required=True, key="condition")

    with st.container(border=True):
        secao("Padrão e condomínio")
        st.segmented_control("Padrão do imóvel", list(PADRAO), format_func=PADRAO.get,
                             required=True, key="tier")
        st.number_input("Condomínio mensal (R$)", min_value=100, max_value=15000, step=50,
                        key="condominio_brl_monthly")
        c1, c2 = st.columns(2)
        c1.toggle("Segurança 24h", key="seguranca_24h")
        c1.toggle("Varanda gourmet", key="varanda_gourmet")
        c2.toggle("Lazer completo", key="lazer_completo")
        c2.toggle("Eixo de estruturação urbana", key="in_eixo_plano_diretor",
                  help="Imóvel dentro de um eixo de estruturação da transformação urbana do "
                       "Plano Diretor de São Paulo.")

    with st.expander("Ajustes avançados"):
        st.caption("Preenchidos automaticamente a partir do bairro e da área útil. "
                   "Altere apenas se souber o valor exato.")
        c1, c2 = st.columns(2)
        c1.selectbox("Ano do anúncio", ANOS_ANUNCIO, key="listing_year", on_change=limitar_ano_construcao)
        c2.number_input("Área total (m²)", min_value=20.0, max_value=500.0, step=1.0, format="%.1f",
                        key="area_total_m2")
        c1.number_input("Latitude", min_value=-24.1, max_value=-23.2, step=0.00001, format="%.5f", key="lat")
        c2.number_input("Longitude", min_value=-47.0, max_value=-46.2, step=0.00001, format="%.5f", key="lon")
        c1.number_input("Distância até a Av. Paulista (km)", min_value=0.0, max_value=40.0, step=0.01,
                        format="%.2f", key="to_paulista_km")
        c2.number_input("Distância até a Faria Lima (km)", min_value=0.0, max_value=40.0, step=0.01,
                        format="%.2f", key="to_faria_lima_km")

s = st.session_state
zona = referencias.loc[s.bairro, "zona"]
entrada = pd.DataFrame([{
    "lat": s.lat,
    "lon": s.lon,
    "area_util_m2": s.area_util_m2,
    "area_total_m2": s.area_total_m2,
    "floor": s.floor,
    "total_floors": s.total_floors,
    "dorms": DORMITORIOS[s.dormitorios],
    "vagas_garagem": s.vagas_garagem,
    "year_built": s.year_built,
    "building_age": s.listing_year - s.year_built,
    "listing_year": s.listing_year,
    "transit_distance_min": s.transit_distance_min,
    "to_paulista_km": s.to_paulista_km,
    "to_faria_lima_km": s.to_faria_lima_km,
    "seguranca_24h": int(s.seguranca_24h),
    "varanda_gourmet": int(s.varanda_gourmet),
    "lazer_completo": int(s.lazer_completo),
    "in_eixo_plano_diretor": int(s.in_eixo_plano_diretor),
    "condominio_brl_monthly": s.condominio_brl_monthly,
    "zona": zona,
    "tier": s.tier,
    "property_type": s.dormitorios,
    "condition": s.condition,
    "sun_facing": s.sun_facing,
    "transit_line": s.transit_line,
    "transit_distance_type": s.transit_distance_type,
    "bairro": s.bairro,
}])[modelo_salvo["colunas_x"]]

preco = float(modelo_salvo["pipeline"].predict(entrada)[0])
preco_m2 = preco / s.area_util_m2
variacao_bairro = preco_m2 / referencias.loc[s.bairro, "preco_m2"] - 1
metricas = modelo_salvo["metricas_teste"]
erro = metricas["erro_pct_mediano"]
rotulo_dorm = "Studio" if s.dormitorios == "studio" else f"{DORMITORIOS_ROTULO[s.dormitorios]} dorm."

with col_resultado:
    with st.container(border=True, key="card_preco"):
        st.html('<p class="rotulo-preco">Preço estimado</p>'
                f'<p class="preco">{brl(preco)}</p>'
                f'<p class="faixa">Faixa provável: <span style="white-space: nowrap">'
                f'{brl(preco * (1 - erro))} a {brl(preco * (1 + erro))}</span></p>'
                f'<p class="resumo">{rotulo_dorm} · {s.area_util_m2:.0f} m² · {s.bairro}, {zona}</p>')
        st.divider()
        st.metric("Preço por m²", brl(preco_m2),
                  delta=f"{variacao_bairro:+.0%} vs. mediana do bairro", delta_color="off")
        st.caption(f"Em imóveis que o modelo nunca viu, metade das estimativas ficou a menos de "
                   f"{numero(erro * 100, 1)}% do preço real (R² = {numero(metricas['R2'], 3)}).")

    artigo = "do" if zona == "Centro" else "da"
    st.page_link("paginas/mercado.py", label=f"Ver o mercado {artigo} {zona}", icon=":material/arrow_forward:")
    st.caption(f"Modelo: {modelo_salvo['nome_modelo']} ajustado via "
               f"{ESTRATEGIA.get(modelo_salvo['estrategia_tuning'], modelo_salvo['estrategia_tuning'])}.")

    with st.expander("Dados enviados ao modelo"):
        st.dataframe(entrada.T.rename(columns={0: "valor"}).astype(str), width="stretch")
