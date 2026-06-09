"""
Tela 1 — Dashboard OEE (espelha aba "📊 Dashboard OEE" da planilha).
Visual profissional com cards coloridos, tabela de resumo diário e gráfico de tendência.
"""
import streamlit as st
import pandas as pd
import datetime
from modules.database import calcular_dia, agregar_mes, status_oee, mes_pt


# ── Helpers visuais ───────────────────────────────────────────────────────────

def _cor(v: float) -> str:
    if v >= 0.85: return "#2E7D32"
    if v >= 0.65: return "#F9A825"
    if v >= 0.45: return "#E65100"
    return "#C62828"


def _pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def _card_oee(label: str, valor: float, icon: str, col) -> None:
    cor = _cor(valor)
    pct = min(valor * 100, 100.0)
    col.markdown(
        f'<div style="background:#1A2236;border-radius:12px;padding:18px 14px;'
        f'box-shadow:0 4px 16px rgba(0,0,0,.5);border-top:5px solid {cor};'
        f'border:1px solid #2A3548;text-align:center;">'
        f'<div style="font-size:11px;color:#9AA3B2;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:.9px;margin-bottom:8px;">{icon}&nbsp;{label}</div>'
        f'<div style="font-size:2.6rem;font-weight:900;color:{cor};line-height:1;">{pct:.1f}%</div>'
        f'<div style="background:#2A3548;border-radius:6px;height:8px;margin-top:10px;">'
        f'<div style="background:{cor};width:{pct:.1f}%;height:8px;border-radius:6px;'
        f'transition:width .4s ease;"></div></div>'
        f'<div style="font-size:10px;color:{cor};margin-top:5px;font-weight:600;">'
        f'{"▲ Acima da meta" if valor >= 0.85 else ("▶ Na zona alvo" if valor >= 0.65 else "▼ Abaixo da meta")}'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def _mini_card(label: str, valor: str, icon: str = "") -> str:
    return (
        f'<div style="background:#1A2236;border-radius:8px;padding:12px;'
        f'box-shadow:0 2px 8px rgba(0,0,0,.4);border:1px solid #2A3548;text-align:center;">'
        f'<div style="font-size:10px;color:#9AA3B2;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:.7px;">{icon} {label}</div>'
        f'<div style="font-size:1.35rem;font-weight:800;color:#4FC3F7;margin-top:4px;">{valor}</div>'
        f'</div>'
    )


# ── Tela principal ─────────────────────────────────────────────────────────────

def tela_dashboard():
    dados   = st.session_state.oee_dados
    config  = dados.get("config", {})
    lancs   = dados.get("lancamentos", {})
    manual  = dados.get("analise_manual", {})
    hoje    = datetime.date.today()
    mes_iso = hoje.strftime("%Y-%m")

    # ── Header ────────────────────────────────────────────────────────────────
    agg = agregar_mes(lancs, config, mes_iso)
    mes_label = mes_pt(hoje)

    cor_header = _cor(agg["oee"]) if agg else "#003366"
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#003366 0%,#0066CC 100%);
                padding:22px 28px;border-radius:12px;margin-bottom:24px;
                display:flex;justify-content:space-between;align-items:center;">
        <div>
            <h2 style="color:white;margin:0;font-size:1.7rem;font-weight:800;">
                📊 Dashboard OEE — NSA Pneutec
            </h2>
            <p style="color:rgba(255,255,255,.75);margin:4px 0 0;font-size:.9rem;">
                Eficiência Global da Produção · {mes_label}
            </p>
        </div>
        {'<div style="background:rgba(255,255,255,.15);border-radius:8px;padding:8px 16px;text-align:center;">'
         f'<div style="color:white;font-size:.75rem;font-weight:700;text-transform:uppercase;">OEE do Mês</div>'
         f'<div style="color:white;font-size:1.8rem;font-weight:900;">{agg["oee"]*100:.1f}%</div>'
         '</div>' if agg else ''}
    </div>
    """, unsafe_allow_html=True)

    # ── Card do último lançamento ─────────────────────────────────────────────
    _ult_chave = max((k for k in lancs if k.startswith(mes_iso)), default=None) or (
        max(lancs.keys(), default=None)
    )
    if _ult_chave:
        _ult_lanc = lancs[_ult_chave]
        _ult_c    = calcular_dia(_ult_lanc, config)
        _ult_dt   = datetime.date.fromisoformat(_ult_chave)
        _DIAS_PT  = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
        _ult_dia  = _DIAS_PT[_ult_dt.weekday()]
        _diff_prod = _ult_c["produzidos"] - _ult_c["pneus_a_produzir"]
        _cor_diff  = "#4CAF50" if _diff_prod >= 0 else "#EF5350"
        _sinal     = "+" if _diff_prod >= 0 else ""
        st.markdown(
            f'<div style="background:#1A2236;border:1px solid #2A3548;border-radius:12px;'
            f'padding:16px 20px;margin-bottom:20px;">'
            f'<div style="font-size:11px;color:#9AA3B2;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:.8px;margin-bottom:10px;">📌 Último Lançamento — '
            f'{_ult_dia}, {_ult_dt.strftime("%d/%m/%Y")}</div>'
            f'<div style="display:flex;gap:12px;flex-wrap:wrap;">'
            # Colab. Presentes
            f'<div style="flex:1;min-width:120px;background:#0D2137;border-radius:8px;padding:12px;text-align:center;">'
            f'<div style="font-size:10px;color:#9AA3B2;font-weight:700;text-transform:uppercase;">👥 Colab. Presentes</div>'
            f'<div style="font-size:2rem;font-weight:900;color:#4FC3F7;">{_ult_c["colab_presentes"]}</div>'
            f'<div style="font-size:10px;color:#9AA3B2;">de {_ult_c["colab_total"]} total</div>'
            f'</div>'
            # Pneus por Homem/dia
            f'<div style="flex:1;min-width:120px;background:#0D2137;border-radius:8px;padding:12px;text-align:center;">'
            f'<div style="font-size:10px;color:#9AA3B2;font-weight:700;text-transform:uppercase;">🔧 Pneus / Homem / Dia</div>'
            f'<div style="font-size:2rem;font-weight:900;color:#4FC3F7;">{_ult_c["pneus_homem_dia"]}</div>'
            f'<div style="font-size:10px;color:#9AA3B2;">{int(config.get("pneus_colab_mes",180))} pneus/homem/mês</div>'
            f'</div>'
            # Pneus a Produzir
            f'<div style="flex:1;min-width:120px;background:#0D2137;border-radius:8px;padding:12px;text-align:center;">'
            f'<div style="font-size:10px;color:#9AA3B2;font-weight:700;text-transform:uppercase;">🎯 Pneus a Produzir</div>'
            f'<div style="font-size:2rem;font-weight:900;color:#4FC3F7;">{_ult_c["pneus_a_produzir"]}</div>'
            f'<div style="font-size:10px;color:#9AA3B2;">{_ult_c["colab_presentes"]} × {_ult_c["pneus_homem_dia"]} pneus/H/dia</div>'
            f'</div>'
            # Pneus Produzidos
            f'<div style="flex:1;min-width:120px;background:#0D2137;border-radius:8px;padding:12px;text-align:center;">'
            f'<div style="font-size:10px;color:#9AA3B2;font-weight:700;text-transform:uppercase;">✅ Pneus Produzidos</div>'
            f'<div style="font-size:2rem;font-weight:900;color:#E8EAF0;">{_ult_c["produzidos"]}</div>'
            f'<div style="font-size:10px;color:{_cor_diff};font-weight:700;">{_sinal}{_diff_prod} vs meta do dia</div>'
            f'</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    # ── Indicadores do mês atual ──────────────────────────────────────────────
    st.markdown(f"#### Indicadores de {mes_label}")

    if agg:
        c1, c2, c3, c4 = st.columns(4)
        _card_oee("OEE Geral",       agg["oee"],        "🏆", c1)
        _card_oee("Disponibilidade", agg["disponib"],   "⏱️", c2)
        _card_oee("Desempenho",      agg["desempenho"], "⚡", c3)
        _card_oee("Qualidade",       agg["qualidade"],  "✅", c4)

        st.markdown("<br>", unsafe_allow_html=True)

        meta_m   = agg["meta_mensal"]
        pct_meta = agg["produzido"] / meta_m if meta_m else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("🔢 Total Produzido",    f"{agg['produzido']:,}")
        k2.metric("✅ Aprovados",          f"{agg['aprovados']:,}")
        k3.metric("❌ Defeitos",           str(agg["defeitos"]))
        k4.metric("🎯 Meta Mensal",        f"{int(meta_m):,}")

        _pneus_hd = int(round(float(config.get("pneus_colab_mes", 180)) / max(float(config.get("dias_uteis", 20)), 1)))
        _pneus_hm = int(config.get("pneus_colab_mes", 180))
        k5, k6, k7, k8 = st.columns(4)
        k5.metric("📈 % da Meta",          f"{pct_meta*100:.1f}%")
        k6.metric("👥 Colab. Presentes",   f"{agg['media_colab']:.1f}")
        k7.metric("🔧 Pneus/Homem Dia",    str(_pneus_hd))
        k8.metric("📦 Pneus/Homem Mês",    str(_pneus_hm))

        # Status banner
        s = status_oee(agg["oee"], mensal=True)
        if "World Class" in s:
            st.success(f"**{s}** — OEE de {_pct(agg['oee'])} · Meta ≥ 85% ✓")
        elif "Bom" in s:
            st.warning(f"**{s}** — OEE de {_pct(agg['oee'])} · Faixa 65–84%")
        elif "Regular" in s:
            st.error(f"**{s}** — OEE de {_pct(agg['oee'])} · Faixa 45–64%")
        else:
            st.error(f"**{s}** — OEE de {_pct(agg['oee'])} · Abaixo de 45%")
    else:
        st.info(
            f"Nenhum lançamento com produção em **{mes_label}**. "
            "Acesse **📋 Lançamento Diário** para registrar a produção."
        )

    # ── Histórico comparativo (meses anteriores) ──────────────────────────────
    st.markdown("---")
    meses_anteriores = []
    for i in range(1, 6):
        dt = hoje.replace(day=1) - datetime.timedelta(days=1)
        for _ in range(i - 1):
            dt = dt.replace(day=1) - datetime.timedelta(days=1)
        mi = dt.strftime("%Y-%m")
        a = agregar_mes(lancs, config, mi)
        if not a:
            a = manual.get(mi)
            if a:
                a = dict(a)
        if a and isinstance(a, dict) and a.get("oee"):
            meses_anteriores.append((dt.strftime("%b/%Y"), a))

    if meses_anteriores:
        st.markdown("#### 📅 Meses Anteriores")
        cols = st.columns(min(len(meses_anteriores), 5))
        for i, (label, m) in enumerate(meses_anteriores[:5]):
            oee_v = m.get("oee", 0)
            cor   = _cor(oee_v)
            html  = (
                f'<div style="background:#1A2236;border-radius:10px;padding:12px;'
                f'box-shadow:0 2px 8px rgba(0,0,0,.4);border-left:4px solid {cor};'
                f'border:1px solid #2A3548;text-align:center;">'
                f'<div style="font-size:10px;color:#9AA3B2;font-weight:700;">{label}</div>'
                f'<div style="font-size:1.4rem;font-weight:900;color:{cor};">{oee_v*100:.1f}%</div>'
                f'<div style="font-size:10px;color:{cor};">{status_oee(oee_v, mensal=True)}</div>'
                f'</div>'
            )
            cols[i].markdown(html, unsafe_allow_html=True)

    # ── Resumo diário do mês ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📋 Resumo Diário — " + mes_label)

    _feriados = dados.get("feriados", {})
    dias_mes  = sorted(
        [(k, v) for k, v in lancs.items() if k.startswith(mes_iso)],
        key=lambda x: x[0],
    )
    _feriados_mes  = {k: v for k, v in _feriados.items() if k.startswith(mes_iso)}
    _todas_datas   = sorted(set(k for k, _ in dias_mes) | set(_feriados_mes.keys()))

    if not _todas_datas:
        st.info("Sem lançamentos no mês atual.")
        return

    _DIAS_PT_ABR = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    rows = []
    for chave in _todas_datas:
        dt       = datetime.date.fromisoformat(chave)
        _is_fer  = chave in _feriados
        _fer_lbl = ("🔴 " + _feriados[chave]) if _is_fer else ""
        _dia_abr = _DIAS_PT_ABR[dt.weekday()]

        if chave in lancs:
            lanc = lancs[chave]
            prod = int(lanc.get("produzidos", 0))
            c    = calcular_dia(lanc, config)
            if _is_fer and prod > 0:
                _status = "⭐ Hora Extra"
            elif prod > 0:
                _status = status_oee(c["oee"])
            else:
                _status = "🔴 Não Trabalhado" if _is_fer else "—"
            rows.append({
                "Data":                 dt.strftime("%d/%m/%Y"),
                "Dia":                  _dia_abr,
                "Feriado":              _fer_lbl,
                "Colab. Pres.":         c["colab_presentes"],
                "Pneus por Homem/dia":  int(round(c["pneus_homem_dia"])),
                "Pneus a Produzir":     c["pneus_a_produzir"],
                "Pneus Produzidos":     prod,
                "Aprovados":            c["aprovados"],
                "Defeitos":             c["defeitos"],
                "Disponib.":            f"{c['disponibilidade']*100:.1f}%" if prod > 0 else "—",
                "Desempenho":           f"{c['desempenho']*100:.1f}%" if prod > 0 else "—",
                "Qualidade":            f"{c['qualidade']*100:.1f}%" if prod > 0 else "—",
                "OEE":                  f"{c['oee']*100:.1f}%" if prod > 0 else "—",
                "Status":               _status,
            })
        else:
            # Feriado sem lançamento
            rows.append({
                "Data":                 dt.strftime("%d/%m/%Y"),
                "Dia":                  _dia_abr,
                "Feriado":              _fer_lbl,
                "Colab. Pres.":         0,
                "Pneus por Homem/dia":  "—",
                "Pneus a Produzir":     0,
                "Pneus Produzidos":     0,
                "Aprovados":            0,
                "Defeitos":             0,
                "Disponib.":            "—",
                "Desempenho":           "—",
                "Qualidade":            "—",
                "OEE":                  "—",
                "Status":               "🔴 Não Trabalhado",
            })

    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    # ── Gráfico de tendência ──────────────────────────────────────────────────
    df_chart = pd.DataFrame([
        {
            "Data": r["Data"],
            "OEE %": float(r["OEE"].replace("%", "")) if r["OEE"] != "—" else None,
        }
        for r in rows
    ]).dropna()

    if not df_chart.empty:
        col_g, col_ref = st.columns([3, 1])
        with col_g:
            st.markdown("#### 📉 Tendência OEE do Mês")
            st.line_chart(df_chart.set_index("Data")[["OEE %"]], height=220)
        with col_ref:
            st.markdown("#### Classificação")
            st.markdown(
                "| OEE | Classificação |\n"
                "|---|---|\n"
                "| ≥ 85% | 🟢 World Class |\n"
                "| 65–84% | 🟡 Bom |\n"
                "| 45–64% | 🟠 Regular |\n"
                "| < 45% | 🔴 Crítico |\n\n"
                "---\n"
                "**OEE = A × P × Q**\n\n"
                "A = T.Oper / T.Disp\n\n"
                "P = Produzido / Meta\n\n"
                "Q = Aprovados / Total"
            )
