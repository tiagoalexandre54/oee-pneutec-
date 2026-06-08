"""
OEE — Sistema de Eficiência Global da Produção
NSA Pneutec — Sistema gerencial separado do ERP.
4 abas espelham a planilha "OEE Maio NSA PNEUTEC".
"""
import streamlit as st
import datetime
from pathlib import Path
from modules.database import carregar_oee, salvar_oee, agregar_mes, status_oee

_LOGO_PATH = Path(__file__).parent / "assets" / "logo.png"

st.set_page_config(
    page_title="OEE — NSA Pneutec",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS global — tema escuro BI
st.markdown("""
<style>
    /* Layout */
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    /* Métricas — dark card */
    [data-testid="metric-container"] {
        background:#1A2236; border-radius:8px;
        padding:12px 14px; box-shadow:0 2px 8px rgba(0,0,0,.4);
        border:1px solid #2A3548;
    }
    [data-testid="metric-container"] label { color:#9AA3B2 !important; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] { color:#E8EAF0 !important; }
    /* Dataframe header azul */
    [data-testid="stDataFrame"] thead tr th {
        background:#1565C0 !important; color:white !important;
        font-weight:700 !important;
    }
    /* Sidebar escura */
    section[data-testid="stSidebar"] { background:#141E30 !important; }
    section[data-testid="stSidebar"] .stMarkdown { color:#C5CEE0; }
    /* Botão primário */
    .stButton > button[kind="primary"] {
        background:linear-gradient(135deg,#1565C0,#4FC3F7);
        border:none; border-radius:8px; font-weight:700; color:white;
        transition: opacity .2s;
    }
    .stButton > button[kind="primary"]:hover { opacity: .88; }
    /* Inputs & selects */
    .stSelectbox div[data-baseweb="select"] > div { background:#1A2236; border-color:#2A3548; }
    .stNumberInput input { background:#1A2236; border-color:#2A3548; color:#E8EAF0; }
    /* Expander */
    details { background:#1A2236; border:1px solid #2A3548; border-radius:8px; }
    /* Caption */
    .stCaption { color:#9AA3B2 !important; }
    /* Divider */
    hr { border-color:#2A3548; }
</style>
""", unsafe_allow_html=True)

# ── Sessão ────────────────────────────────────────────────────────────────────
if "oee_dados" not in st.session_state:
    st.session_state.oee_dados = carregar_oee()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo / Brand
    if _LOGO_PATH.exists():
        st.image(str(_LOGO_PATH), use_container_width=True)
    else:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#003366,#0066CC);
                    border-radius:10px;padding:16px;text-align:center;margin-bottom:8px;">
            <div style="font-size:2rem;">📊</div>
            <div style="color:white;font-weight:800;font-size:1rem;letter-spacing:1px;">NSA PNEUTEC</div>
            <div style="color:rgba(255,255,255,.7);font-size:.75rem;">OEE · Eficiência Global</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    menu = st.radio(
        "Navegação:",
        [
            "📊 Dashboard OEE",
            "📋 Lançamento Diário",
            "📈 Análise Mensal",
            "🔧 Pneus Homem-Mês",
            "⚙️ Configurações",
        ],
        label_visibility="collapsed",
    )

    # ── Resumo do mês atual na sidebar ────────────────────────────────────────
    st.markdown("---")
    dados   = st.session_state.oee_dados
    config  = dados.get("config", {})
    lancs   = dados.get("lancamentos", {})
    hoje    = datetime.date.today()
    mes_iso = hoje.strftime("%Y-%m")

    agg = agregar_mes(lancs, config, mes_iso)

    st.markdown(f"**📅 {hoje.strftime('%B %Y').capitalize()}**")

    if agg:
        oee_v = agg["oee"]
        cor   = ("#2E7D32" if oee_v >= 0.85 else
                 "#F9A825" if oee_v >= 0.65 else
                 "#E65100" if oee_v >= 0.45 else "#C62828")
        st.markdown(
            f"""<div style="background:#1A2236;border-radius:8px;padding:12px;
                    box-shadow:0 2px 8px rgba(0,0,0,.4);margin-bottom:8px;
                    border:1px solid #2A3548;">
                <div style="font-size:10px;color:#9AA3B2;font-weight:700;
                            text-transform:uppercase;letter-spacing:.7px;">OEE do Mês</div>
                <div style="font-size:1.6rem;font-weight:900;color:{cor};">
                    {oee_v*100:.1f}%
                </div>
                <div style="font-size:11px;color:{cor};">{status_oee(oee_v, mensal=True)}</div>
                <div style="background:#2A3548;border-radius:4px;height:5px;margin-top:6px;">
                    <div style="background:{cor};width:{min(oee_v*100,100):.1f}%;
                                height:5px;border-radius:4px;"></div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"🔢 {agg['dias_com_producao']} dias · {agg['produzido']:,} pneus  \n"
            f"⏱️ Disponib: **{agg['disponib']*100:.1f}%**  \n"
            f"⚡ Desempenho: **{agg['desempenho']*100:.1f}%**  \n"
            f"✅ Qualidade: **{agg['qualidade']*100:.1f}%**"
        )
    else:
        dias_mes = sum(1 for k in lancs if k.startswith(mes_iso))
        st.markdown(
            f"📅 Lançamentos: **{dias_mes} dias**  \n"
            f"🎯 Meta/dia: **{int(config.get('meta_diaria', 360))} pneus**  \n"
            f"⏱️ Turno: **{config.get('turno_horas', 8.8)}h**"
        )

    st.markdown("---")
    st.caption("v2.0 · NSA Pneutec · 2026")

# ── Roteamento ────────────────────────────────────────────────────────────────
if menu == "📊 Dashboard OEE":
    from modules.dashboard import tela_dashboard
    tela_dashboard()

elif menu == "📋 Lançamento Diário":
    from modules.lancamento import tela_lancamento
    tela_lancamento()

elif menu == "📈 Análise Mensal":
    from modules.analise_mensal import tela_analise_mensal
    tela_analise_mensal()

elif menu == "🔧 Pneus Homem-Mês":
    from modules.homem_mes import tela_homem_mes
    tela_homem_mes()

elif menu == "⚙️ Configurações":
    st.markdown("""
    <div style="background:linear-gradient(135deg,#003366 0%,#0066CC 100%);
                padding:22px 28px;border-radius:12px;margin-bottom:24px;">
        <h2 style="color:white;margin:0;font-size:1.6rem;font-weight:800;">
            ⚙️ Configurações do Sistema
        </h2>
        <p style="color:rgba(255,255,255,.75);margin:4px 0 0;font-size:.9rem;">
            Parâmetros gerais — altere ao mudar o mês, equipe ou metas de produção
        </p>
    </div>
    """, unsafe_allow_html=True)

    config = dados.get("config", {})

    with st.form("form_config"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                '<div style="background:#1F2E45;border-radius:8px;padding:12px 16px;margin-bottom:8px;border:1px solid #2A3548;">'
                '<b>🎯 Metas de Produção</b></div>',
                unsafe_allow_html=True,
            )
            meta_dia = st.number_input(
                "Meta Diária (pneus/dia):", 1, 2000,
                int(config.get("meta_diaria", 360)),
                help="Meta de produção por dia de trabalho",
            )
            dias_ut = st.number_input(
                "Dias Úteis no Mês:", 1, 31,
                int(config.get("dias_uteis", 20)),
                help="Dias de trabalho efetivo no mês (exclui fins de semana e feriados)",
            )
            st.info(f"📦 Meta Mensal calculada: **{meta_dia * dias_ut} pneus**")

        with col2:
            st.markdown(
                '<div style="background:#1F2E45;border-radius:8px;padding:12px 16px;margin-bottom:8px;border:1px solid #2A3548;">'
                '<b>👥 Equipe & Turno</b></div>',
                unsafe_allow_html=True,
            )
            pneus_colab = st.number_input(
                "Pneus/Colab/Mês (meta):", 1, 2000,
                int(config.get("pneus_colab_mes", 180)),
                help="Meta de produção por colaborador por mês. "
                     "Define: Pneus/Homem/dia = Pneus/Colab/Mês ÷ Dias Úteis",
            )
            turno_h = st.number_input(
                "Turno (horas):", 1.0, 24.0,
                float(config.get("turno_horas", 8.8)),
                step=0.1, format="%.1f",
                help="Duração do turno de trabalho em horas",
            )
            pneus_hd = pneus_colab / dias_ut if dias_ut > 0 else 0
            st.caption(f"👤 Pneus/Homem/dia calculado: **{pneus_hd:.1f}**")

        salvar_cfg = st.form_submit_button("💾 Salvar Configurações", type="primary")

    if salvar_cfg:
        dados["config"] = {
            "meta_diaria":     meta_dia,
            "pneus_colab_mes": pneus_colab,
            "turno_horas":     turno_h,
            "dias_uteis":      dias_ut,
        }
        salvar_oee(dados)
        st.session_state.oee_dados = dados
        st.success("✅ Configurações salvas com sucesso!")

    # ── Fórmulas OEE ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📐 Fórmulas OEE — NSA Pneutec")
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        st.markdown("""
| Indicador | Fórmula |
|---|---|
| **Tempo Disponível** | Colab. Presentes × Turno (h) |
| **Tempo Operacional** | T.Disp − Par.Plan − Par.N.Plan |
| **Disponibilidade (A)** | T.Operacional / T.Disponível |
| **Pneus/Homem/dia** | Pneus/Colab/Mês ÷ Dias Úteis |
| **Pneus a Produzir** | Colab. Presentes × Pneus/H/dia |
| **Desempenho (P)** | Produzidos / Meta Diária |
| **Aprovados** | Produzidos − Defeitos |
| **Qualidade (Q)** | Aprovados / Produzidos |
| **OEE** | **A × P × Q** |
        """)

    with col_f2:
        st.markdown("""
| OEE | Classificação |
|---|---|
| ≥ 85% | 🟢 World Class |
| 65–84% | 🟡 Bom |
| 45–64% | 🟠 Regular |
| < 45% | 🔴 Crítico |
        """)
        st.markdown("---")
        st.markdown("**Parâmetros atuais:**")
        config_atual = st.session_state.oee_dados.get("config", {})
        st.markdown(
            f"- Meta diária: **{int(config_atual.get('meta_diaria', 360))} pneus**\n"
            f"- Dias úteis: **{int(config_atual.get('dias_uteis', 20))}**\n"
            f"- Turno: **{config_atual.get('turno_horas', 8.8)}h**\n"
            f"- Meta mensal: **{int(config_atual.get('meta_diaria', 360)) * int(config_atual.get('dias_uteis', 20))} pneus**\n"
            f"- Pneus/colab/mês: **{int(config_atual.get('pneus_colab_mes', 180))}**"
        )

    # ── Persistência cloud ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### ☁️ Persistência na Nuvem (GitHub)")
    st.markdown(
        "Os dados são salvos em `data/oee.json` no repositório GitHub. "
        "Configure o arquivo `.streamlit/secrets.toml` para sincronização em nuvem:"
    )
    st.code(
        "# .streamlit/secrets.toml\n"
        "[github]\n"
        'token  = "ghp_seu_token_aqui"\n'
        'repo   = "tiagoalexandre54/nsa-erp-pneutec"\n'
        'branch = "main"',
        language="toml",
    )
    st.caption(
        "Sem token: dados salvos apenas localmente em `data/oee.json`.  \n"
        "Com token: sincronização automática com GitHub a cada lançamento."
    )
