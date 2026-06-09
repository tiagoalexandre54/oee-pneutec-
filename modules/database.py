"""
Persistência dos dados de OEE + cálculos centrais.
Banco: data/oee.json (local) + GitHub opcional (mesmo repo do ERP).

Estrutura:
{
  "_schema": 2,
  "config": { "meta_diaria":360, "pneus_colab_mes":180, "turno_horas":8.8, "dias_uteis":20 },
  "lancamentos": {
    "2026-05-04": {
      "colab_total":34, "colab_presentes":31,
      "paradas_plan_h":0.0, "paradas_nplan_h":0.0,
      "produzidos":290, "defeitos":2
    }
  },
  "analise_manual": {
    "2026-01": {
      "dias_uteis":21, "produzido":6790, "aprovados":6779,
      "defeitos":11, "disponib":0.95, "desempenho":0.898,
      "qualidade":0.998, "oee":0.8513938, "meta_mensal":7560
    }
  }
}
"""
import json
import datetime
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
_OEE_JSON = _BASE_DIR / "data" / "oee.json"
_SCHEMA   = 2
_OEE_PATH_GITHUB = "data/oee.json"

_CONFIG_PADRAO = {
    "meta_diaria":     360,
    "pneus_colab_mes": 180,
    "turno_horas":     8.8,
    "dias_uteis":      20,
    "metas_mensais":   {},   # {"2026-01": 7200, "2026-02": 6480, ...}
}
_DADOS_PADRAO = {
    "_schema":       _SCHEMA,
    "config":        _CONFIG_PADRAO.copy(),
    "lancamentos":   {},
    "analise_manual": {},
    "feriados":      {},   # {"2026-06-12": "Corpus Christi", ...}
}


# ── GitHub helpers ────────────────────────────────────────────────────────────

def _token() -> str:
    try:
        import streamlit as st
        t = st.secrets.get("github", {}).get("token", "")
        if t and t.strip():
            return t.strip()
    except Exception:
        pass
    import os
    return os.environ.get("GITHUB_TOKEN", "")


def _modo_github() -> bool:
    return bool(_token())


def _github_cfg():
    t = _token()
    try:
        import streamlit as st
        cfg    = st.secrets.get("github", {})
        repo   = cfg.get("repo",   "tiagoalexandre54/nsa-erp-pneutec")
        branch = cfg.get("branch", "main")
    except Exception:
        repo   = "tiagoalexandre54/nsa-erp-pneutec"
        branch = "main"
    return t, repo, branch


def _ler_github() -> dict | None:
    try:
        import requests, base64
        t, repo, branch = _github_cfg()
        url = f"https://api.github.com/repos/{repo}/contents/{_OEE_PATH_GITHUB}?ref={branch}"
        r = requests.get(url, headers={"Authorization": f"token {t}"}, timeout=8)
        if r.status_code == 200:
            return json.loads(base64.b64decode(r.json()["content"]).decode("utf-8"))
    except Exception:
        pass
    return None


def _salvar_github(dados: dict) -> None:
    try:
        import requests, base64
        t, repo, branch = _github_cfg()
        url     = f"https://api.github.com/repos/{repo}/contents/{_OEE_PATH_GITHUB}"
        headers = {"Authorization": f"token {t}"}
        b64     = base64.b64encode(
            json.dumps(dados, ensure_ascii=False, indent=2).encode()
        ).decode()
        r   = requests.get(url, headers=headers, timeout=5)
        sha = r.json().get("sha") if r.status_code == 200 else None
        payload = {"message": "Atualiza OEE", "content": b64, "branch": branch}
        if sha:
            payload["sha"] = sha
        requests.put(url, json=payload, headers=headers, timeout=15)
    except Exception:
        pass


# ── Carga / Salvamento ────────────────────────────────────────────────────────

def carregar_oee() -> dict:
    dados = None
    if _modo_github():
        dados = _ler_github()
    if dados is None and _OEE_JSON.exists():
        try:
            dados = json.loads(_OEE_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    if dados is None or dados.get("_schema") != _SCHEMA:
        return dict(_DADOS_PADRAO)
    dados.setdefault("config", _CONFIG_PADRAO.copy())
    dados.setdefault("lancamentos", {})
    dados.setdefault("analise_manual", {})
    dados.setdefault("feriados", {})
    return dados


def salvar_oee(dados: dict) -> None:
    dados["_schema"] = _SCHEMA
    conteudo = json.dumps(dados, ensure_ascii=False, indent=2)
    try:
        _OEE_JSON.parent.mkdir(parents=True, exist_ok=True)
        tmp = _OEE_JSON.with_suffix(".tmp")
        tmp.write_text(conteudo, encoding="utf-8")
        tmp.replace(_OEE_JSON)
    except Exception:
        pass
    if _modo_github():
        _salvar_github(dados)


# ── Cálculo diário ────────────────────────────────────────────────────────────

def calcular_dia(lanc: dict, config: dict) -> dict:
    """
    Calcula todos os campos derivados para um lançamento diário.

    Fórmulas (idênticas à planilha OEE Maio NSA PNEUTEC):
      pneus_homem_dia  = pneus_colab_mes / dias_uteis
      tempo_disp       = colab_presentes × turno_horas
      tempo_oper       = tempo_disp − paradas_plan − paradas_nplan
      Disponib (A)     = tempo_oper / tempo_disp
      Desempenho (P)   = produzidos / meta_diaria
      Aprovados        = produzidos − defeitos
      Qualidade (Q)    = aprovados / produzidos
      OEE              = A × P × Q
    """
    meta_dia        = float(config.get("meta_diaria",     360))
    pneus_colab_mes = float(config.get("pneus_colab_mes", 180))
    turno           = float(config.get("turno_horas",     8.8))
    dias_uteis      = float(config.get("dias_uteis",       20))

    colab_total    = int(lanc.get("colab_total",    0))
    colab_pres     = int(lanc.get("colab_presentes", 0))
    par_plan       = float(lanc.get("paradas_plan_h",  0))
    par_nplan      = float(lanc.get("paradas_nplan_h", 0))
    produzidos     = int(lanc.get("produzidos", 0))
    defeitos       = int(lanc.get("defeitos",   0))

    colab_aus      = colab_total - colab_pres
    pneus_hd       = int(round(pneus_colab_mes / dias_uteis)) if dias_uteis > 0 else 0
    pneus_a_prod   = colab_pres * pneus_hd
    tempo_disp     = round(colab_pres * turno, 4)
    paradas_total  = par_plan + par_nplan
    tempo_oper     = max(round(tempo_disp - paradas_total, 4), 0.0)

    disponib   = (tempo_oper / tempo_disp)  if tempo_disp > 0 else 0.0
    desempenho = min(produzidos / meta_dia, 1.0) if meta_dia > 0 else 0.0
    aprovados  = max(produzidos - defeitos, 0)
    qualidade  = (aprovados / produzidos) if produzidos > 0 else 0.0
    oee        = disponib * desempenho * qualidade

    return {
        "colab_total":    colab_total,
        "colab_presentes": colab_pres,
        "colab_ausentes":  colab_aus,
        "paradas_plan_h":  par_plan,
        "paradas_nplan_h": par_nplan,
        "paradas_total_h": paradas_total,
        "tempo_disp":      tempo_disp,
        "tempo_oper":      tempo_oper,
        "pneus_homem_dia": pneus_hd,
        "pneus_a_produzir": pneus_a_prod,
        "produzidos":      produzidos,
        "defeitos":        defeitos,
        "aprovados":       aprovados,
        "disponibilidade": disponib,
        "desempenho":      desempenho,
        "qualidade":       qualidade,
        "oee":             oee,
    }


def status_oee(oee: float, mensal: bool = False) -> str:
    rotulo = "World Class" if mensal else "Ótimo"
    if oee >= 0.85: return f"🟢 {rotulo}"
    if oee >= 0.65: return "🟡 Bom"
    if oee >= 0.45: return "🟠 Regular"
    return "🔴 Crítico"


# ── Agregação mensal a partir de lançamentos ──────────────────────────────────

def agregar_mes(lancamentos: dict, config: dict, mes_iso: str) -> dict | None:
    """
    Agrega indicadores mensais a partir dos lançamentos diários de um mês (ex: '2026-05').
    Retorna None se não houver lançamentos com produção para o mês.
    """
    dias_prod = [
        (k, v) for k, v in lancamentos.items()
        if k.startswith(mes_iso) and int(v.get("produzidos", 0)) > 0
    ]
    if not dias_prod:
        return None

    calcs = [calcular_dia(v, config) for _, v in dias_prod]
    meta_diaria   = float(config.get("meta_diaria", 360))
    dias_uteis    = int(config.get("dias_uteis", 20))
    metas_mensais = config.get("metas_mensais", {})
    # Usa meta específica do mês se cadastrada; caso contrário, meta global
    meta_custom = metas_mensais.get(mes_iso)
    meta_mensal = float(meta_custom) if meta_custom else (meta_diaria * dias_uteis)

    n = len(calcs)
    return {
        "dias_com_producao": n,
        "produzido":   sum(c["produzidos"]    for c in calcs),
        "aprovados":   sum(c["aprovados"]     for c in calcs),
        "defeitos":    sum(c["defeitos"]      for c in calcs),
        "disponib":    sum(c["disponibilidade"] for c in calcs) / n,
        "desempenho":  sum(c["desempenho"]    for c in calcs) / n,
        "qualidade":   sum(c["qualidade"]     for c in calcs) / n,
        "oee":         sum(c["oee"]           for c in calcs) / n,
        "meta_mensal": meta_mensal,
        "media_colab": sum(c["colab_presentes"] for c in calcs) / n,
    }
