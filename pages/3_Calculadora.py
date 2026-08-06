from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from auth import restaurar_cliente_autenticado


st.set_page_config(
    page_title="Calculadora",
    page_icon="🧮",
    layout="wide",
)

# ==========================================================
# VALIDAÇÃO DA SESSÃO
# ==========================================================

if not st.session_state.get("autenticado"):
    st.warning("Faça login pela página inicial.")
    st.stop()

empresa_id = st.session_state.get("empresa_ativa_id")
empresa_nome = st.session_state.get("empresa_ativa_nome")

if not empresa_id:
    st.warning("Nenhuma empresa ativa foi encontrada.")
    st.stop()

supabase = restaurar_cliente_autenticado()


# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================

def formatar_moeda(valor: float) -> str:
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# ==========================================================
# CABEÇALHO
# ==========================================================

st.title("🧮 Calculadora de preço de venda")
st.caption(f"Empresa: {empresa_nome}")

if st.session_state.get("mensagem_calculo"):
    st.success(st.session_state.pop("mensagem_calculo"))


# ==========================================================
# CARREGAR PRODUTOS
# ==========================================================

try:
    resposta_produtos = (
        supabase.table("produtos")
        .select("id, nome, codigo, categoria")
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

produtos_por_nome = {
    produto["nome"]: produto
    for produto in produtos
}


# ==========================================================
# FORMULÁRIO DA CALCULADORA
# ==========================================================

with st.form("form_calculadora"):
    produto_nome = st.selectbox(
        "Produto",
        options=list(produtos_por_nome.keys()),
    )

    st.subheader("Parâmetros do mês")

    coluna1, coluna2 = st.columns(2)

    with coluna1:
        mes_referencia = st.date_input(
            "Mês de referência",
            value=date.today().replace(day=1),
        )

    with coluna2:
        quantidade_produzida = st.number_input(
            "Quantidade produzida no mês",
            min_value=1,
            value=100,
            step=1,
        )

    st.subheader("Custos totais do lote")

    st.caption(
        "Informe abaixo os custos totais utilizados para produzir "
        "a quantidade de peças indicada acima."
    )

    coluna1, coluna2 = st.columns(2)

    with coluna1:
        custo_insumos = st.number_input(
            "Total de matéria-prima e insumos do lote",
            min_value=0.0,
            value=0.0,
            step=1.0,
            format="%.2f",
            help=(
                "Informe o valor total dos tecidos, matérias-primas, "
                "aviamentos e demais materiais usados no lote."
            ),
        )

        custo_mao_obra = st.number_input(
            "Total de mão de obra do lote",
            min_value=0.0,
            value=0.0,
            step=1.0,
            format="%.2f",
            help=(
                "Informe o custo total da mão de obra referente "
                "à produção do lote."
            ),
        )

    with coluna2:
        custo_embalagem = st.number_input(
            "Total de embalagens do lote",
            min_value=0.0,
            value=0.0,
            step=1.0,
            format="%.2f",
            help=(
                "Informe o valor total gasto com embalagens "
                "para todas as peças do lote."
            ),
        )

        outros_custos = st.number_input(
            "Outros custos diretos do lote",
            min_value=0.0,
            value=0.0,
            step=1.0,
            format="%.2f",
        )

    # Valores exibidos dinamicamente no formulário
    custo_direto_total_exibicao = (
        float(custo_insumos)
        + float(custo_mao_obra)
        + float(custo_embalagem)
        + float(outros_custos)
    )

    custo_direto_peca_exibicao = (
        custo_direto_total_exibicao
        / quantidade_produzida
    )

    coluna_total, coluna_peca = st.columns(2)

    with coluna_total:
        st.info(
            "Custo direto total do lote: "
            f"**{formatar_moeda(custo_direto_total_exibicao)}**"
        )

    with coluna_peca:
        st.info(
            "Custo direto por peça: "
            f"**{formatar_moeda(custo_direto_peca_exibicao)}**"
        )

    st.subheader("Taxas e margem")

    coluna1, coluna2, coluna3 = st.columns(3)

    with coluna1:
        margem = st.number_input(
            "Margem desejada (%)",
            min_value=0.0,
            max_value=99.0,
            value=30.0,
            step=1.0,
            help=(
                "Percentual do preço de venda que ficará "
                "como margem de lucro."
            ),
        )

    with coluna2:
        imposto = st.number_input(
            "Impostos (%)",
            min_value=0.0,
            max_value=99.0,
            value=0.0,
            step=0.1,
        )

    with coluna3:
        taxa_maquineta = st.number_input(
            "Taxa da maquineta (%)",
            min_value=0.0,
            max_value=99.0,
            value=0.0,
            step=0.1,
        )

    calcular = st.form_submit_button(
        "Calcular e salvar no histórico",
        type="primary",
        use_container_width=True,
    )


# ==========================================================
# REALIZAR E SALVAR O CÁLCULO
# ==========================================================

if calcular:
    try:
        produto = produtos_por_nome[produto_nome]
        produto_id = produto["id"]

        inicio_mes = mes_referencia.replace(day=1).isoformat()

        # Busca as despesas fixas cadastradas no mesmo mês
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

        # Custos totais informados para toda a produção
        custo_direto_total = (
            float(custo_insumos)
            + float(custo_mao_obra)
            + float(custo_embalagem)
            + float(outros_custos)
        )

        # Custo direto de uma única peça
        custo_direto_por_peca = (
            custo_direto_total
            / quantidade_produzida
        )

        # Rateio das despesas fixas por peça
        rateio_fixo_por_peca = (
            despesas_mes
            / quantidade_produzida
        )

        # Custo completo de uma peça
        custo_total_por_peca = (
            custo_direto_por_peca
            + rateio_fixo_por_peca
        )

        total_taxas = (
            float(imposto)
            + float(taxa_maquineta)
        )

        percentual_total = (
            float(margem)
            + float(imposto)
            + float(taxa_maquineta)
        ) / 100

        if percentual_total >= 1:
            st.error(
                "A soma da margem, impostos e taxas "
                "deve ser inferior a 100%."
            )
            st.stop()

        # Preserva margem e taxas dentro do preço final
        preco_venda = (
            custo_total_por_peca
            / (1 - percentual_total)
        )

        valor_impostos = (
            preco_venda
            * float(imposto)
            / 100
        )

        valor_maquineta = (
            preco_venda
            * float(taxa_maquineta)
            / 100
        )

        lucro_estimado = (
            preco_venda
            * float(margem)
            / 100
        )

        st.session_state["ultimo_resultado"] = {
            "produto": produto_nome,
            "quantidade_produzida": quantidade_produzida,
            "despesas_mes": despesas_mes,
            "custo_direto_total": custo_direto_total,
            "custo_direto_por_peca": custo_direto_por_peca,
            "rateio_fixo_por_peca": rateio_fixo_por_peca,
            "custo_total_por_peca": custo_total_por_peca,
            "preco_venda": preco_venda,
            "valor_impostos": valor_impostos,
            "valor_maquineta": valor_maquineta,
            "lucro_estimado": lucro_estimado,
        }

        supabase.rpc(
            "salvar_calculo_precificacao",
            {
                "p_empresa_id": empresa_id,
                "p_produto_id": produto_id,
                "p_mes_referencia": inicio_mes,
                "p_quantidade_produzida": quantidade_produzida,
                "p_despesas_fixas_mes": despesas_mes,
                "p_rateio_fixo_por_peca": rateio_fixo_por_peca,
                # O banco guarda os totais informados por categoria
                "p_custo_insumos": float(custo_insumos),
                "p_custo_mao_obra": float(custo_mao_obra),
                "p_custo_embalagem": float(custo_embalagem),
                "p_outros_custos": float(outros_custos),
                # Estes campos são armazenados por peça
                "p_custo_direto": custo_direto_por_peca,
                "p_custo_total_peca": custo_total_por_peca,
                "p_total_taxas_percentual": total_taxas,
                "p_margem_varejo": float(margem),
                "p_preco_varejo": preco_venda,
                "p_lucro_varejo_estimado": lucro_estimado,
            },
        ).execute()

        st.session_state["mensagem_calculo"] = (
            f"Cálculo do produto {produto_nome} "
            "salvo com sucesso."
        )

        st.rerun()

    except Exception as exc:
        st.error(f"Erro ao calcular ou salvar: {exc}")


# ==========================================================
# RESULTADO DO ÚLTIMO CÁLCULO
# ==========================================================

resultado = st.session_state.get("ultimo_resultado")

if resultado:
    st.subheader("Resultado do último cálculo")

    st.caption(
        f"Produto: {resultado['produto']} · "
        f"Quantidade: {resultado['quantidade_produzida']} peças"
    )

    coluna1, coluna2, coluna3 = st.columns(3)

    coluna1.metric(
        "Custo direto total do lote",
        formatar_moeda(
            resultado["custo_direto_total"]
        ),
    )

    coluna2.metric(
        "Custo direto por peça",
        formatar_moeda(
            resultado["custo_direto_por_peca"]
        ),
    )

    coluna3.metric(
        "Rateio fixo por peça",
        formatar_moeda(
            resultado["rateio_fixo_por_peca"]
        ),
    )

    coluna1, coluna2, coluna3 = st.columns(3)

    coluna1.metric(
        "Custo total por peça",
        formatar_moeda(
            resultado["custo_total_por_peca"]
        ),
    )

    coluna2.metric(
        "Preço sugerido",
        formatar_moeda(
            resultado["preco_venda"]
        ),
    )

    coluna3.metric(
        "Lucro estimado por unidade",
        formatar_moeda(
            resultado["lucro_estimado"]
        ),
    )

    with st.expander("Detalhamento do preço"):
        tabela_detalhamento = pd.DataFrame(
            [
                {
                    "Componente": "Custo direto por peça",
                    "Valor": resultado["custo_direto_por_peca"],
                },
                {
                    "Componente": "Rateio fixo por peça",
                    "Valor": resultado["rateio_fixo_por_peca"],
                },
                {
                    "Componente": "Impostos",
                    "Valor": resultado["valor_impostos"],
                },
                {
                    "Componente": "Taxa da maquineta",
                    "Valor": resultado["valor_maquineta"],
                },
                {
                    "Componente": "Margem de lucro",
                    "Valor": resultado["lucro_estimado"],
                },
                {
                    "Componente": "Preço final",
                    "Valor": resultado["preco_venda"],
                },
            ]
        )

        st.dataframe(
            tabela_detalhamento,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Valor": st.column_config.NumberColumn(
                    "Valor",
                    format="R$ %.2f",
                ),
            },
        )


# ==========================================================
# HISTÓRICO
# ==========================================================

st.divider()
st.subheader("Histórico de cálculos")

try:
    resposta_historico = (
        supabase.table("calculos_precificacao")
        .select(
            "id, produto_id, mes_referencia, "
            "quantidade_produzida, despesas_fixas_mes, "
            "custo_insumos, custo_mao_obra, "
            "custo_embalagem, outros_custos, "
            "custo_direto, rateio_fixo_por_peca, "
            "custo_total_peca, total_taxas_percentual, "
            "margem_varejo, preco_varejo, "
            "lucro_varejo_estimado, criado_em"
        )
        .eq("empresa_id", empresa_id)
        .order("criado_em", desc=True)
        .limit(100)
        .execute()
    )

    historico = resposta_historico.data or []

    nomes_produtos = {
        produto["id"]: produto["nome"]
        for produto in produtos
    }

    if not historico:
        st.info("Nenhum cálculo foi salvo até o momento.")

    else:
        linhas_historico = []

        for calculo in historico:
            custo_total_lote = (
                float(calculo.get("custo_insumos") or 0)
                + float(calculo.get("custo_mao_obra") or 0)
                + float(calculo.get("custo_embalagem") or 0)
                + float(calculo.get("outros_custos") or 0)
            )

            linhas_historico.append(
                {
                    "Produto": nomes_produtos.get(
                        calculo["produto_id"],
                        "Produto não encontrado",
                    ),
                    "Mês": calculo["mes_referencia"],
                    "Quantidade": calculo["quantidade_produzida"],
                    "Custos do lote": custo_total_lote,
                    "Custo direto/peça": float(
                        calculo["custo_direto"]
                    ),
                    "Rateio fixo/peça": float(
                        calculo["rateio_fixo_por_peca"]
                    ),
                    "Custo total/peça": float(
                        calculo["custo_total_peca"]
                    ),
                    "Taxas (%)": float(
                        calculo["total_taxas_percentual"]
                    ),
                    "Margem (%)": float(
                        calculo["margem_varejo"]
                    ),
                    "Preço de venda": float(
                        calculo["preco_varejo"]
                    ),
                    "Lucro estimado": float(
                        calculo["lucro_varejo_estimado"]
                    ),
                    "Data do cálculo": calculo["criado_em"],
                }
            )

        tabela_historico = pd.DataFrame(
            linhas_historico
        )

        st.dataframe(
            tabela_historico,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Custos do lote": st.column_config.NumberColumn(
                    "Custos do lote",
                    format="R$ %.2f",
                ),
                "Custo direto/peça": st.column_config.NumberColumn(
                    "Custo direto/peça",
                    format="R$ %.2f",
                ),
                "Rateio fixo/peça": st.column_config.NumberColumn(
                    "Rateio fixo/peça",
                    format="R$ %.2f",
                ),
                "Custo total/peça": st.column_config.NumberColumn(
                    "Custo total/peça",
                    format="R$ %.2f",
                ),
                "Preço de venda": st.column_config.NumberColumn(
                    "Preço de venda",
                    format="R$ %.2f",
                ),
                "Lucro estimado": st.column_config.NumberColumn(
                    "Lucro estimado",
                    format="R$ %.2f",
                ),
                "Taxas (%)": st.column_config.NumberColumn(
                    "Taxas (%)",
                    format="%.2f%%",
                ),
                "Margem (%)": st.column_config.NumberColumn(
                    "Margem (%)",
                    format="%.2f%%",
                ),
            },
        )

except Exception as exc:
    st.error(f"Erro ao carregar o histórico: {exc}")