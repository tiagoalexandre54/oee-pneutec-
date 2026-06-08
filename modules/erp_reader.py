"""
Leitura dos dados ao vivo do ERP NSA Pneutec via GitHub raw URL (sem autenticação).
"""
import pandas as pd
import datetime

_URL_ERP = (
    "https://raw.githubusercontent.com/tiagoalexandre54/"
    "nsa-erp-pneutec/main/data/ordens.csv"
)

_COLUNAS = [
    'NRORDEM', 'IDPEDIDOPNEU', 'CLIENTE', 'NRSERIE',
    'DESENHO', 'STATUS', 'DATA_ENTRADA', 'DATA_SAIDA', 'LOCAL_PALLET',
]


def carregar_erp() -> pd.DataFrame:
    """Lê ordens.csv do ERP via URL raw (pública, sem auth)."""
    try:
        df = pd.read_csv(_URL_ERP, dtype=str, keep_default_na=False)
        for col in _COLUNAS:
            if col not in df.columns:
                df[col] = ''
        return df[_COLUNAS].copy()
    except Exception:
        return pd.DataFrame(columns=_COLUNAS)


def _parse_data(s: str) -> datetime.date | None:
    """Converte string de data para datetime.date. Retorna None se inválida."""
    s = str(s).strip()
    if not s:
        return None
    try:
        return pd.to_datetime(s, dayfirst=True, errors='raise').date()
    except Exception:
        return None


def expedidos_por_dia(df: pd.DataFrame) -> dict:
    """Retorna {date: int} de pneus expedidos agrupados por DATA_SAIDA."""
    sub = df[df['STATUS'] == 'Expedido'].copy()
    sub['_dt'] = sub['DATA_SAIDA'].apply(_parse_data)
    sub = sub.dropna(subset=['_dt'])
    return sub.groupby('_dt').size().to_dict()


def produzidos_por_dia(df: pd.DataFrame) -> dict:
    """
    Retorna {date: int} de pneus que entraram na linha (Em Produção ou Expedido)
    agrupados por DATA_ENTRADA — conforme indicado em BASE_DADOS.md.
    """
    sub = df[df['STATUS'].isin(['Em Produção', 'Expedido'])].copy()
    sub['_dt'] = sub['DATA_ENTRADA'].apply(_parse_data)
    sub = sub.dropna(subset=['_dt'])
    return sub.groupby('_dt').size().to_dict()


def resumo_erp(df: pd.DataFrame) -> dict:
    """Retorna contagens rápidas de status para o sidebar."""
    return {
        'total':    len(df),
        'expedido': int((df['STATUS'] == 'Expedido').sum()),
        'em_prod':  int((df['STATUS'] == 'Em Produção').sum()),
        'aguard':   int((df['STATUS'] == 'Aguardando').sum()),
    }
