"""
Tela 4 — Pneus Homem-Mês (espelha aba "🔧 Pneus Homem-Mês" da planilha).
Relação entre colaboradores presentes e pneus produzidos por mês.
"""
import streamlit as st
import pandas as pd
from modules.database import agregar_mes

_MESES_ORDEM = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
_MESES_ISO   = {m: f"{i+1:02d}" for i, m in enumerate(_MESES_ORDEM)}


def _mini_kpi(label: str, valor: str, sub: str, cor: str, col) -> None:
    html = (
        f'<div style="background:#1A2236;border-radius:10px;padding:16px;'
        f'box-shadow:0 4px 16px rgba(0,0,0,.5);border-left:5px solid {cor};'
        f'border:1px solid #2A3548;text-align:center;">'
        f'<div style="font-size:10px;color:#9AA3B2;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:.8px;margin-bottom:6px;">{label}</div>'
        f'<div style="font-size:1.8rem;font-weight:900;color:{cor};">{valor}</div>'
        f'<div style="font-size:11px;color:#9AA3B2;margin-top:4px;">{sub}</div>'
        f'</div>'
    )
    col.markdown(html, unsafe_allow_html=True)


def tela_homem_mes():
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:linear-gradient(135deg,#003366 0%,#0066CC 100%);
                padding:22px 28px;border-radius:12px;margin-bottom:24px;">
        <h2 style="color:white;margin:0;font-size:1.6rem;font-weight:800;">
            🔧 Pneus por Homem / Mês — Produtividade
        </h2>
        <p style="color:rgba(255,255,255,.75);margin:4px 0 0;font-size:.9rem;">
            Pneus / Pessoa = Pneus Produzidos ÷ Média de Colaboradores Presentes
        </p>
    </div>
    """, unsafe_allow_html=True)

    dados  = st.session_state.oee_dados
    config = dados.get("config", {})
    lancs  = dados.get("lancamentos", {})

    anos = sorted({k[:4] for k in lancs}, reverse=True)
    if not anos:
        st.info("Sem lançamentos. Acesse **📋 Lançamento Diário** para começar.")
        return

    col_a, _ = st.columns([1, 3])
    ano_sel   = col_a.selectbox("📅 Ano:", anos, key="hm_ano")

    # ── Coleta de dados ───────────────────────────────────────────────────────
    rows = []
    for mes_nome in _MESES_ORDEM:
        mes_num = _MESES_ISO[mes_nome]
        mes_iso = f"{ano_sel}-{mes_num}"
        agg     = agregar_mes(lancs, config, mes_iso)
        if agg and agg["produzido"] > 0:
            pp = (agg["produzido"] / agg["media_colab"]) if agg["media_colab"] > 0 else 0
            rows.append({
                "Mês":                  mes_nome,
                "Média Colab. Pres.":   round(agg["media_colab"], 1),
                "Pneus Produzidos":     agg["produzido"],
                "Aprovados":            agg["aprovados"],
                "Defeitos":             agg["defeitos"],
                "% Qualidade":          f"{(agg['aprovados']/agg['produzido']*100):.1f}%" if agg["produzido"] else "—",
                "Pneus / Pessoa":       int(round(pp)),
                "Meta Pneus/Pessoa":    int(config.get("pneus_colab_mes", 180)),
                "% vs Meta":            f"{pp / config.get('pneus_colab_mes', 180) * 100:.1f}%"
                                        if config.get("pneus_colab_mes", 0) > 0 else "—",
            })

    if not rows:
        st.info(f"Sem dados de produção para {ano_sel}.")
        return

    n = len(rows)
    media_pp      = sum(r["Pneus / Pessoa"] for r in rows) / n
    total_prod    = sum(r["Pneus Produzidos"] for r in rows)
    media_colab   = sum(r["Média Colab. Pres."] for r in rows) / n
    meta_pp       = int(config.get("pneus_colab_mes", 180))

    # ── KPIs de produtividade ─────────────────────────────────────────────────
    cor_pp = "#2E7D32" if media_pp >= meta_pp else ("#F9A825" if media_pp >= meta_pp * 0.85 else "#C62828")
    c1, c2, c3, c4 = st.columns(4)
    _mini_kpi("Pneus/Pessoa Médio", f"{media_pp:.1f}", f"Meta: {meta_pp}", cor_pp, c1)
    _mini_kpi("Total Produzido",    f"{total_prod:,}", f"{n} meses",       "#003366", c2)
    _mini_kpi("Média Colab. Pres.", f"{media_colab:.1f}", "colaboradores", "#0066CC", c3)
    _mini_kpi("Meses com Dados",    str(n),            ano_sel,            "#546E7A", c4)

    st.markdown("<br>", unsafe_allow_html=True)

    # Linha de média na tabela
    rows_tab = list(rows)
    rows_tab.append({
        "Mês":                "MÉDIA",
        "Média Colab. Pres.": round(media_colab, 1),
        "Pneus Produzidos":   round(total_prod / n),
        "Aprovados":          round(sum(r["Aprovados"] for r in rows) / n),
        "Defeitos":           round(sum(r["Defeitos"]  for r in rows) / n),
        "% Qualidade":        f"{sum(float(r['% Qualidade'].replace('%','')) for r in rows if r['% Qualidade'] != '—') / n:.1f}%",
        "Pneus / Pessoa":     round(media_pp, 1),
        "Meta Pneus/Pessoa":  meta_pp,
        "% vs Meta":          f"{media_pp / meta_pp * 100:.1f}%" if meta_pp else "—",
    })

    st.dataframe(pd.DataFrame(rows_tab), hide_index=True, width="stretch")

    # ── Gráfico ───────────────────────────────────────────────────────────────
    if n >= 2:
        st.markdown("#### 📊 Pneus por Pessoa — Evolução Mensal")
        df_chart = pd.DataFrame([
            {"Mês": r["Mês"], "Pneus / Pessoa": r["Pneus / Pessoa"]}
            for r in rows
        ]).set_index("Mês")
        st.bar_chart(df_chart, height=260)

    # ── Nota explicativa ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f"""<div style="background:#0D2137;border-radius:8px;padding:14px 18px;font-size:13px;color:#90CAF9;border:1px solid #1565C0;">
            <b>📌 Fórmula:</b> Pneus / Pessoa = Pneus Produzidos ÷ Média de Colaboradores Presentes no mês.<br>
            <b>Meta atual:</b> <b>{meta_pp} pneus</b> por colaborador por mês
            (= {config.get('meta_diaria',360)} pneus/dia ÷ {config.get('dias_uteis',20)} dias úteis × dias úteis).<br>
            Apenas meses com lançamentos diários são exibidos.
        </div>""",
        unsafe_allow_html=True,
    )
