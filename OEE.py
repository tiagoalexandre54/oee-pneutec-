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
        st.image(str(_LOGO_PATH), width="stretch")
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
    import json as _json
    import datetime as _dt
    from modules.database import _modo_github

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

    # ── Status de persistência ────────────────────────────────────────────────
    n_lanc = len(dados.get("lancamentos", {}))
    n_man  = len(dados.get("analise_manual", {}))
    if _modo_github():
        st.success(
            f"☁️ **Dados salvos no GitHub** — sincronização automática ativa.  \n"
            f"📦 {n_lanc} lançamentos · {n_man} análises manuais em nuvem."
        )
    else:
        st.warning(
            f"⚠️ **Modo local apenas** — dados salvos só neste computador.  \n"
            f"📦 {n_lanc} lançamentos · {n_man} análises manuais locais.  \n"
            f"Configure o token GitHub em `.streamlit/secrets.toml` para não perder dados."
        )

    config = dados.get("config", {})

    # ── Formulário de parâmetros ──────────────────────────────────────────────
    st.markdown("#### ⚙️ Parâmetros de Produção")
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
                help="Meta de produção por colaborador por mês.",
            )
            turno_h = st.number_input(
                "Turno (horas):", 1.0, 24.0,
                float(config.get("turno_horas", 8.8)),
                step=0.1, format="%.1f",
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

    # ── Metas de Produção por Mês ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🎯 Metas de Produção por Mês")
    st.caption(
        "Defina uma meta personalizada para cada mês. "
        "**0 = usar padrão** (Meta Diária × Dias Úteis configurados acima)."
    )

    _MESES_NOMES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    _ano_hoje    = _dt.date.today().year

    _col_yr, _ = st.columns([1, 3])
    _ano_sel_m  = _col_yr.selectbox(
        "Ano:", [_ano_hoje - 1, _ano_hoje, _ano_hoje + 1],
        index=1, key="cfg_ano_metas",
    )

    # Recarrega config (pode ter sido salvo acima)
    _cfg_atual    = st.session_state.oee_dados.get("config", {})
    _metas_cfg    = _cfg_atual.get("metas_mensais", {})
    _meta_padrao  = int(_cfg_atual.get("meta_diaria", 360)) * int(_cfg_atual.get("dias_uteis", 20))

    # Preview: quais meses têm meta customizada neste ano
    _meses_custom = [
        f"{_MESES_NOMES[int(k[5:7])-1]}/{k[:4]}: **{int(v):,}**"
        for k, v in _metas_cfg.items()
        if k.startswith(str(_ano_sel_m)) and v
    ]
    if _meses_custom:
        st.info("📌 Metas personalizadas cadastradas: " + " · ".join(_meses_custom))
    else:
        st.caption(f"Nenhuma meta personalizada para {_ano_sel_m}. Todos os meses usam o padrão de **{_meta_padrao:,} pneus**.")

    with st.form("form_metas_mensais"):
        st.caption(f"📦 Padrão global: **{_meta_padrao:,} pneus/mês**. Deixe 0 para usar o padrão no mês.")
        _metas_novas = {}

        for _row in range(3):
            _cols_m = st.columns(4)
            for _ci in range(4):
                _mi       = _row * 4 + _ci
                _mes_nome = _MESES_NOMES[_mi]
                _mes_key  = f"{_ano_sel_m}-{_mi+1:02d}"
                _val_atual = int(_metas_cfg.get(_mes_key) or 0)
                _v = _cols_m[_ci].number_input(
                    f"{_mes_nome} {_ano_sel_m}",
                    min_value=0,
                    max_value=999_999,
                    value=_val_atual,
                    step=100,
                    help=f"Padrão: {_meta_padrao:,} pneus. Digite 0 para usar o padrão.",
                    key=f"meta_{_mes_key}",
                )
                if _v > 0:
                    _metas_novas[_mes_key] = _v

        _salvar_metas = st.form_submit_button("💾 Salvar Metas Mensais", type="primary", width="stretch")

    if _salvar_metas:
        # Preserva metas de outros anos, sobrescreve apenas o ano selecionado
        _todas_metas = {k: v for k, v in _metas_cfg.items() if not k.startswith(str(_ano_sel_m))}
        _todas_metas.update(_metas_novas)
        dados["config"]["metas_mensais"] = _todas_metas
        salvar_oee(dados)
        st.session_state.oee_dados = dados
        st.success(f"✅ Metas mensais de {_ano_sel_m} salvas! ({len(_metas_novas)} meses personalizados)")
        st.rerun()

    # ── Backup & Restauração ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 💾 Backup & Restauração de Dados")

    col_dl, col_up = st.columns(2)

    with col_dl:
        st.markdown(
            '<div style="background:#1F2E45;border-radius:8px;padding:12px 16px;'
            'margin-bottom:12px;border:1px solid #2A3548;"><b>⬇️ Baixar Backup</b></div>',
            unsafe_allow_html=True,
        )
        backup_bytes = _json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")
        fname = f"oee_backup_{_dt.date.today().isoformat()}.json"
        st.download_button(
            label="⬇️ Baixar Backup Completo",
            data=backup_bytes,
            file_name=fname,
            mime="application/json",
            help="Salva todos os lançamentos e análises num arquivo .json",
        )
        st.caption(
            f"Arquivo: `{fname}`  \n"
            f"Contém: **{n_lanc}** lançamentos + **{n_man}** análises manuais"
        )

    with col_up:
        st.markdown(
            '<div style="background:#1F2E45;border-radius:8px;padding:12px 16px;'
            'margin-bottom:12px;border:1px solid #2A3548;"><b>📤 Restaurar Backup</b></div>',
            unsafe_allow_html=True,
        )
        arquivo = st.file_uploader(
            "Selecione o arquivo de backup (.json):",
            type=["json"],
            key="upload_backup",
            label_visibility="collapsed",
        )
        if arquivo is not None:
            try:
                dados_bkp = _json.loads(arquivo.read())
                if dados_bkp.get("_schema") == 2:
                    n_l = len(dados_bkp.get("lancamentos", {}))
                    n_m = len(dados_bkp.get("analise_manual", {}))
                    st.info(f"📦 Backup: **{n_l}** lançamentos · **{n_m}** análises manuais")
                    if st.button("✅ Restaurar estes dados", type="primary", key="btn_restaurar"):
                        salvar_oee(dados_bkp)
                        st.session_state.oee_dados = dados_bkp
                        st.success("✅ Dados restaurados com sucesso!")
                else:
                    st.error("❌ Arquivo inválido — schema incompatível.")
            except Exception as _ex:
                st.error(f"❌ Erro ao ler o arquivo: {_ex}")

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

    # ── Zona de Perigo ────────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("🗑️ Zona de Perigo — Apagar Todos os Dados", expanded=False):
        st.markdown(
            '<div style="background:#3B0A0A;border-radius:8px;padding:14px 18px;'
            'border:1px solid #C62828;margin-bottom:16px;">'
            '<b style="color:#FF5252;">⚠️ ATENÇÃO:</b>'
            '<span style="color:#FFCDD2;"> Esta ação apaga permanentemente TODOS os lançamentos '
            'diários e análises manuais. As configurações de metas são mantidas. '
            'Faça um backup antes de continuar.</span></div>',
            unsafe_allow_html=True,
        )
        col_conf, col_btn = st.columns([2, 1])
        confirmar_txt = col_conf.text_input(
            "Digite **CONFIRMAR** para habilitar o botão:",
            key="conf_apagar",
            placeholder="CONFIRMAR",
        )
        botao_habilitado = confirmar_txt.strip().upper() == "CONFIRMAR"
        apagar = col_btn.button(
            "🗑️ Apagar Tudo",
            type="primary",
            disabled=not botao_habilitado,
            key="btn_apagar",
        )
        if apagar and botao_habilitado:
            dados_zerados = {
                "_schema": 2,
                "config":        dados.get("config", {}),
                "lancamentos":   {},
                "analise_manual": {},
            }
            salvar_oee(dados_zerados)
            st.session_state.oee_dados  = dados_zerados
            st.session_state["_apagado"] = True

    if st.session_state.pop("_apagado", False):
        st.success("✅ Todos os dados foram apagados. Configurações mantidas.")
        st.balloons()
