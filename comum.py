import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.base import BaseEstimator, TransformerMixin

BASE_DIR = Path(__file__).parent
MODEL_PATH = BASE_DIR / "modelo.pkl"
DATA_PATH = BASE_DIR / "data" / "secondary_sales.csv"

# legíveis nos temas claro e escuro, para os gráficos não dependerem de rerun ao trocar o tema
COR_DESTAQUE = "#1E78E6"
COR_CONTEXTO = "#8A9099"

DORMITORIOS = {"studio": 0, "1_dorm": 1, "2_dorm": 2, "3_dorm": 3, "4_dorm_plus": 4}
DORMITORIOS_ROTULO = {"studio": "Studio", "1_dorm": "1", "2_dorm": "2", "3_dorm": "3", "4_dorm_plus": "4+"}
PADRAO = {"affordable": "Econômico", "mid": "Médio", "premium": "Alto padrão", "luxury": "Luxo"}
CONSERVACAO = {"novo": "Novo", "seminovo": "Seminovo", "reformado": "Reformado",
               "necessita_reforma": "Precisa de reforma"}
SOL = {"face_norte": "Norte", "face_leste": "Leste", "face_oeste": "Oeste", "face_sul": "Sul"}
TRAJETO = {"walk": "A pé", "bus": "Ônibus"}
ESTRATEGIA = {"Baseline": "baseline", "GridSearch": "Grid Search", "Optuna": "Optuna"}

CAMPOS_AVALIACAO = [
    "bairro", "transit_line", "transit_distance_min", "transit_distance_type", "dormitorios",
    "area_util_m2", "vagas_garagem", "year_built", "floor", "total_floors", "sun_facing",
    "condition", "tier", "condominio_brl_monthly", "seguranca_24h", "varanda_gourmet",
    "lazer_completo", "in_eixo_plano_diretor", "listing_year", "area_total_m2", "lat", "lon",
    "to_paulista_km", "to_faria_lima_km",
]


class CodificadorBairro(BaseEstimator, TransformerMixin):
    """Mesma classe do notebook, necessária para desserializar o pipeline."""

    def __init__(self, suavizacao=50):
        self.suavizacao = suavizacao

    def fit(self, X, y):
        serie = X.iloc[:, 0]
        y = np.asarray(y, dtype=float)
        self.media_global_ = float(y.mean())
        estatisticas = pd.DataFrame({"cat": serie.values, "y": y}).groupby("cat")["y"].agg(["mean", "count"])
        estatisticas["codificado"] = (
            estatisticas["count"] * estatisticas["mean"] + self.suavizacao * self.media_global_
        ) / (estatisticas["count"] + self.suavizacao)
        self.mapa_ = estatisticas["codificado"].to_dict()
        return self

    def transform(self, X):
        serie = X.iloc[:, 0]
        return serie.map(self.mapa_).fillna(self.media_global_).to_numpy().reshape(-1, 1)

    def get_feature_names_out(self, input_features=None):
        return np.array(["bairro_codificado"])


@st.cache_resource
def carregar_modelo():
    # o pipeline foi serializado no notebook, onde a classe pertence a __main__
    sys.modules["__main__"].CodificadorBairro = CodificadorBairro
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


@st.cache_data
def carregar_dados():
    df = pd.read_csv(DATA_PATH)
    df["listing_year"] = pd.to_datetime(df["date_listed"]).dt.year
    df = df[df["year_built"] <= df["listing_year"]].copy()
    df["preco_m2"] = df["price_brl"] / df["area_util_m2"]
    return df


@st.cache_data
def carregar_referencias():
    def moda(s):
        return s.mode().iat[0]

    return carregar_dados().groupby("bairro").agg(
        zona=("zona", moda),
        lat=("lat", "median"),
        lon=("lon", "median"),
        to_paulista_km=("to_paulista_km", "median"),
        to_faria_lima_km=("to_faria_lima_km", "median"),
        transit_line=("transit_line", moda),
        transit_distance_min=("transit_distance_min", "median"),
        transit_distance_type=("transit_distance_type", moda),
        condominio=("condominio_brl_monthly", "median"),
        preco_m2=("preco_m2", "median"),
    )


def brl(valor):
    return "R$ " + f"{valor:,.0f}".replace(",", ".")


def numero(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def secao(texto):
    st.html(f'<p class="secao">{texto}</p>')
