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
    st.success(
        st.session_state.pop("mensagem_produto")
    )

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
                    f"Produto cadastrado com sucesso. "
                    f"ID: {resposta_rpc.data}"
                )

                st.rerun()

            except Exception as exc:
                mensagem = str(exc).lower()

                if "produto_codigo_unico" in mensagem:
                    st.error(
                        "Já existe um produto com esse código."
                    )
                elif "sem permissão" in mensagem:
                    st.error(
                        "Seu usuário não possui permissão "
                        "para cadastrar produtos."
                    )
                else:
                    st.error(
                        f"Erro ao cadastrar produto: {exc}"
                    )