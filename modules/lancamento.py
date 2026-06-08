"""
Tela 2 — Lançamento Diário (espelha aba "📋 Lançamento Diário" da planilha).
Campos de input manual: colab_total, colab_presentes, paradas_plan_h,
                        paradas_nplan_h, produzidos, defeitos.
Tudo mais é calculado automaticamente.

FIX: st.rerun() removido do handler de save — a atualização de session_state
     já dispara o rerender natural sem corromper o React DOM.
"""
import streamlit as st
import pandas as pd
import datetime
from modules.database import calcular_dia, salvar_oee, status_oee


def _pct(v: float) -> str:
    return f"{v * 100:.2f}%"


def _cor(v: float) -> str:
    if v >= 0.85: return "#2E7D32"
    if v >= 0.65: return "#F9A825"
    if v >= 0.45: return "#E65100"
    return "#C62828"


def _indicador_card(label: str, valor: float, col) -> None:
    cor = _cor(valor)
    pct = min(valor * 100, 100.0)
    html = (
        f'<div style="background:#1A2236;border-radius:10px;padding:14px 10px;'
        f'box-shadow:0 4px 16px rgba(0,0,0,.5);border-top:4px solid {cor};'
        f'border:1px solid #2A3548;text-align:center;">'
        f'<div style="font-size:10px;color:#9AA3B2;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:.8px;margin-bottom:6px;">{label}</div>'
        f'<div style="font-size:2rem;font-weight:900;color:{cor};line-height:1.1;">{pct:.2f}%</div>'
        f'<div style="background:#2A3548;border-radius:4px;height:6px;margin-top:8px;">'
        f'<div style="background:{cor};width:{pct:.1f}%;height:6px;border-radius:4px;"></div>'
        f'</div></div>'
    )
    col.markdown(html, unsafe_allow_html=True)


def tela_lancamento():
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:linear-gradient(135deg,#003366 0%,#0066CC 100%);
                padding:22px 28px;border-radius:12px;margin-bottom:24px;">
        <h2 style="color:white;margin:0;font-size:1.6rem;font-weight:800;">
            📋 Lançamento Diário de OEE
        </h2>
        <p style="color:rgba(255,255,255,.75);margin:4px 0 0;font-size:.9rem;">
            Registre a produção diária — indicadores calculados automaticamente
        </p>
    </div>
    """, unsafe_allow_html=True)

    dados      = st.session_state.oee_dados
    config     = dados.get("config", {})
    lancs      = dados.get("lancamentos", {})

    meta_dia   = int(config.get("meta_diaria",     360))
    dias_uteis = int(config.get("dias_uteis",       20))
    meta_mes   = meta_dia * dias_uteis
    colab_ref  = int(config.get("pneus_colab_mes", 180))
    turno      = float(config.get("turno_horas",   8.8))

    # Mensagem de sucesso (flag setada no save — sem st.rerun() extra)
    if "_lanc_salvo" in st.session_state:
        msg = st.session_state.pop("_lanc_salvo")
        st.success(f"✅ Lançamento de **{msg}** salvo com sucesso!")

    # Parâmetros ativos
    st.markdown(
        (f'<div style="background:#0D2137;border-radius:8px;padding:10px 16px;'
         f'margin-bottom:16px;font-size:13px;color:#90CAF9;border:1px solid #1565C0;">'
         f'<b>Parâmetros ativos:</b> &nbsp;'
         f'🎯 Meta: <b>{meta_dia} pneus/dia</b> &nbsp;|&nbsp;'
         f'📅 Dias úteis: <b>{dias_uteis}</b> &nbsp;|&nbsp;'
         f'📦 Meta mensal: <b>{meta_mes} pneus</b> &nbsp;|&nbsp;'
         f'⏱️ Turno: <b>{turno}h</b> &nbsp;|&nbsp;'
         f'👤 Pneus/colab/mês: <b>{colab_ref}</b>'
         f'</div>'),
        unsafe_allow_html=True,
    )

    # ── Seleção de data ───────────────────────────────────────────────────────
    hoje     = datetime.date.today()
    data_sel = st.date_input("📅 Data do lançamento:", value=hoje, max_value=hoje, key="lanc_data")
    chave    = data_sel.isoformat()
    e        = lancs.get(chave, {})

    if e:
        st.info(f"✏️ Editando lançamento de **{data_sel.strftime('%d/%m/%Y')}** — dados anteriores carregados.")

    st.markdown("---")

    # ── Formulário ────────────────────────────────────────────────────────────
    with st.form("form_lanc"):
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown(
                '<div style="background:#1F2E45;border-radius:8px;padding:14px 16px;margin-bottom:8px;border:1px solid #2A3548;">'
                '<b>👥 Colaboradores</b></div>',
                unsafe_allow_html=True,
            )
            colab_total = st.number_input(
                "Total Colab. (Mão no Pneu):",
                min_value=0, max_value=200,
                value=int(e.get("colab_total", 0)),
                help="Total de colaboradores na equipe do turno",
            )
            colab_pres = st.number_input(
                "Colab. Presentes:",
                min_value=0, max_value=200,
                value=int(e.get("colab_presentes", 0)),
                help="Colaboradores que compareceram ao trabalho",
            )

        with col_b:
            st.markdown(
                '<div style="background:#1F2E45;border-radius:8px;padding:14px 16px;margin-bottom:8px;border:1px solid #2A3548;">'
                '<b>⏸️ Paradas (horas)</b></div>',
                unsafe_allow_html=True,
            )
            par_plan = st.number_input(
                "Paradas Planejadas (h):",
                min_value=0.0, step=0.25, format="%.2f",
                value=float(e.get("paradas_plan_h", 0.0)),
                help="Ex: manutenção preventiva, treinamento, reunião programada",
            )
            par_nplan = st.number_input(
                "Paradas Não Planejadas (h):",
                min_value=0.0, step=0.25, format="%.2f",
                value=float(e.get("paradas_nplan_h", 0.0)),
                help="Ex: quebra de máquina, falta de material, problemas elétricos",
            )

        st.markdown(
            '<div style="background:#1F2E45;border-radius:8px;padding:14px 16px;margin-bottom:8px;border:1px solid #2A3548;">'
            '<b>🔧 Produção</b></div>',
            unsafe_allow_html=True,
        )
        col5, col6 = st.columns(2)
        produzidos = col5.number_input(
            "Pneus Produzidos:",
            min_value=0, max_value=5000,
            value=int(e.get("produzidos", 0)),
        )
        defeitos = col6.number_input(
            "Pneus com Defeito / Refugo:",
            min_value=0, max_value=5000,
            value=int(e.get("defeitos", 0)),
        )

        salvar = st.form_submit_button("💾 Salvar Lançamento", type="primary", width="stretch")

    # ── Validação e salvamento ────────────────────────────────────────────────
    if salvar:
        tempo_disp = colab_pres * turno
        paradas    = par_plan + par_nplan
        erros = []
        if colab_pres > colab_total:
            erros.append("Colab. Presentes não pode ser maior que o total.")
        if paradas > tempo_disp and tempo_disp > 0:
            erros.append(
                f"Paradas ({paradas:.2f}h) excedem o tempo disponível ({tempo_disp:.2f}h)."
            )
        if defeitos > produzidos:
            erros.append("Defeitos não podem ser maiores que pneus produzidos.")

        if erros:
            for e_msg in erros:
                st.error(f"⚠️ {e_msg}")
        else:
            dados["lancamentos"][chave] = {
                "colab_total":     colab_total,
                "colab_presentes": colab_pres,
                "paradas_plan_h":  par_plan,
                "paradas_nplan_h": par_nplan,
                "produzidos":      produzidos,
                "defeitos":        defeitos,
            }
            salvar_oee(dados)
            st.session_state.oee_dados = dados
            # Flag de sucesso para próxima renderização — SEM st.rerun()
            st.session_state["_lanc_salvo"] = data_sel.strftime("%d/%m/%Y")

    # ── Preview dos indicadores calculados ────────────────────────────────────
    if chave in dados.get("lancamentos", {}):
        c = calcular_dia(dados["lancamentos"][chave], config)
        st.markdown("---")
        st.markdown("#### 📊 Indicadores Calculados")

        if c["produzidos"] == 0:
            st.warning("Nenhum pneu produzido — OEE não calculado para este dia.")
        else:
            # Cards de indicadores OEE
            c1, c2, c3, c4 = st.columns(4)
            _indicador_card("🏆 OEE",           c["oee"],            c1)
            _indicador_card("⏱️ Disponibilidade", c["disponibilidade"], c2)
            _indicador_card("⚡ Desempenho",     c["desempenho"],     c3)
            _indicador_card("✅ Qualidade",      c["qualidade"],      c4)

            st.markdown("<br>", unsafe_allow_html=True)
            s = status_oee(c["oee"])
            if "Ótimo" in s:
                st.success(f"**{s}** — Resultado excelente para hoje!")
            elif "Bom" in s:
                st.warning(f"**{s}** — Bom resultado, próximo da meta!")
            else:
                st.error(f"**{s}** — Atenção: OEE abaixo do esperado.")

            # Detalhes técnicos
            st.markdown("#### 🔍 Detalhamento")
            col_d1, col_d2, col_d3, col_d4 = st.columns(4)
            col_d1.metric("Colab. Ausentes",  c["colab_ausentes"])
            col_d2.metric("Tempo Disp. (h)",  f"{c['tempo_disp']:.1f}h")
            col_d3.metric("Tempo Oper. (h)",  f"{c['tempo_oper']:.1f}h")
            col_d4.metric("Paradas Total (h)", f"{c['paradas_total_h']:.1f}h")

            col_d5, col_d6, col_d7, col_d8 = st.columns(4)
            col_d5.metric("Pneus/Homem/dia",  f"{c['pneus_homem_dia']:.0f}")
            col_d6.metric("Pneus a Produzir", c["pneus_a_produzir"])
            col_d7.metric("Aprovados",         c["aprovados"])
            col_d8.metric("Defeitos",          c["defeitos"])

    # ── Tabela resumo do mês ──────────────────────────────────────────────────
    st.markdown("---")
    mes_atual = data_sel.strftime("%Y-%m")
    dias_mes  = sorted(
        [(k, v) for k, v in dados["lancamentos"].items() if k.startswith(mes_atual)],
        key=lambda x: x[0],
    )
    if not dias_mes:
        return

    st.markdown(f"#### 📅 Resumo de {data_sel.strftime('%B %Y').capitalize()}")
    rows = []
    for k, lanc in dias_mes:
        dt = datetime.date.fromisoformat(k)
        c  = calcular_dia(lanc, config)
        rows.append({
            "Data":               dt.strftime("%d/%m/%Y"),
            "Dia da Semana":      dt.strftime("%A"),
            "Total Colab.":       c["colab_total"],
            "Colab. Presentes":   c["colab_presentes"],
            "Colab. Ausentes":    c["colab_ausentes"],
            "T. Disp.(h)":        round(c["tempo_disp"],     2),
            "Par. Plan.(h)":      round(c["paradas_plan_h"], 2),
            "Par. N.Plan.(h)":    round(c["paradas_nplan_h"],2),
            "T. Oper.(h)":        round(c["tempo_oper"],     2),
            "Pneus/Homem/dia":    round(c["pneus_homem_dia"],1),
            "Pneus a Produzir":   c["pneus_a_produzir"],
            "Pneus Produzidos":   c["produzidos"],
            "Pneus Defeito":      c["defeitos"],
            "Pneus Aprovados":    c["aprovados"],
            "Disponib. (A)":      f"{c['disponibilidade']*100:.2f}%",
            "Desempenho (P)":     f"{c['desempenho']*100:.2f}%",
            "Qualidade (Q)":      f"{c['qualidade']*100:.2f}%",
            "OEE (%)":            f"{c['oee']*100:.2f}%",
            "Status":             status_oee(c["oee"]) if c["produzidos"] > 0 else "—",
        })

    # Linha TOTAIS / MÉDIAS
    dias_prod = [r for r in rows if r["Pneus Produzidos"] > 0]
    if dias_prod:
        n = len(dias_prod)
        def _avg_pct(col):
            vals = [float(r[col].replace("%", "")) for r in dias_prod]
            return f"{sum(vals)/n:.2f}%"

        rows.append({
            "Data":               "TOTAIS / MÉDIAS",
            "Dia da Semana":      f"({n} dias c/ prod.)",
            "Total Colab.":       "",
            "Colab. Presentes":   round(sum(r["Colab. Presentes"] for r in dias_prod) / n, 1),
            "Colab. Ausentes":    round(sum(r["Colab. Ausentes"]  for r in dias_prod) / n, 1),
            "T. Disp.(h)":        round(sum(r["T. Disp.(h)"]     for r in dias_prod), 2),
            "Par. Plan.(h)":      round(sum(r["Par. Plan.(h)"]   for r in dias_prod), 2),
            "Par. N.Plan.(h)":    round(sum(r["Par. N.Plan.(h)"] for r in dias_prod), 2),
            "T. Oper.(h)":        round(sum(r["T. Oper.(h)"]     for r in dias_prod), 2),
            "Pneus/Homem/dia":    round(sum(r["Pneus/Homem/dia"] for r in dias_prod) / n, 1),
            "Pneus a Produzir":   round(sum(r["Pneus a Produzir"] for r in dias_prod) / n),
            "Pneus Produzidos":   sum(r["Pneus Produzidos"] for r in dias_prod),
            "Pneus Defeito":      sum(r["Pneus Defeito"]   for r in dias_prod),
            "Pneus Aprovados":    sum(r["Pneus Aprovados"]  for r in dias_prod),
            "Disponib. (A)":      _avg_pct("Disponib. (A)"),
            "Desempenho (P)":     _avg_pct("Desempenho (P)"),
            "Qualidade (Q)":      _avg_pct("Qualidade (Q)"),
            "OEE (%)":            _avg_pct("OEE (%)"),
            "Status":             "",
        })

    df_tab = pd.DataFrame(rows)
    # "Total Colab." tem string "" na linha de totais e int nas demais → str
    if "Total Colab." in df_tab.columns:
        df_tab["Total Colab."] = df_tab["Total Colab."].astype(str)
    # Colab. Presentes/Ausentes: int nas linhas, float na de totais → float
    for _c in ["Colab. Presentes", "Colab. Ausentes"]:
        if _c in df_tab.columns:
            df_tab[_c] = pd.to_numeric(df_tab[_c], errors="coerce")
    st.dataframe(df_tab, hide_index=True, width="stretch")
    st.caption(
        "📌 TOTAIS = soma · MÉDIAS = média dos dias com produção  |  "
        "🟢 OEE ≥85% · 🟡 65–84% · 🟠 45–64% · 🔴 <45%"
    )
