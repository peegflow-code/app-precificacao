from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import streamlit as st

from auth import restaurar_cliente_autenticado


# ==========================================================
# SESSÃO
# ==========================================================

empresa_id = st.session_state.get(
    "empresa_ativa_id"
)

empresa_nome = st.session_state.get(
    "empresa_ativa_nome"
)

if not empresa_id:
    st.warning(
        "Nenhuma empresa ativa foi encontrada."
    )
    st.stop()

supabase = restaurar_cliente_autenticado()


# ==========================================================
# FUNÇÕES
# ==========================================================

def formatar_moeda(valor: float) -> str:
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


MESES = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


# ==========================================================
# CABEÇALHO
# ==========================================================

st.title("📊 Visão gerencial")

st.caption(
    f"Indicadores de precificação · {empresa_nome}"
)


# ==========================================================
# FILTRO DE PERÍODO
# ==========================================================

hoje = date.today()

coluna1, coluna2 = st.columns(2)

with coluna1:
    mes_selecionado = st.selectbox(
        "Mês",
        options=range(1, 13),
        index=hoje.month - 1,
        format_func=lambda x: MESES[x - 1],
    )

with coluna2:
    ano_selecionado = st.number_input(
        "Ano",
        min_value=2020,
        max_value=2100,
        value=hoje.year,
        step=1,
    )

inicio_mes = date(
    int(ano_selecionado),
    mes_selecionado,
    1,
).isoformat()

if mes_selecionado == 12:
    fim_mes = date(
        int(ano_selecionado) + 1,
        1,
        1,
    ).isoformat()

else:
    fim_mes = date(
        int(ano_selecionado),
        mes_selecionado + 1,
        1,
    ).isoformat()


# ==========================================================
# CARREGAR PRODUTOS
# ==========================================================

try:
    resposta_produtos = (
        supabase.table("produtos")
        .select(
            "id, nome, categoria, ativo"
        )
        .eq("empresa_id", empresa_id)
        .execute()
    )

    produtos = resposta_produtos.data or []

except Exception as exc:
    st.error(
        f"Erro ao carregar produtos: {exc}"
    )
    st.stop()

produtos_ativos = [
    produto
    for produto in produtos
    if produto.get("ativo")
]

nomes_produtos = {
    produto["id"]: produto["nome"]
    for produto in produtos
}


# ==========================================================
# CARREGAR DESPESAS DO MÊS
# ==========================================================

try:
    resposta_despesas = (
        supabase.table("despesas")
        .select(
            "id, descricao, valor, recorrente"
        )
        .eq("empresa_id", empresa_id)
        .eq("mes_referencia", inicio_mes)
        .execute()
    )

    despesas = resposta_despesas.data or []

except Exception as exc:
    st.error(
        f"Erro ao carregar despesas: {exc}"
    )
    despesas = []

total_despesas = sum(
    float(item.get("valor") or 0)
    for item in despesas
)


# ==========================================================
# CARREGAR CÁLCULOS DO MÊS
# ==========================================================

try:
    resposta_calculos_mes = (
        supabase.table(
            "calculos_precificacao"
        )
        .select(
            "id, produto_id, mes_referencia, "
            "quantidade_produzida, "
            "custo_direto, "
            "rateio_fixo_por_peca, "
            "custo_total_peca, "
            "total_taxas_percentual, "
            "margem_varejo, "
            "preco_varejo, "
            "lucro_varejo_estimado, "
            "criado_em"
        )
        .eq("empresa_id", empresa_id)
        .eq("mes_referencia", inicio_mes)
        .order("criado_em", desc=True)
        .execute()
    )

    calculos_mes = (
        resposta_calculos_mes.data or []
    )

except Exception as exc:
    st.error(
        f"Erro ao carregar cálculos: {exc}"
    )
    calculos_mes = []


# ==========================================================
# INDICADORES
# ==========================================================

quantidade_calculos = len(calculos_mes)

quantidade_produzida = sum(
    int(
        calculo.get(
            "quantidade_produzida"
        )
        or 0
    )
    for calculo in calculos_mes
)

precos = [
    float(
        calculo.get(
            "preco_varejo"
        )
        or 0
    )
    for calculo in calculos_mes
]

custos = [
    float(
        calculo.get(
            "custo_total_peca"
        )
        or 0
    )
    for calculo in calculos_mes
]

margens = [
    float(
        calculo.get(
            "margem_varejo"
        )
        or 0
    )
    for calculo in calculos_mes
]

lucros_unitarios = [
    float(
        calculo.get(
            "lucro_varejo_estimado"
        )
        or 0
    )
    for calculo in calculos_mes
]


preco_medio = (
    sum(precos) / len(precos)
    if precos
    else 0
)

custo_medio = (
    sum(custos) / len(custos)
    if custos
    else 0
)

margem_media = (
    sum(margens) / len(margens)
    if margens
    else 0
)

lucro_unitario_medio = (
    sum(lucros_unitarios)
    / len(lucros_unitarios)
    if lucros_unitarios
    else 0
)


# ==========================================================
# LUCRO E FATURAMENTO DOS LOTES
# ==========================================================

lucro_total_lotes = sum(
    float(
        calculo.get(
            "lucro_varejo_estimado"
        )
        or 0
    )
    * int(
        calculo.get(
            "quantidade_produzida"
        )
        or 0
    )
    for calculo in calculos_mes
)

faturamento_estimado = sum(
    float(
        calculo.get(
            "preco_varejo"
        )
        or 0
    )
    * int(
        calculo.get(
            "quantidade_produzida"
        )
        or 0
    )
    for calculo in calculos_mes
)


# ==========================================================
# CARDS PRINCIPAIS
# ==========================================================

st.subheader(
    f"{MESES[mes_selecionado - 1]} "
    f"de {int(ano_selecionado)}"
)

coluna1, coluna2, coluna3, coluna4 = (
    st.columns(4)
)

coluna1.metric(
    "Produtos ativos",
    len(produtos_ativos),
)

coluna2.metric(
    "Despesas fixas",
    formatar_moeda(total_despesas),
)

coluna3.metric(
    "Cálculos realizados",
    quantidade_calculos,
)

coluna4.metric(
    "Peças consideradas",
    quantidade_produzida,
)


coluna1, coluna2, coluna3 = st.columns(3)

coluna1.metric(
    "Custo médio por peça",
    formatar_moeda(custo_medio),
)

coluna2.metric(
    "Preço médio sugerido",
    formatar_moeda(preco_medio),
)

coluna3.metric(
    "Margem média",
    f"{margem_media:.1f}%",
)


st.divider()


# ==========================================================
# RESULTADOS GERENCIAIS
# ==========================================================

st.subheader("Resultado potencial dos lotes")

coluna1, coluna2, coluna3 = st.columns(3)

coluna1.metric(
    "Faturamento potencial",
    formatar_moeda(
        faturamento_estimado
    ),
)

coluna2.metric(
    "Lucro potencial dos lotes",
    formatar_moeda(
        lucro_total_lotes
    ),
)

coluna3.metric(
    "Lucro médio por unidade",
    formatar_moeda(
        lucro_unitario_medio
    ),
)

st.caption(
    "Os valores de faturamento e lucro são estimativas "
    "baseadas nas quantidades informadas nos cálculos "
    "de precificação. Eles não representam vendas realizadas."
)


# ==========================================================
# GRÁFICOS
# ==========================================================

st.divider()
st.subheader("Análise dos produtos precificados")

if calculos_mes:
    dados_produtos = []

    for calculo in calculos_mes:
        nome = nomes_produtos.get(
            calculo["produto_id"],
            "Produto",
        )

        dados_produtos.append(
            {
                "Produto": nome,
                "Custo": float(
                    calculo[
                        "custo_total_peca"
                    ]
                ),
                "Preço": float(
                    calculo[
                        "preco_varejo"
                    ]
                ),
            }
        )

    df_produtos = pd.DataFrame(
        dados_produtos
    )

    # Se um produto foi calculado várias vezes,
    # utiliza o cálculo mais recente
    df_produtos = (
        df_produtos
        .drop_duplicates(
            subset=["Produto"],
            keep="first",
        )
        .set_index("Produto")
    )

    st.caption(
        "Comparação entre o custo unitário e "
        "o preço sugerido."
    )

    st.bar_chart(
        df_produtos[
            ["Custo", "Preço"]
        ],
        use_container_width=True,
    )

else:
    st.info(
        "Ainda não existem cálculos para "
        "o período selecionado."
    )


# ==========================================================
# DESPESAS
# ==========================================================

st.divider()
st.subheader("Despesas do mês")

if despesas:
    df_despesas = pd.DataFrame(
        [
            {
                "Despesa": item["descricao"],
                "Valor": float(
                    item["valor"]
                ),
            }
            for item in despesas
        ]
    )

    df_despesas = (
        df_despesas
        .groupby(
            "Despesa",
            as_index=False,
        )["Valor"]
        .sum()
        .sort_values(
            "Valor",
            ascending=False,
        )
    )

    st.bar_chart(
        df_despesas.set_index(
            "Despesa"
        ),
        use_container_width=True,
    )

else:
    st.info(
        "Nenhuma despesa cadastrada "
        "para este mês."
    )


# ==========================================================
# ÚLTIMOS CÁLCULOS
# ==========================================================

st.divider()
st.subheader("Últimos cálculos")

if calculos_mes:
    linhas = []

    for calculo in calculos_mes[:10]:
        quantidade = int(
            calculo[
                "quantidade_produzida"
            ]
        )

        lucro_unitario = float(
            calculo[
                "lucro_varejo_estimado"
            ]
        )

        linhas.append(
            {
                "Produto": (
                    nomes_produtos.get(
                        calculo["produto_id"],
                        "Produto",
                    )
                ),
                "Quantidade": quantidade,
                "Custo": float(
                    calculo[
                        "custo_total_peca"
                    ]
                ),
                "Preço sugerido": float(
                    calculo[
                        "preco_varejo"
                    ]
                ),
                "Margem": float(
                    calculo[
                        "margem_varejo"
                    ]
                ),
                "Lucro/unidade": (
                    lucro_unitario
                ),
                "Lucro do lote": (
                    lucro_unitario
                    * quantidade
                ),
            }
        )

    tabela = pd.DataFrame(linhas)

    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Custo": (
                st.column_config.NumberColumn(
                    "Custo",
                    format="R$ %.2f",
                )
            ),
            "Preço sugerido": (
                st.column_config.NumberColumn(
                    "Preço sugerido",
                    format="R$ %.2f",
                )
            ),
            "Margem": (
                st.column_config.NumberColumn(
                    "Margem",
                    format="%.1f%%",
                )
            ),
            "Lucro/unidade": (
                st.column_config.NumberColumn(
                    "Lucro/unidade",
                    format="R$ %.2f",
                )
            ),
            "Lucro do lote": (
                st.column_config.NumberColumn(
                    "Lucro do lote",
                    format="R$ %.2f",
                )
            ),
        },
    )

else:
    st.info(
        "Nenhum cálculo realizado "
        "no período selecionado."
    )