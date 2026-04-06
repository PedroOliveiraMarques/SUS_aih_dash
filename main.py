# -*- coding: utf-8 -*-
"""
Dashboard SUS — AIH  |  FUNASA / DataIESB
Dash (Python) + design do dashboard HTML premium
"""

import pandas as pd
from sqlalchemy import create_engine
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import os

load_dotenv()

print("Iniciando Dashboard FUNASA - AIH...")

# ═══════════════════════════════════════════════
# 1. CONEXÃO E DADOS
# ═══════════════════════════════════════════════
url_conexao = (
    f"mssql+pymssql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(url_conexao, pool_pre_ping=True)

query = """
SELECT TOP 80000
    ano_aih, mes_aih, nome_municipio, regiao_nome, uf_sigla,
    municipio_capital, numero_habitantes,
    qtd_total, vl_total,
    qtd_01, qtd_02, qtd_03, qtd_04, qtd_05, qtd_06, qtd_07, qtd_08,
    vl_02, vl_03, vl_04, vl_05, vl_06, vl_07, vl_08
FROM dbo.sus_aih
WHERE ano_aih >= 2018
"""

print("Carregando dados do banco...")
df = pd.read_sql_query(query, engine)
print(f"Dados carregados com sucesso! → {len(df):,} registros")

# ═══════════════════════════════════════════════
# 2. LIMPEZA
# ═══════════════════════════════════════════════
numeric_cols = [
    'vl_total', 'qtd_total',
    'qtd_01','qtd_02','qtd_03','qtd_04','qtd_05','qtd_06','qtd_07','qtd_08',
    'vl_02','vl_03','vl_04','vl_05','vl_06','vl_07','vl_08',
    'numero_habitantes'
    # municipio_capital removido — contém texto "Sim"/"Não", tratado abaixo
]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# municipio_capital: banco armazena "Sim" / "Não" como texto
if 'municipio_capital' in df.columns:
    df['municipio_capital'] = (
        df['municipio_capital']
        .astype(str).str.strip().str.capitalize()
        .map({'Sim': 1, 'Não': 0, 'Nao': 0})
        .fillna(0).astype(int)
    )

df['ano_aih'] = df['ano_aih'].astype(int)
df['mes_aih'] = pd.to_numeric(df['mes_aih'], errors='coerce').fillna(1).astype(int)

# Listas para filtros
regioes = sorted([r for r in df['regiao_nome'].dropna().unique() if r])
anos    = sorted(df['ano_aih'].unique())
ufs     = sorted([u for u in df['uf_sigla'].dropna().unique() if u])

# ═══════════════════════════════════════════════
# 3. PALETA DE CORES
# ═══════════════════════════════════════════════
AZUIS    = ['#0D2B55','#1565C0','#1976D2','#2196F3','#42A5F5','#90CAF9','#BBDEFB']
VERDES   = ['#1B5E20','#2E7D32','#388E3C','#43A047','#66BB6A','#A5D6A7','#C8E6C9']
AMARELOS = ['#E65100','#EF6C00','#F57C00','#FB8C00','#FFA726','#FFB300','#FFD54F']
MIX6     = [AZUIS[1], VERDES[1], AMARELOS[2], AZUIS[3], VERDES[3], AMARELOS[4]]

REGIOES_COLOR = {
    'Norte':        AZUIS[2],
    'Nordeste':     AMARELOS[2],
    'Centro-Oeste': VERDES[2],
    'Sudeste':      AZUIS[0],
    'Sul':          VERDES[0],
}

PLOTLY_LAYOUT = dict(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family='DM Sans, sans-serif', color='#0D1F3C'),
    margin=dict(l=16, r=16, t=12, b=12),
    hoverlabel=dict(bgcolor='#0D2B55', font_color='white', font_size=13),
)

# ═══════════════════════════════════════════════
# 4. FORMATADORES
# ═══════════════════════════════════════════════
def fmtBRL(v):
    if v >= 1e9: return f'R$ {v/1e9:.2f}B'
    if v >= 1e6: return f'R$ {v/1e6:.1f}M'
    if v >= 1e3: return f'R$ {v/1e3:.1f}K'
    return f'R$ {v:,.2f}'

def fmtNum(v):
    if v >= 1e6: return f'{v/1e6:.1f}M'
    if v >= 1e3: return f'{v/1e3:.1f}K'
    return f'{int(round(v)):,}'.replace(',', '.')

# ═══════════════════════════════════════════════
# 5. APP + INDEX STRING (CSS PREMIUM)
# ═══════════════════════════════════════════════
app = dash.Dash(__name__, title="Dashboard SUS · AIH · FUNASA")

app.index_string = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    {%metas%}
    <title>Dashboard SUS · AIH · FUNASA</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
    {%css%}
    <style>
      :root {
        --azul-profundo:    #0D2B55;
        --azul-medio:       #1565C0;
        --azul-claro:       #42A5F5;
        --azul-fraco:       #E3F2FD;
        --verde-forte:      #1B5E20;
        --verde-medio:      #2E7D32;
        --verde-claro:      #66BB6A;
        --verde-fraco:      #E8F5E9;
        --amarelo:          #FFB300;
        --amarelo-claro:    #FFF8E1;
        --branco:           #FFFFFF;
        --cinza-fundo:      #F4F7FB;
        --cinza-borda:      #DDE3ED;
        --texto-principal:  #0D1F3C;
        --texto-secundario: #5A6A82;
        --sombra-card:      0 2px 16px rgba(13,43,85,0.10);
        --sombra-forte:     0 8px 32px rgba(13,43,85,0.16);
      }

      *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

      body {
        font-family: 'DM Sans', sans-serif;
        background: var(--cinza-fundo);
        color: var(--texto-principal);
        min-height: 100vh;
      }

      /* ── HEADER ───────────────────────────────────── */
      header {
        background: linear-gradient(135deg, var(--azul-profundo) 0%, var(--azul-medio) 60%, var(--verde-medio) 100%);
        position: sticky;
        top: 0;
        z-index: 100;
        box-shadow: 0 4px 24px rgba(13,43,85,0.22);
      }
      .header-inner {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 18px 40px;
        flex-wrap: wrap;
        gap: 12px;
      }
      .header-brand { display: flex; align-items: center; gap: 18px; }
      .header-badge {
        background: var(--amarelo);
        color: var(--azul-profundo);
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.15rem;
        letter-spacing: 2px;
        padding: 6px 16px;
        border-radius: 4px;
        font-weight: 700;
      }
      .header-title h1 {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2rem;
        letter-spacing: 3px;
        color: #fff;
        line-height: 1;
        margin: 0;
      }
      .header-title p {
        font-size: 0.82rem;
        color: rgba(255,255,255,0.72);
        letter-spacing: 1px;
        margin-top: 2px;
      }
      .header-meta { display: flex; gap: 8px; align-items: center; }
      .status-dot {
        width: 10px; height: 10px;
        background: var(--verde-claro);
        border-radius: 50%;
        animation: pulse 2s infinite;
      }
      @keyframes pulse {
        0%   { box-shadow: 0 0 0 0   rgba(102,187,106,0.7); }
        70%  { box-shadow: 0 0 0 8px rgba(102,187,106,0);   }
        100% { box-shadow: 0 0 0 0   rgba(102,187,106,0);   }
      }
      .status-text {
        font-size: 0.78rem;
        color: rgba(255,255,255,0.75);
        font-family: 'DM Mono', monospace;
      }

      /* ── FILTROS ──────────────────────────────────── */
      .filter-bar {
        background: var(--branco);
        border-bottom: 2px solid var(--cinza-borda);
        padding: 14px 40px;
        display: flex;
        gap: 20px;
        align-items: center;
        flex-wrap: wrap;
      }
      .filter-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--texto-secundario);
        letter-spacing: 1.5px;
        text-transform: uppercase;
        white-space: nowrap;
      }
      .Select-control {
        border-radius: 6px !important;
        border-color: var(--cinza-borda) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.85rem !important;
        background: var(--cinza-fundo) !important;
      }
      .btn-reset {
        background: var(--azul-profundo) !important;
        color: white !important;
        border: none !important;
        padding: 7px 18px !important;
        border-radius: 6px !important;
        font-size: 0.82rem !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        cursor: pointer;
        letter-spacing: .5px;
        transition: background .2s;
      }
      .btn-reset:hover { background: var(--azul-medio) !important; }

      /* ── MAIN ─────────────────────────────────────── */
      main { padding: 32px 40px; }

      /* ── KPI CARDS ────────────────────────────────── */
      .kpi-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 18px;
        margin-bottom: 28px;
      }
      .kpi-card {
        background: var(--branco);
        border-radius: 12px;
        padding: 22px 26px;
        box-shadow: var(--sombra-card);
        border-left: 5px solid transparent;
        display: flex;
        flex-direction: column;
        gap: 6px;
        transition: transform .18s, box-shadow .18s;
        position: relative;
        overflow: hidden;
      }
      .kpi-card:hover { transform: translateY(-3px); box-shadow: var(--sombra-forte); }
      .kpi-card.azul    { border-left-color: var(--azul-medio); }
      .kpi-card.verde   { border-left-color: var(--verde-medio); }
      .kpi-card.amarelo { border-left-color: var(--amarelo); }
      .kpi-card.ciano   { border-left-color: var(--azul-claro); }
      .kpi-card::after {
        content: '';
        position: absolute;
        top: -30px; right: -30px;
        width: 90px; height: 90px;
        border-radius: 50%;
        opacity: .07;
      }
      .kpi-card.azul::after    { background: var(--azul-medio); }
      .kpi-card.verde::after   { background: var(--verde-medio); }
      .kpi-card.amarelo::after { background: var(--amarelo); }
      .kpi-card.ciano::after   { background: var(--azul-claro); }

      .kpi-label {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: var(--texto-secundario);
      }
      .kpi-value {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.4rem;
        line-height: 1;
        letter-spacing: 1px;
      }
      .kpi-value.azul    { color: var(--azul-medio); }
      .kpi-value.verde   { color: var(--verde-medio); }
      .kpi-value.amarelo { color: #C67C00; }
      .kpi-value.ciano   { color: var(--azul-claro); }
      .kpi-sub { font-size: 0.78rem; color: var(--texto-secundario); }

      /* ── CHART CARDS ──────────────────────────────── */
      .charts-row { display: grid; gap: 22px; margin-bottom: 28px; }
      .charts-row.cols-2 { grid-template-columns: 1fr 1fr; }
      .charts-row.cols-3 { grid-template-columns: 2fr 1fr 1fr; }
      .charts-row.cols-1 { grid-template-columns: 1fr; }

      .chart-card {
        background: var(--branco);
        border-radius: 12px;
        padding: 24px 26px;
        box-shadow: var(--sombra-card);
        display: flex;
        flex-direction: column;
        gap: 14px;
        transition: box-shadow .18s;
      }
      .chart-card:hover { box-shadow: var(--sombra-forte); }
      .chart-header { display: flex; align-items: flex-start; justify-content: space-between; }
      .chart-title { font-size: 0.98rem; font-weight: 600; color: var(--texto-principal); line-height: 1.3; }
      .chart-subtitle { font-size: 0.76rem; color: var(--texto-secundario); margin-top: 2px; }
      .chart-tag {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        padding: 3px 10px;
        border-radius: 20px;
        white-space: nowrap;
      }
      .tag-azul    { background: var(--azul-fraco);    color: var(--azul-medio);  }
      .tag-verde   { background: var(--verde-fraco);   color: var(--verde-forte); }
      .tag-amarelo { background: var(--amarelo-claro); color: #7A4800;            }

      /* ── FOOTER ───────────────────────────────────── */
      footer {
        text-align: center;
        padding: 22px 40px;
        font-size: 0.75rem;
        color: var(--texto-secundario);
        border-top: 1px solid var(--cinza-borda);
        background: var(--branco);
        margin-top: 10px;
      }
      footer span { color: var(--azul-medio); font-weight: 600; }

      /* ── RESPONSIVO ───────────────────────────────── */
      @media (max-width: 900px) {
        .charts-row.cols-2,
        .charts-row.cols-3 { grid-template-columns: 1fr; }
        main, .filter-bar, .header-inner { padding-left: 16px; padding-right: 16px; }
      }
    </style>
</head>
<body>
    {%app_entry%}
    {%config%}
    {%scripts%}
    {%renderer%}
</body>
</html>
'''

# ═══════════════════════════════════════════════
# 6. LAYOUT
# ═══════════════════════════════════════════════
app.layout = html.Div([

    # ── HEADER ──────────────────────────────────
    html.Header(
        html.Div(className='header-inner', children=[
            html.Div(className='header-brand', children=[
                html.Div('FUNASA', className='header-badge'),
                html.Div([
                    html.H1('Dashboard SUS — AIH'),
                    html.P('AUTORIZAÇÃO DE INTERNAÇÃO HOSPITALAR · ANÁLISE INTERATIVA'),
                ], className='header-title'),
            ]),
            html.Div(className='header-meta', children=[
                html.Div(className='status-dot'),
                html.Span('Conectado ao banco de dados', className='status-text'),
            ]),
        ])
    ),

    # ── FILTROS ─────────────────────────────────
    html.Div(className='filter-bar', children=[
        html.Span('Filtros', className='filter-label'),
        dcc.Dropdown(
            id='filtro-regiao',
            options=[{'label': r, 'value': r} for r in regioes],
            placeholder='Todas as regiões',
            clearable=True,
            style={'width': '220px', 'fontFamily': 'DM Sans, sans-serif', 'fontSize': '0.85rem'},
        ),
        dcc.Dropdown(
            id='filtro-ano',
            options=[{'label': str(a), 'value': a} for a in anos],
            placeholder='Todos os anos',
            clearable=True,
            style={'width': '150px', 'fontFamily': 'DM Sans, sans-serif', 'fontSize': '0.85rem'},
        ),
        dcc.Dropdown(
            id='filtro-uf',
            options=[{'label': u, 'value': u} for u in ufs],
            placeholder='Todas as UFs',
            clearable=True,
            style={'width': '150px', 'fontFamily': 'DM Sans, sans-serif', 'fontSize': '0.85rem'},
        ),
        html.Button('↺  Limpar Filtros', id='btn-limpar', n_clicks=0, className='btn-reset'),
    ]),

    # ── MAIN ────────────────────────────────────
    html.Main(style={'padding': '32px 40px'}, children=[

        # KPIs
        html.Div(className='kpi-row', id='kpi-row'),

        # Row 1 — Barras Região + Rosca UF
        html.Div(className='charts-row cols-2', children=[
            html.Div(className='chart-card', children=[
                html.Div(className='chart-header', children=[
                    html.Div([
                        html.Div('Gasto Total por Região', className='chart-title'),
                        html.Div('Valor consolidado em R$ por macrorregião', className='chart-subtitle'),
                    ]),
                    html.Span('BARRAS', className='chart-tag tag-azul'),
                ]),
                dcc.Graph(id='chart-regiao', style={'height': '320px'}, config={'displayModeBar': False}),
            ]),
            html.Div(className='chart-card', children=[
                html.Div(className='chart-header', children=[
                    html.Div([
                        html.Div('Distribuição por UF (Top 10)', className='chart-title'),
                        html.Div('Participação percentual no gasto total', className='chart-subtitle'),
                    ]),
                    html.Span('ROSCA', className='chart-tag tag-amarelo'),
                ]),
                dcc.Graph(id='chart-uf', style={'height': '380px'}, config={'displayModeBar': False}),
            ]),
        ]),

        # Row 2 — Linha Evolução + Procedimentos Horizontal
        html.Div(className='charts-row cols-2', children=[
            html.Div(className='chart-card', children=[
                html.Div(className='chart-header', children=[
                    html.Div([
                        html.Div('Evolução Anual do Gasto', className='chart-title'),
                        html.Div('Tendência histórica por ano de AIH', className='chart-subtitle'),
                    ]),
                    html.Span('LINHA', className='chart-tag tag-verde'),
                ]),
                dcc.Graph(id='chart-evolucao', style={'height': '320px'}, config={'displayModeBar': False}),
            ]),
            html.Div(className='chart-card', children=[
                html.Div(className='chart-header', children=[
                    html.Div([
                        html.Div('Grupos de Procedimentos', className='chart-title'),
                        html.Div('Volume de AIHs por grupo (qtd_01 a qtd_08)', className='chart-subtitle'),
                    ]),
                    html.Span('HORIZONTAL', className='chart-tag tag-azul'),
                ]),
                dcc.Graph(id='chart-procedimentos', style={'height': '320px'}, config={'displayModeBar': False}),
            ]),
        ]),

        # Row 3 — Gasto Mensal Empilhado + Capitais vs Interior
        html.Div(className='charts-row cols-2', children=[
            html.Div(className='chart-card', children=[
                html.Div(className='chart-header', children=[
                    html.Div([
                        html.Div('Gasto Mensal por Região', className='chart-title'),
                        html.Div('Distribuição de valores ao longo dos meses', className='chart-subtitle'),
                    ]),
                    html.Span('MENSAL', className='chart-tag tag-verde'),
                ]),
                dcc.Graph(id='chart-mensal', style={'height': '320px'}, config={'displayModeBar': False}),
            ]),
            html.Div(className='chart-card', children=[
                html.Div(className='chart-header', children=[
                    html.Div([
                        html.Div('Capitais vs Interior', className='chart-title'),
                        html.Div('Comparativo de AIHs e gastos totais', className='chart-subtitle'),
                    ]),
                    html.Span('COMPARATIVO', className='chart-tag tag-amarelo'),
                ]),
                dcc.Graph(id='chart-capital', style={'height': '320px'}, config={'displayModeBar': False}),
            ]),
        ]),

        # Row 4 — Top 10 Municípios
        html.Div(className='charts-row cols-1', children=[
            html.Div(className='chart-card', children=[
                html.Div(className='chart-header', children=[
                    html.Div([
                        html.Div('Top 10 Municípios por Gasto Total', className='chart-title'),
                        html.Div('Ranking com valor total de AIHs e número de procedimentos', className='chart-subtitle'),
                    ]),
                    html.Span('RANKING', className='chart-tag tag-azul'),
                ]),
                dcc.Graph(id='chart-top-mun', style={'height': '400px'}, config={'displayModeBar': False}),
            ]),
        ]),
    ]),

    # ── FOOTER ──────────────────────────────────
    html.Footer([
        'Dashboard SUS · AIH — ',
        html.Span('FUNASA / DataIESB'),
        ' · Fonte: Sistema de Informações Hospitalares (SIH/SUS)',
    ]),
])


# ═══════════════════════════════════════════════
# 7. CALLBACK
# ═══════════════════════════════════════════════
@app.callback(
    [
        Output('kpi-row',            'children'),
        Output('chart-regiao',       'figure'),
        Output('chart-uf',           'figure'),
        Output('chart-evolucao',     'figure'),
        Output('chart-procedimentos','figure'),
        Output('chart-mensal',       'figure'),
        Output('chart-capital',      'figure'),
        Output('chart-top-mun',      'figure'),
    ],
    [
        Input('filtro-regiao', 'value'),
        Input('filtro-ano',    'value'),
        Input('filtro-uf',     'value'),
        Input('btn-limpar',    'n_clicks'),
    ]
)
def atualizar(regiao, ano, uf, _n):

    # Filtragem
    dff = df.copy()
    if regiao: dff = dff[dff['regiao_nome'] == regiao]
    if ano:    dff = dff[dff['ano_aih']     == ano]
    if uf:     dff = dff[dff['uf_sigla']    == uf]

    # ── KPIs ──────────────────────────────────
    total_qtd  = dff['qtd_total'].sum()
    total_vl   = dff['vl_total'].sum()
    total_mun  = dff['nome_municipio'].nunique()
    ticket     = total_vl / total_qtd if total_qtd > 0 else 0

    kpis = [
        html.Div(className='kpi-card azul', children=[
            html.Div('Total de AIHs',           className='kpi-label'),
            html.Div(fmtNum(total_qtd),         className='kpi-value azul'),
            html.Div('Procedimentos registrados',className='kpi-sub'),
        ]),
        html.Div(className='kpi-card verde', children=[
            html.Div('Valor Total',             className='kpi-label'),
            html.Div(fmtBRL(total_vl),          className='kpi-value verde'),
            html.Div('Gasto consolidado (R$)',  className='kpi-sub'),
        ]),
        html.Div(className='kpi-card amarelo', children=[
            html.Div('Municípios',              className='kpi-label'),
            html.Div(fmtNum(total_mun),         className='kpi-value amarelo'),
            html.Div('Com registros ativos',    className='kpi-sub'),
        ]),
        html.Div(className='kpi-card ciano', children=[
            html.Div('Ticket Médio',            className='kpi-label'),
            html.Div(fmtBRL(ticket),            className='kpi-value ciano'),
            html.Div('Por internação (R$)',     className='kpi-sub'),
        ]),
    ]

    # ── GRÁFICO 1 — Barras por Região ─────────
    df_reg = (dff.groupby('regiao_nome')['vl_total']
                 .sum().reset_index()
                 .sort_values('vl_total', ascending=False))
    colors_reg = [REGIOES_COLOR.get(r, AZUIS[2]) for r in df_reg['regiao_nome']]

    fig_reg = go.Figure(go.Bar(
        x=df_reg['regiao_nome'],
        y=df_reg['vl_total'],
        marker_color=colors_reg,
        marker_line_width=0,
        hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>',
    ))
    fig_reg.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(title='', showgrid=False, tickfont=dict(size=12, family='DM Sans')),
        yaxis=dict(title='Gasto Total (R$)', showgrid=True, gridcolor='#EEF2F7', tickformat=',.0f'),
        showlegend=False,
        bargap=0.35,
    )
    fig_reg.update_traces(marker_cornerradius=5)

    # ── GRÁFICO 2 — Rosca UF ──────────────────
    df_uf = (dff.groupby('uf_sigla')['vl_total']
                .sum().nlargest(10).reset_index())
    uf_colors = (AZUIS[:4] + VERDES[:3] + AMARELOS[:3])

    fig_uf = go.Figure(go.Pie(
        labels=df_uf['uf_sigla'],
        values=df_uf['vl_total'],
        hole=0.60,
        marker_colors=uf_colors,
        textfont=dict(family='DM Sans', size=12),
        hovertemplate='<b>%{label}</b><br>R$ %{value:,.0f}<br>%{percent}<extra></extra>',
    ))
    fig_uf.update_layout(**PLOTLY_LAYOUT)
    fig_uf.update_layout(
        legend=dict(orientation='v', x=1.02, y=0.5, font=dict(family='DM Sans', size=12)),
        margin=dict(l=16, r=120, t=12, b=12),
    )

    # ── GRÁFICO 3 — Linha Evolução Anual ──────
    df_ano = dff.groupby('ano_aih')['vl_total'].sum().reset_index().sort_values('ano_aih')

    fig_evo = go.Figure()
    fig_evo.add_trace(go.Scatter(
        x=df_ano['ano_aih'], y=df_ano['vl_total'],
        mode='lines+markers',
        line=dict(color=VERDES[1], width=3),
        marker=dict(size=8, color=VERDES[1], line=dict(color='white', width=2)),
        fill='tozeroy',
        fillcolor='rgba(46,125,50,0.10)',
        hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>',
    ))
    fig_evo.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(title='Ano', showgrid=False, tickfont=dict(family='DM Mono', size=11)),
        yaxis=dict(title='Gasto Total (R$)', showgrid=True, gridcolor='#EEF2F7', tickformat=',.0f'),
        showlegend=False,
    )

    # ── GRÁFICO 4 — Procedimentos Horizontal ──
    grupos = ['qtd_01','qtd_02','qtd_03','qtd_04','qtd_05','qtd_06','qtd_07','qtd_08']
    nomes  = ['Ações Clínicas','Proc. Diagnósticos','Proc. Clínicos','Proc. Cirúrgicos',
              'Transplantes','Medicamentos','Órteses/Próteses','Ações Especiais']
    totais = [dff[g].sum() for g in grupos]
    proc_colors = MIX6 + [AZUIS[3], VERDES[3]]

    fig_proc = go.Figure(go.Bar(
        x=totais,
        y=nomes,
        orientation='h',
        marker_color=proc_colors,
        marker_line_width=0,
        hovertemplate='<b>%{y}</b><br>%{x:,.0f} AIHs<extra></extra>',
    ))
    fig_proc.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(title='Qtd. AIHs', showgrid=True, gridcolor='#EEF2F7', tickformat=',.0f'),
        yaxis=dict(title='', autorange='reversed', showgrid=False, tickfont=dict(size=11)),
        showlegend=False,
        bargap=0.30,
    )
    fig_proc.update_traces(marker_cornerradius=4)

    # ── GRÁFICO 5 — Gasto Mensal Empilhado ────
    nomes_mes = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
    fig_mensal = go.Figure()
    for i, reg in enumerate(sorted(dff['regiao_nome'].dropna().unique())):
        sub = dff[dff['regiao_nome'] == reg]
        vals = [sub[sub['mes_aih'] == m]['vl_total'].sum() for m in range(1, 13)]
        fig_mensal.add_trace(go.Bar(
            name=reg,
            x=nomes_mes,
            y=vals,
            marker_color=REGIOES_COLOR.get(reg, MIX6[i % len(MIX6)]),
            hovertemplate=f'<b>{reg}</b><br>%{{x}}<br>R$ %{{y:,.0f}}<extra></extra>',
        ))
    fig_mensal.update_layout(
        **PLOTLY_LAYOUT,
        barmode='stack',
        xaxis=dict(title='', showgrid=False),
        yaxis=dict(title='Gasto (R$)', showgrid=True, gridcolor='#EEF2F7', tickformat=',.0f'),
        legend=dict(orientation='h', y=-0.18, font=dict(family='DM Sans', size=11)),
        bargap=0.20,
    )

    # ── GRÁFICO 6 — Capitais vs Interior ──────
    cap = dff[dff['municipio_capital'] == 1] if 'municipio_capital' in dff.columns else dff.iloc[0:0]
    int_ = dff[dff['municipio_capital'] == 0] if 'municipio_capital' in dff.columns else dff

    vl_cap  = cap['vl_total'].sum()
    vl_int  = int_['vl_total'].sum()
    qtd_cap = cap['qtd_total'].sum()
    qtd_int = int_['qtd_total'].sum()

    fig_cap = go.Figure()
    fig_cap.add_trace(go.Bar(
        name='Gasto Total (R$)', x=['Capitais', 'Interior'], y=[vl_cap, vl_int],
        marker_color=[AZUIS[1], VERDES[1]], marker_line_width=0, yaxis='y',
        hovertemplate='<b>%{x}</b><br>R$ %{y:,.0f}<extra></extra>',
    ))
    fig_cap.add_trace(go.Bar(
        name='Qtd AIHs', x=['Capitais', 'Interior'], y=[qtd_cap, qtd_int],
        marker_color=['rgba(247,124,0,0.80)', 'rgba(33,150,243,0.80)'], marker_line_width=0, yaxis='y2',
        hovertemplate='<b>%{x}</b><br>%{y:,.0f} AIHs<extra></extra>',
    ))
    fig_cap.update_layout(
        **PLOTLY_LAYOUT,
        barmode='group',
        xaxis=dict(showgrid=False),
        yaxis=dict(title='Gasto (R$)', showgrid=True, gridcolor='#EEF2F7', tickformat=',.0f'),
        yaxis2=dict(title='Qtd AIHs', overlaying='y', side='right', showgrid=False, tickformat=',.0f'),
        legend=dict(orientation='h', y=-0.18, font=dict(family='DM Sans', size=11)),
        bargap=0.30,
    )
    fig_cap.update_traces(marker_cornerradius=4)

    # ── GRÁFICO 7 — Top 10 Municípios ─────────
    df_mun = (dff.groupby('nome_municipio')
                 .agg(vl_total=('vl_total','sum'), qtd_total=('qtd_total','sum'))
                 .nlargest(10, 'vl_total')
                 .reset_index()
                 .sort_values('vl_total'))

    fig_mun = go.Figure(go.Bar(
        x=df_mun['vl_total'],
        y=df_mun['nome_municipio'],
        orientation='h',
        marker=dict(
            color=df_mun['vl_total'],
            colorscale=[[0, AZUIS[4]], [0.5, AZUIS[1]], [1, AZUIS[0]]],
            showscale=False,
            line_width=0,
        ),
        customdata=df_mun['qtd_total'],
        hovertemplate='<b>%{y}</b><br>Gasto: R$ %{x:,.0f}<br>AIHs: %{customdata:,.0f}<extra></extra>',
    ))
    fig_mun.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(title='Gasto Total (R$)', showgrid=True, gridcolor='#EEF2F7', tickformat=',.0f'),
        yaxis=dict(title='', showgrid=False, tickfont=dict(size=12)),
        showlegend=False,
        bargap=0.28,
    )
    fig_mun.update_traces(marker_cornerradius=4)

    return kpis, fig_reg, fig_uf, fig_evo, fig_proc, fig_mensal, fig_cap, fig_mun


# ═══════════════════════════════════════════════
# 8. EXECUÇÃO
# ═══════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=True, port=8050)