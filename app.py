import streamlit as st

from comum import BASE_DIR, CAMPOS_AVALIACAO, MODEL_PATH

st.set_page_config(page_title="Preditor de Preço de Imóveis em São Paulo",
                   page_icon=":material/apartment:", layout="wide")
st.logo(str(BASE_DIR / "assets" / "logo.svg"), size="large")

st.html("""
<style>
header[data-testid="stHeader"] { border-bottom: 1px solid rgba(128, 128, 128, .22); }
@media (min-width: 60rem) {
  [data-testid="stToolbar"] > div { justify-content: center; gap: 1.5rem; }
  [data-testid="stToolbar"] > div > div:has([data-testid="stTopNavLinkContainer"]) {
    flex: 0 0 auto; width: 16rem; justify-content: center; padding: 0; }
  [data-testid="stToolbar"] > div > div:has([data-testid="stMainMenu"]) {
    position: absolute; right: 0; margin-left: 0; }
}
[data-testid="stToolbar"] > div > div:has([data-testid="stMainMenu"]) { pointer-events: none; }
[data-testid="stMainMenu"], [data-testid="stMainMenuPopover"], .st-key-infra_tema,
div:has(> .st-key-infra_tema) { display: none !important; }
html[data-tema="escuro"] [data-testid="stHeaderLogo"] { filter: invert(1); }
#botao-tema { position: absolute; right: 1.25rem; top: 50%; transform: translateY(-50%); z-index: 1000001;
              width: 2.25rem; height: 2.25rem; padding: 0; border-radius: 50%; cursor: pointer;
              display: inline-flex; align-items: center; justify-content: center;
              background: transparent; color: inherit; border: 1px solid rgba(128, 128, 128, .35); }
#botao-tema:hover { background: rgba(128, 128, 128, .14); }
#botao-tema:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
[data-testid="stMainBlockContainer"] { max-width: 1180px; padding-top: 5.5rem; }
.secao { font-size: .78rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
         opacity: .68; margin: 0 0 .25rem 0; }
.rotulo-preco { font-size: .78rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
                opacity: .68; margin: 0; }
.preco { font-size: 2.6rem; font-weight: 700; letter-spacing: -.02em; line-height: 1.15; margin: .15rem 0 .1rem 0; }
.faixa { font-size: .98rem; margin: 0 0 .35rem 0; }
.resumo { opacity: .7; font-size: .92rem; margin: 0; }
.st-key-card_preco { background: rgba(128, 128, 128, .07); }
.rodape { opacity: .7; font-size: .8rem; border-top: 1px solid rgba(128, 128, 128, .22);
          padding-top: 1rem; margin-top: 2.5rem; }
</style>
""")

# botão de tema: aciona o seletor nativo do Streamlit (menu oculto); no JS, "<" vira "\x3c"
# porque o sanitizador do st.html descarta scripts com tags no texto
st.container(key="infra_tema").html("""
<script>
(() => {
  if (window.__botaoTema) return;
  window.__botaoTema = true;
  const icone = (caminho) => '\\x3csvg width="18" height="18" viewBox="0 0 24 24" fill="none" ' +
    'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + caminho + '\\x3c/svg>';
  const LUA = icone('\\x3cpath d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>');
  const SOL = icone('\\x3ccircle cx="12" cy="12" r="4"/>\\x3cpath d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41' +
    'M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>');
  const POPOVER = '[data-testid="stMainMenuPopover"]';
  let ocupado = false;

  const escuro = () => {
    const app = document.querySelector('.stApp');
    if (!app) return false;
    const [r, g, b] = getComputedStyle(app).backgroundColor.match(/\\d+/g).map(Number);
    return 0.299 * r + 0.587 * g + 0.114 * b < 128;
  };
  const mostrar = (botao, e) => {
    document.documentElement.dataset.tema = e ? 'escuro' : 'claro';
    const rotulo = e ? 'Ativar modo claro' : 'Ativar modo escuro';
    if (botao.title !== rotulo) {
      botao.innerHTML = e ? SOL : LUA;
      botao.title = rotulo;
      botao.setAttribute('aria-label', rotulo);
    }
  };
  const esperar = (seletor) => new Promise((resolve) => {
    let tentativas = 60;
    const t = setInterval(() => {
      const el = document.querySelector(seletor);
      if (el || --tentativas <= 0) { clearInterval(t); resolve(el); }
    }, 15);
  });
  const alternar = async () => {
    if (ocupado) return;
    ocupado = true;
    const botao = document.getElementById('botao-tema');
    const destino = escuro() ? 'Light' : 'Dark';
    try {
      const menu = document.querySelector('[data-testid="stMainMenu"] button');
      if (!menu) return;
      if (!document.querySelector(POPOVER)) menu.click();
      const item = await esperar('[data-testid="stMainMenuItem-theme-' + destino + '"]');
      if (!item) return;
      item.click();
      mostrar(botao, destino === 'Dark');
      // o Streamlit guarda o tema por caminho da URL; grava o mesmo valor para todas as páginas
      const base = location.pathname.replace(/(mercado|sobre)\\/?$/, '');
      [base, base + 'mercado', base + 'sobre'].forEach(
        (caminho) => localStorage.setItem('stActiveTheme-' + caminho + '-v2', JSON.stringify(destino)));
    } finally {
      if (document.querySelector(POPOVER)) document.querySelector('[data-testid="stMainMenu"] button')?.click();
      setTimeout(() => { ocupado = false; }, 150);
    }
  };
  const injetar = () => {
    const header = document.querySelector('header[data-testid="stHeader"]');
    if (!header) return;
    let botao = document.getElementById('botao-tema');
    if (!botao) {
      botao = document.createElement('button');
      botao.id = 'botao-tema';
      botao.type = 'button';
      botao.addEventListener('click', alternar);
      header.appendChild(botao);
    }
    if (!ocupado) mostrar(botao, escuro());
  };
  injetar();
  setInterval(injetar, 300);
})();
</script>
""", unsafe_allow_javascript=True)

# widgets de páginas não exibidas perdem o estado; reatribuir mantém o formulário entre páginas
for campo in CAMPOS_AVALIACAO:
    if campo in st.session_state:
        st.session_state[campo] = st.session_state[campo]

if not MODEL_PATH.exists():
    st.error("Modelo não encontrado. Execute o notebook do CheckPoint 5 para gerar "
             "`modelo.pkl` na raiz do projeto.")
    st.stop()

pagina = st.navigation([
    st.Page("paginas/avaliar.py", title="Avaliar imóvel", default=True),
    st.Page("paginas/mercado.py", title="Mercado", url_path="mercado"),
    st.Page("paginas/sobre.py", title="Sobre", url_path="sobre"),
], position="top")
pagina.run()

st.html('<p class="rodape">Projeto acadêmico · FIAP · Data Science &amp; Statistical Computing · '
        'CheckPoint 5</p>')
