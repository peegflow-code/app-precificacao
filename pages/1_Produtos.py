from __future__ import annotations

import pandas as pd
import streamlit as st

from auth import restaurar_cliente_autenticado


st.set_page_config(
    page_title="Produtos",
    page_icon="📦",
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

st.title("📦 Produtos")
st.caption(f"Empresa: {empresa_nome}")

if st.session_state.get("mensagem_produto"):
    st.success(st.session_state.pop("mensagem_produto"))

with st.expander("Cadastrar novo produto", expanded=True):
    with st.form("form_produto", clear_on_submit=True):
        coluna1, coluna2 = st.columns(2)

        with coluna1:
            nome = st.text_input("Nome do produto *")
            codigo = st.text_input("Código")

        with coluna2:
            categoria = st.text_input("Categoria")

            unidade = st.selectbox(
                "Unidade de medida",
                [
                    "unidade",
                    "kg",
                    "g",
                    "litro",
                    "ml",
                    "metro",
                    "cm",
                ],
            )

        salvar = st.form_submit_button(
            "Salvar produto",
            type="primary",
            use_container_width=True,
        )

    if salvar:
        if not nome.strip():
            st.error("Informe o nome do produto.")
        else:
            try:
                resposta_rpc = supabase.rpc(
                    "cadastrar_produto",
                    {
                        "p_empresa_id": empresa_id,
                        "p_nome": nome.strip(),
                        "p_codigo": codigo.strip() or None,
                        "p_categoria": categoria.strip() or None,
                        "p_unidade_medida": unidade,
                    },
                ).execute()

                st.session_state["mensagem_produto"] = (
                    f"Produto {nome.strip()} cadastrado com sucesso."
                )

                st.rerun()

            except Exception as exc:
                mensagem = str(exc).lower()

                if "produto_codigo_unico" in mensagem:
                    st.error("Já existe um produto com esse código.")
                elif "sem permissão" in mensagem:
                    st.error(
                        "Seu usuário não possui permissão "
                        "para cadastrar produtos."
                    )
                else:
                    st.error(f"Erro ao cadastrar produto: {exc}")

st.subheader("Produtos cadastrados")

try:
    resposta = (
        supabase.table("produtos")
        .select(
            "id, codigo, nome, categoria, "
            "unidade_medida, ativo, criado_em"
        )
        .eq("empresa_id", empresa_id)
        .order("nome")
        .execute()
    )

    produtos = resposta.data or []

    if not produtos:
        st.info("Nenhum produto cadastrado.")
    else:
        st.metric("Quantidade de produtos", len(produtos))

        linhas = []

        for produto in produtos:
            linhas.append(
                {
                    "Código": produto.get("codigo") or "—",
                    "Produto": produto.get("nome"),
                    "Categoria": produto.get("categoria") or "—",
                    "Unidade": produto.get("unidade_medida"),
                    "Situação": (
                        "Ativo"
                        if produto.get("ativo")
                        else "Inativo"
                    ),
                }
            )

        tabela = pd.DataFrame(linhas)

        st.dataframe(
            tabela,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Código": st.column_config.TextColumn(
                    "Código",
                    width="small",
                ),
                "Produto": st.column_config.TextColumn(
                    "Produto",
                    width="large",
                ),
                "Categoria": st.column_config.TextColumn(
                    "Categoria",
                    width="medium",
                ),
                "Unidade": st.column_config.TextColumn(
                    "Unidade",
                    width="small",
                ),
                "Situação": st.column_config.TextColumn(
                    "Situação",
                    width="small",
                ),
            },
        )

except Exception as exc:
    st.error(f"Erro ao carregar produtos: {exc}")