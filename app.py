import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
import pandas as pd
import plotly.express as px

# ------------------- Cargar datos -------------------
df_serie = pd.read_parquet("china_serie_mensual.parquet")
df_ranking = pd.read_parquet("china_ranking_mercaderias.parquet")
df_puerto = pd.read_parquet("china_mercaderia_puerto.parquet")

# Ajustar columna fecha
df_serie["fecha"] = pd.to_datetime(
    dict(year=df_serie["anio"], month=df_serie["mes"], day=1)
)

# Listas únicas para dropdowns
MERCADERIAS = sorted(df_ranking["mercaderia"].dropna().unique().tolist())
PUERTOS = sorted(df_puerto["aduana"].dropna().unique().tolist())

# ------------------- Instancia Dash -------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)
server = app.server

# ------------------- Header -------------------
header = html.Header(
    dbc.Container(
        dbc.Row(
            [
                dbc.Col(
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Img(
                                    src="/assets/CAMBRA.png",
                                    style={"height": "80px", "width": "auto"},
                                ),
                                width="auto",
                            ),
                            dbc.Col(
                                html.H1(
                                    "Análisis de Puertos de Importación del Paraguay",
                                    className="m-0",
                                    style={
                                        "fontFamily": "Avenir, sans-serif",
                                        "fontWeight": "700",
                                        "fontSize": "2rem",
                                        "textAlign": "center",
                                        "color": "#333",
                                    },
                                ),
                                align="center",
                            ),
                        ],
                        align="center",
                    ),
                    width=10,
                ),
            ],
            justify="center",
            className="py-3",
        )
    ),
    style={"backgroundColor": "white"},
)

# ------------------- Layout -------------------
app.layout = dbc.Container([

    header,

    # Filtros
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    html.Label("Mercadería"),
                    dcc.Dropdown(
                        id="china-mercaderia",
                        options=[{"label": m, "value": m} for m in MERCADERIAS],
                        multi=True,
                        placeholder="Seleccione mercaderías..."
                    )
                ], md=4, sm=12),
                dbc.Col([
                    html.Label("Puerto (Aduana)"),
                    dcc.Dropdown(
                        id="china-puerto",
                        options=[{"label": p, "value": p} for p in PUERTOS],
                        multi=True,
                        placeholder="Seleccione puertos..."
                    )
                ], md=4, sm=12),
                dbc.Col([
                    html.Label("Período"),
                    dcc.RangeSlider(
                        id="china-periodo",
                        min=df_serie["anio"].min(),
                        max=df_serie["anio"].max(),
                        value=[df_serie["anio"].min(), df_serie["anio"].max()],
                        marks={str(y): str(y) for y in sorted(df_serie["anio"].unique())}
                    )
                ], md=4, sm=12),
            ])
        ], md=10, sm=12)
    ], className="mb-4 justify-content-center"),

    # KPIs
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Volumen total (Kg Neto)"), html.H3(id="kpi-kilo")])), md=3, sm=6),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Valor total (Gs)"), html.H3(id="kpi-total")])), md=3, sm=6),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Flete total (USD)"), html.H3(id="kpi-flete")])), md=3, sm=6),
        dbc.Col(dbc.Card(dbc.CardBody([html.H6("Seguro total (USD)"), html.H3(id="kpi-seguro")])), md=3, sm=6),
    ], className="mb-4 justify-content-center"),

    # Serie temporal
    dbc.Row([
        dbc.Col([
            dcc.Tabs(id="china-tabs-temporal", value="kilo", children=[
                dcc.Tab(label="Volumen (Kg Neto)", value="kilo"),
                dcc.Tab(label="Valor (Gs)", value="valor"),
                dcc.Tab(label="Flete (USD)", value="flete"),
                dcc.Tab(label="Seguro (USD)", value="seguro"),
            ]),
            dcc.Graph(id="china-linea-temporal")
        ], md=10, sm=12)
    ], className="mb-4 justify-content-center"),

    # Ranking mercaderías
    dbc.Row([
        dbc.Col([
            html.H4("Top mercaderías importadas desde China"),
            dcc.Graph(id="china-ranking-mercaderias")
        ], md=10, sm=12)
    ], className="mb-4 justify-content-center"),

    # Composición por puerto (Treemap)
    dbc.Row([
        dbc.Col([
            html.H4("Composición de mercaderías por puerto (Treemap)"),
            dcc.Graph(id="china-treemap-puerto")
        ], md=10, sm=12)
    ], className="mb-4 justify-content-center"),

    # Tabla detalle
    dbc.Row([
        dbc.Col([
            html.H4("Detalle de mercaderías filtradas"),
            dcc.Graph(id="china-tabla-detalle")  # uso Graph con table de Plotly
        ], md=10, sm=12)
    ], className="mb-4 justify-content-center"),

], fluid=True)

# ------------------- Callbacks -------------------

@app.callback(
    Output("kpi-kilo", "children"),
    Output("kpi-total", "children"),
    Output("kpi-flete", "children"),
    Output("kpi-seguro", "children"),
    Output("china-linea-temporal", "figure"),
    Output("china-ranking-mercaderias", "figure"),
    Output("china-treemap-puerto", "figure"),
    Output("china-tabla-detalle", "figure"),
    Input("china-mercaderia", "value"),
    Input("china-puerto", "value"),
    Input("china-periodo", "value"),
    Input("china-tabs-temporal", "value")
)
def actualizar_dashboard(mercaderias, puertos, periodo, tab_temporal):
    # --- Filtros base ---
    df_f = df_serie.copy()
    df_r = df_ranking.copy()
    df_p = df_puerto.copy()

    anio_min, anio_max = periodo
    df_f = df_f[(df_f["anio"] >= anio_min) & (df_f["anio"] <= anio_max)]

    if mercaderias:
        df_r = df_r[df_r["mercaderia"].isin(mercaderias)]
        df_p = df_p[df_p["mercaderia"].isin(mercaderias)]
    if puertos:
        df_p = df_p[df_p["aduana"].isin(puertos)]

    # --- KPIs (usar ranking para sumar flete/seguro y volumen global) ---
    total_kilo = df_r["kilo_neto"].sum()
    total_valor = df_r["total_gs"].sum()
    total_flete = df_r["flete_usd"].sum()
    total_seguro = df_r["seguro_usd"].sum()

    # --- Serie temporal ---
    if tab_temporal == "kilo":
        fig_temporal = px.line(df_f, x="fecha", y="kilo_neto", title="Evolución de Volumen (Kg Neto)")
    elif tab_temporal == "valor":
        fig_temporal = px.line(df_f, x="fecha", y="total_gs", title="Evolución de Valor (Gs)")
    elif tab_temporal == "flete":
        fig_temporal = px.line(df_f, x="fecha", y="flete_usd", title="Evolución de Flete (USD)")
    else:
        fig_temporal = px.line(df_f, x="fecha", y="seguro_usd", title="Evolución de Seguro (USD)")

    # --- Ranking mercaderías ---
    top_rank = df_r.sort_values("total_gs", ascending=False).head(20)
    fig_rank = px.bar(top_rank, x="total_gs", y="mercaderia",
                      orientation="h", title="Top mercaderías (por valor Gs)")

    # --- Treemap por puerto ---
    if not df_p.empty:
        fig_tree = px.treemap(df_p, path=["aduana", "mercaderia"], values="total_gs",
                              title="Composición de mercaderías por puerto (valor Gs)")
    else:
        fig_tree = px.treemap(title="Sin datos")

    # --- Tabla detalle ---
    cols = ["mercaderia", "kilo_neto", "total_gs", "flete_usd", "seguro_usd"]
    table_data = df_r.sort_values("total_gs", ascending=False).head(50)[cols]
    fig_table = go.Figure(data=[go.Table(
        header=dict(values=table_data.columns, fill_color="lightgrey", align="left"),
        cells=dict(values=[table_data[c] for c in table_data.columns], align="left")
    )])

    return (
        f"{total_kilo:,.0f}",
        f"{total_valor:,.0f}",
        f"{total_flete:,.0f}",
        f"{total_seguro:,.0f}",
        fig_temporal,
        fig_rank,
        fig_tree,
        fig_table
    )


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
