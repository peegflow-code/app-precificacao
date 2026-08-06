from __future__ import annotations

from datetime import date

import streamlit as st

from auth import restaurar_cliente_autenticado


empresa_id = st.session_state.get("empresa_ativa_id")
empresa_nome = st.session_state.get("empresa_ativa_nome")

if not empresa_id:
    st.warning("Nenhuma empresa ativa foi encontrada.")
    st.stop()

supabase = restaurar_cliente_autenticado()


def formatar_moeda(valor: float) -> str:
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


st.title("Visão geral")

st.success(
    f"Empresa ativa: {empresa_nome}"
)

inicio_mes = date.today().replace(day=1).isoformat()

try:
    resposta_produtos = (
        supabase.table("produtos")
        .select("id")
        .eq("empresa_id", empresa_id)
        .eq("ativo", True)
        .execute()
    )

    produtos = resposta_produtos.data or []
    quantidade_produtos = len(produtos)

    resposta_despesas = (
        supabase.table("despesas")
        .select("valor")
        .eq("empresa_id", empresa_id)
        .eq("mes_referencia", inicio_mes)
        .execute()
    )

    despesas = resposta_despesas.data or []

    total_despesas = sum(
        float(item.get("valor") or 0)
        for item in despesas
    )

    resposta_calculos = (
        supabase.table("calculos_precificacao")
        .select("id, preco_varejo, lucro_varejo_estimado")
        .eq("empresa_id", empresa_id)
        .execute()
    )

    calculos = resposta_calculos.data or []
    quantidade_calculos = len(calculos)

    precos = [
        float(item.get("preco_varejo") or 0)
        for item in calculos
    ]

    lucros = [
        float(
            item.get("lucro_varejo_estimado") or 0
        )
        for item in calculos
    ]

    preco_medio = (
        sum(precos) / len(precos)
        if precos
        else 0
    )

    lucro_medio = (
        sum(lucros) / len(lucros)
        if lucros
        else 0
    )

    coluna1, coluna2, coluna3 = st.columns(3)

    coluna1.metric(
        "Produtos ativos",
        quantidade_produtos,
    )

    coluna2.metric(
        "Despesas do mês",
        formatar_moeda(total_despesas),
    )

    coluna3.metric(
        "Cálculos realizados",
        quantidade_calculos,
    )

    coluna1, coluna2 = st.columns(2)

    coluna1.metric(
        "Preço médio calculado",
        formatar_moeda(preco_medio),
    )

    coluna2.metric(
        "Lucro médio por unidade",
        formatar_moeda(lucro_medio),
    )

    st.caption(
        "As despesas consideram o mês atual. "
        "Os cálculos consideram todo o histórico da empresa."
    )

except Exception as exc:
    st.error(
        f"Não foi possível carregar o dashboard: {exc}"
    )