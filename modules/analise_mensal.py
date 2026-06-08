"""
Tela 3 — Análise Mensal (espelha aba "📈 Análise Mensal" da planilha).
Meses com lançamentos diários → cálculo automático.
Meses históricos (sem daily) → entrada manual via expander.

FIX: st.rerun() REMOVIDO do handler do form.
     Em Streamlit, a submissão de form já dispara um rerun natural.
     Chamar st.rerun() DENTRO de expander+form causa duplo rerun que
     corrompe o React DOM (NotFoundError: removeChild).
     Solução: flag em session_state, exibida no início do próximo render.
"""
import streamlit as st
import pandas as pd
from io import BytesIO
from modules.database import agregar_mes, salvar_oee, status_oee

_MESES_ORDEM = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
_MESES_ISO   = {m: f"{i+1:02d}" for i, m in enumerate(_MESES_ORDEM)}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _pct(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, float) and v != v:   # NaN
        return "—"
    return f"{float(v) * 100:.2f}%"


def _cor_oee(v: float | None) -> str:
    if v is None:
        return "#9E9E9E"
    if v >= 0.85: return "#2E7D32"
    if v >= 0.65: return "#F9A825"
    if v >= 0.45: return "#E65100"
    return "#C62828"


def _df_excel(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Análise Mensal")
        ws = writer.sheets["Análise Mensal"]
        from openpyxl.styles import PatternFill, Font, Alignment
        fill_h = PatternFill("solid", fgColor="003366")
        font_h = Font(bold=True, color="FFFFFF")
        fill_t = PatternFill("solid", fgColor="E3F2FD")
        font_t = Font(bold=True)
        for idx, col_name in enumerate(df.columns, 1):
            c = ws.cell(row=1, column=idx)
            c.fill = fill_h
            c.font = font_h
            c.alignment = Alignment(horizontal="center")
            ws.column_dimensions[c.column_letter].width = max(len(str(col_name)) + 4, 12)
        last_row = ws.max_row
        for col in range(1, ws.max_column + 1):
            ws.cell(row=last_row, column=col).fill = fill_t
            ws.cell(row=last_row, column=col).font = font_t
        ws.freeze_panes = "A2"
    return buf.getvalue()


def _kpi_card(label: str, valor: str, cor: str, icon: str = "") -> str:
    return (
        f'<div style="background:#1A2236;border-radius:10px;padding:14px 16px;'
        f'box-shadow:0 4px 16px rgba(0,0,0,.5);border-top:4px solid {cor};'
        f'border:1px solid #2A3548;text-align:center;">'
        f'<div style="font-size:10px;color:#9AA3B2;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:.8px;margin-bottom:6px;">{icon} {label}</div>'
        f'<div style="font-size:1.7rem;font-weight:900;color:{cor};line-height:1.1;">{valor}</div>'
        f'</div>'
    )


def _avg_pct_col(rows: list, key: str) -> str:
    """Calcula média de percentuais formatados ('xx.xx%') de uma lista de linhas."""
    vals = []
    for r in rows:
        v = r.get(key, "—")
        if v != "—":
            try:
                vals.append(float(str(v).replace("%", "")))
            except Exception:
                pass
    return f"{sum(vals)/len(vals):.2f}%" if vals else "—"


# ── Tela principal ─────────────────────────────────────────────────────────────

def tela_analise_mensal():
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:linear-gradient(135deg,#003366 0%,#0066CC 100%);
                padding:22px 28px;border-radius:12px;margin-bottom:24px;">
        <h2 style="color:white;margin:0;font-size:1.6rem;font-weight:800;">
            📈 Análise Mensal &amp; Histórico OEE
        </h2>
        <p style="color:rgba(255,255,255,.75);margin:4px 0 0;font-size:.9rem;">
            Evolução anual dos indicadores de eficiência global da produção
        </p>
    </div>
    """, unsafe_allow_html=True)

    dados  = st.session_state.oee_dados
    config = dados.get("config", {})
    lancs  = dados.get("lancamentos", {})
    manual = dados.get("analise_manual", {})

    # Mensagem de sucesso via flag (evita st.rerun() dentro do expander)
    if "_am_salvo" in st.session_state:
        msg = st.session_state.pop("_am_salvo")
        st.success(f"✅ Dados de **{msg}** salvos com sucesso!")

    # ── Seleção de ano ────────────────────────────────────────────────────────
    anos = sorted({k[:4] for k in lancs} | {k[:4] for k in manual}, reverse=True)
    if not anos:
        import datetime
        anos = [str(datetime.date.today().year)]

    col_a, _ = st.columns([1, 3])
    ano_sel   = col_a.selectbox("📅 Ano:", anos, key="am_ano")

    meta_diaria = float(config.get("meta_diaria", 360))
    dias_uteis  = int(config.get("dias_uteis", 20))

    # ── Montar linhas ─────────────────────────────────────────────────────────
    rows_dados = []   # Apenas meses com dados (auto ou manual)

    for mes_nome in _MESES_ORDEM:
        mes_num = _MESES_ISO[mes_nome]
        mes_iso = f"{ano_sel}-{mes_num}"

        agg = agregar_mes(lancs, config, mes_iso)
        man = manual.get(mes_iso)

        if agg:
            meta_m = agg["meta_mensal"]
            rows_dados.append({
                "Mês":          mes_nome,
                "Dias Prod.":   agg["dias_com_producao"],
                "Total Prod.":  agg["produzido"],
                "Aprovados":    agg["aprovados"],
                "Defeitos":     agg["defeitos"],
                "% Defeito":    f"{agg['defeitos']/agg['produzido']*100:.2f}%" if agg["produzido"] else "—",
                "Disponib.":    _pct(agg["disponib"]),
                "Desempenho":   _pct(agg["desempenho"]),
                "Qualidade":    _pct(agg["qualidade"]),
                "OEE Geral":    _pct(agg["oee"]),
                "Meta Mensal":  int(meta_m),
                "% da Meta":    _pct(agg["produzido"] / meta_m) if meta_m else "—",
                "Resultado":    status_oee(agg["oee"], mensal=True),
                "_oee_raw":     agg["oee"],
                "_fonte":       "auto",
            })
        elif man:
            meta_m = man.get("meta_mensal", meta_diaria * dias_uteis)
            prod   = man.get("produzido", 0)
            rows_dados.append({
                "Mês":          mes_nome,
                "Dias Prod.":   man.get("dias_uteis", dias_uteis),
                "Total Prod.":  prod,
                "Aprovados":    man.get("aprovados", 0),
                "Defeitos":     man.get("defeitos",  0),
                "% Defeito":    f"{man['defeitos']/prod*100:.2f}%" if prod else "—",
                "Disponib.":    _pct(man.get("disponib")),
                "Desempenho":   _pct(man.get("desempenho")),
                "Qualidade":    _pct(man.get("qualidade")),
                "OEE Geral":    _pct(man.get("oee")),
                "Meta Mensal":  int(meta_m),
                "% da Meta":    _pct(prod / meta_m) if meta_m else "—",
                "Resultado":    status_oee(man.get("oee", 0), mensal=True),
                "_oee_raw":     man.get("oee", 0),
                "_fonte":       "manual",
            })

    if not rows_dados:
        st.info(f"Nenhum dado para **{ano_sel}**. Use o formulário abaixo para inserir histórico.")
    else:
        n = len(rows_dados)

        # ── KPIs anuais ───────────────────────────────────────────────────────
        oee_vals   = [r["_oee_raw"] for r in rows_dados]
        oee_medio  = sum(oee_vals) / n
        total_prod = sum(r["Total Prod."] for r in rows_dados if isinstance(r["Total Prod."], int))
        total_def  = sum(r["Defeitos"]    for r in rows_dados if isinstance(r["Defeitos"],    int))
        cor_oee    = _cor_oee(oee_medio)

        st.markdown(
            f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">'
            f'{_kpi_card("OEE Médio Anual",  f"{oee_medio*100:.1f}%", cor_oee,    "🏆")}'
            f'{_kpi_card("Meses com Dados",   str(n),                  "#003366",  "📅")}'
            f'{_kpi_card("Total Produzido",   f"{total_prod:,}",       "#0066CC",  "🔢")}'
            f'{_kpi_card("Total Defeitos",    str(total_def),          "#C62828",  "❌")}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Linha de média anual ──────────────────────────────────────────────
        rows_tabela = list(rows_dados)   # cópia para não alterar o original
        total_aprov = sum(r["Aprovados"] for r in rows_dados if isinstance(r["Aprovados"], int))

        rows_tabela.append({
            "Mês":          "MÉDIA ANUAL",
            "Dias Prod.":   "—",
            "Total Prod.":  total_prod,
            "Aprovados":    total_aprov,
            "Defeitos":     total_def,
            "% Defeito":    _avg_pct_col(rows_dados, "% Defeito"),
            "Disponib.":    _avg_pct_col(rows_dados, "Disponib."),
            "Desempenho":   _avg_pct_col(rows_dados, "Desempenho"),
            "Qualidade":    _avg_pct_col(rows_dados, "Qualidade"),
            "OEE Geral":    _avg_pct_col(rows_dados, "OEE Geral"),
            "Meta Mensal":  "—",
            "% da Meta":    _avg_pct_col(rows_dados, "% da Meta"),
            "Resultado":    "",
            "_oee_raw":     None,
            "_fonte":       "total",
        })

        # Exibir tabela (sem colunas internas)
        df_view = pd.DataFrame(rows_tabela).drop(columns=["_oee_raw", "_fonte"])
        # Colunas mistas (int + "—") precisam ser string para Arrow serialização
        for _col in ["Dias Prod.", "Meta Mensal"]:
            if _col in df_view.columns:
                df_view[_col] = df_view[_col].astype(str)
        st.dataframe(df_view, hide_index=True, width="stretch")

        # ── Gráfico de evolução ───────────────────────────────────────────────
        chart_src = [r for r in rows_dados if r["_oee_raw"] is not None]

        if len(chart_src) >= 2:
            st.markdown(f"#### 📊 Evolução dos Indicadores — {ano_sel}")

            def _safe_float(r, key) -> float | None:
                v = r.get(key, "—")
                if v == "—":
                    return None
                try:
                    return float(str(v).replace("%", ""))
                except Exception:
                    return None

            chart_data = pd.DataFrame([
                {
                    "Mês":           r["Mês"],
                    "OEE %":         round(r["_oee_raw"] * 100, 2),
                    "Disponib. %":   _safe_float(r, "Disponib."),
                    "Desempenho %":  _safe_float(r, "Desempenho"),
                    "Qualidade %":   _safe_float(r, "Qualidade"),
                }
                for r in chart_src
            ]).set_index("Mês").dropna(how="all")

            st.line_chart(chart_data, height=280)
            st.caption("Linha de meta = 85% (World Class)")

        # ── Exportar Excel ────────────────────────────────────────────────────
        df_export = pd.DataFrame(rows_tabela).drop(columns=["_oee_raw", "_fonte"])
        col_dl, _ = st.columns([1, 3])
        col_dl.download_button(
            "⬇️ Exportar Excel",
            data=_df_excel(df_export),
            file_name=f"oee_analise_mensal_{ano_sel}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # ── Inserção manual de mês histórico ──────────────────────────────────────
    st.markdown("---")
    with st.expander("📝 Inserir / Editar mês histórico (sem lançamento diário)", expanded=False):
        st.caption(
            "Use para meses anteriores que não possuem lançamentos diários registrados. "
            "Informe os valores totais/médias do mês."
        )

        col1, col2 = st.columns(2)
        mes_manual = col1.selectbox("Mês:", _MESES_ORDEM, key="am_mes_manual")
        ano_manual = col2.text_input("Ano:", value=ano_sel, key="am_ano_manual")
        mes_key    = f"{ano_manual}-{_MESES_ISO[mes_manual]}"
        ex         = manual.get(mes_key, {})
        # Usa meta específica do mês se cadastrada em config; senão usa meta global
        _metas_cfg = config.get("metas_mensais", {})
        meta_m_def = int(_metas_cfg.get(mes_key) or (meta_diaria * dias_uteis))

        with st.form("form_mensal_manual"):
            st.markdown("##### 📦 Volumes de Produção")
            c1, c2, c3 = st.columns(3)
            du_m   = c1.number_input("Dias Úteis:",     1, 31,    int(ex.get("dias_uteis",  dias_uteis)))
            prod_m = c2.number_input("Total Produzido:",0, 50000, int(ex.get("produzido",   0)))
            apro_m = c3.number_input("Total Aprovados:",0, 50000, int(ex.get("aprovados",   0)))

            c4, c5 = st.columns(2)
            def_m  = c4.number_input("Defeitos:",       0, 50000, int(ex.get("defeitos",    0)))
            meta_m = c5.number_input("Meta Mensal:",    0, 50000, int(ex.get("meta_mensal", meta_m_def)))

            st.markdown("##### 📊 Indicadores Médios do Mês (valor de 0.0 a 1.0)")
            d1, d2, d3, d4 = st.columns(4)
            disp_m = d1.number_input("Disponib.:",  0.0, 1.0, float(ex.get("disponib",   0.0)), step=0.001, format="%.4f")
            desp_m = d2.number_input("Desempenho:", 0.0, 1.0, float(ex.get("desempenho", 0.0)), step=0.001, format="%.4f")
            qual_m = d3.number_input("Qualidade:",  0.0, 1.0, float(ex.get("qualidade",  0.0)), step=0.001, format="%.4f")
            oee_m  = d4.number_input("OEE:",        0.0, 1.0, float(ex.get("oee",        0.0)), step=0.001, format="%.4f")

            # Preview de cálculo
            if disp_m > 0 and desp_m > 0 and qual_m > 0:
                oee_calc = disp_m * desp_m * qual_m
                st.info(
                    f"OEE calculado = {disp_m:.4f} × {desp_m:.4f} × {qual_m:.4f} "
                    f"= **{oee_calc*100:.2f}%** {status_oee(oee_calc, mensal=True)}"
                )

            salvar_m = st.form_submit_button("💾 Salvar Mês", type="primary")

        # ── FORA do with st.form(), DENTRO do with st.expander() ────────────
        # NÃO chamar st.rerun() aqui!
        # A submissão do form já dispara um rerun automático no Streamlit.
        # Um st.rerun() adicional dentro de expander corrompe o React DOM.
        if salvar_m:
            dados["analise_manual"][mes_key] = {
                "dias_uteis":  du_m,
                "produzido":   prod_m,
                "aprovados":   apro_m,
                "defeitos":    def_m,
                "disponib":    disp_m,
                "desempenho":  desp_m,
                "qualidade":   qual_m,
                "oee":         oee_m,
                "meta_mensal": meta_m,
            }
            salvar_oee(dados)
            st.session_state.oee_dados = dados
            # Flag exibida no PRÓXIMO render (após o rerun natural do form)
            st.session_state["_am_salvo"] = f"{mes_manual}/{ano_manual}"
