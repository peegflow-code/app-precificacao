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
                (
                    supabase.table("produtos")
                    .insert(
                        {
                            "empresa_id": empresa_id,
                            "nome": nome.strip(),
                            "codigo": codigo.strip() or None,
                            "categoria": categoria.strip() or None,
                            "unidade_medida": unidade,
                            "ativo": True,
                        }
                    )
                    .execute()
                )

                st.success("Produto cadastrado com sucesso.")
                st.rerun()

            except Exception as exc:
                if "produto_codigo_unico" in str(exc).lower():
                    st.error("Já existe um produto com esse código.")
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
        tabela = pd.DataFrame(produtos)

        tabela = tabela.rename(
            columns={
                "codigo": "Código",
                "nome": "Produto",
                "categoria": "Categoria",
                "unidade_medida": "Unidade",
                "ativo": "Ativo",
                "criado_em": "Criado em",
            }
        )

        st.dataframe(
            tabela[
                [
                    "Código",
                    "Produto",
                    "Categoria",
                    "Unidade",
                    "Ativo",
                    "Criado em",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

except Exception as exc:
    st.error(f"Erro ao carregar produtos: {exc}")