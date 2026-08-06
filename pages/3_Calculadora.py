from __future__ import annotations

from datetime import date

import streamlit as st

from auth import restaurar_cliente_autenticado


st.set_page_config(
    page_title="Calculadora",
    page_icon="🧮",
    layout="wide",
)

if not st.session_state.get("autenticado"):
    st.warning("Faça login pela página inicial.")
    st.stop()

empresa_id = st.session_state.get("empresa_ativa_id")
empresa_nome = st.session_state.get("empresa_ativa_nome")

if not empresa_id:
    st.warning("Nenhuma empresa ativa foi encontrada.")
    st.stop()

supabase = restaurar_cliente_autenticado()

st.title("🧮 Calculadora de preço de venda")
st.caption(f"Empresa: {empresa_nome}")

try:
    resposta_produtos = (
        supabase.table("produtos")
        .select("id, nome")
        .eq("empresa_id", empresa_id)
        .eq("ativo", True)
        .order("nome")
        .execute()
    )

    produtos = resposta_produtos.data or []

except Exception as exc:
    st.error(f"Erro ao carregar produtos: {exc}")
    st.stop()

if not produtos:
    st.warning(
        "Cadastre pelo menos um produto na página Produtos."
    )
    st.stop()

opcoes_produtos = {
    produto["nome"]: produto["id"]
    for produto in produtos
}

with st.form("form_calculadora"):
    produto_nome = st.selectbox(
        "Produto",
        options=list(opcoes_produtos.keys()),
    )

    coluna1, coluna2 = st.columns(2)

    with coluna1:
        mes_referencia = st.date_input(
            "Mês de referência",
            value=date.today().replace(day=1),
        )

        quantidade_produzida = st.number_input(
            "Quantidade produzida no mês",
            min_value=1,
            value=100,
            step=1,
        )

        custo_direto = st.number_input(
            "Custo direto por peça",
            min_value=0.0,
            step=1.0,
            format="%.2f",
        )

    with coluna2:
        margem = st.number_input(
            "Margem desejada (%)",
            min_value=0.0,
            max_value=99.0,
            value=30.0,
            step=1.0,
        )

        imposto = st.number_input(
            "Impostos (%)",
            min_value=0.0,
            max_value=99.0,
            value=0.0,
            step=0.1,
        )

        taxa_maquineta = st.number_input(
            "Taxa da maquineta (%)",
            min_value=0.0,
            max_value=99.0,
            value=0.0,
            step=0.1,
        )

    calcular = st.form_submit_button(
        "Calcular preço",
        type="primary",
        use_container_width=True,
    )

if calcular:
    try:
        inicio_mes = mes_referencia.replace(day=1).isoformat()

        resposta_despesas = (
            supabase.table("despesas")
            .select("valor")
            .eq("empresa_id", empresa_id)
            .eq("mes_referencia", inicio_mes)
            .execute()
        )

        despesas_mes = sum(
            float(item["valor"])
            for item in (resposta_despesas.data or [])
        )

        rateio_fixo = despesas_mes / quantidade_produzida
        custo_total = custo_direto + rateio_fixo

        percentual_total = (
            margem + imposto + taxa_maquineta
        ) / 100

        if percentual_total >= 1:
            st.error(
                "A soma da margem, impostos e taxas "
                "deve ser inferior a 100%."
            )
            st.stop()

        preco_venda = custo_total / (1 - percentual_total)
        lucro_estimado = preco_venda * (margem / 100)

        st.subheader("Resultado")

        coluna1, coluna2, coluna3, coluna4 = st.columns(4)

        coluna1.metric(
            "Despesas do mês",
            f"R$ {despesas_mes:,.2f}",
        )

        coluna2.metric(
            "Rateio fixo por peça",
            f"R$ {rateio_fixo:,.2f}",
        )

        coluna3.metric(
            "Custo total por peça",
            f"R$ {custo_total:,.2f}",
        )

        coluna4.metric(
            "Preço sugerido",
            f"R$ {preco_venda:,.2f}",
        )

        st.write(
            f"Lucro estimado por unidade: "
            f"**R$ {lucro_estimado:,.2f}**"
        )

    except Exception as exc:
        st.error(f"Erro ao calcular o preço: {exc}")