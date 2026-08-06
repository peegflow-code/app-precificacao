from __future__ import annotations

import pandas as pd
import streamlit as st

from auth import restaurar_cliente_autenticado


st.set_page_config(
    page_title="Produtos",
    page_icon="📦",
    layout="wide",
)

# ==========================================================
# VALIDAR SESSÃO
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
# CABEÇALHO
# ==========================================================

st.title("📦 Produtos")
st.caption(f"Empresa: {empresa_nome}")

if st.session_state.get("mensagem_produto"):
    st.success(
        st.session_state.pop("mensagem_produto")
    )


# ==========================================================
# CADASTRAR PRODUTO
# ==========================================================

with st.expander(
    "Cadastrar novo produto",
    expanded=True,
):
    with st.form(
        "form_produto",
        clear_on_submit=True,
    ):
        coluna1, coluna2 = st.columns(2)

        with coluna1:
            nome = st.text_input(
                "Nome do produto *"
            )

            codigo = st.text_input(
                "Código"
            )

        with coluna2:
            categoria = st.text_input(
                "Categoria"
            )

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
            st.error(
                "Informe o nome do produto."
            )

        else:
            try:
                supabase.rpc(
                    "cadastrar_produto",
                    {
                        "p_empresa_id": empresa_id,
                        "p_nome": nome.strip(),
                        "p_codigo": (
                            codigo.strip() or None
                        ),
                        "p_categoria": (
                            categoria.strip() or None
                        ),
                        "p_unidade_medida": unidade,
                    },
                ).execute()

                st.session_state[
                    "mensagem_produto"
                ] = (
                    f"Produto {nome.strip()} "
                    "cadastrado com sucesso."
                )

                st.rerun()

            except Exception as exc:
                mensagem = str(exc).lower()

                if "produto_codigo_unico" in mensagem:
                    st.error(
                        "Já existe um produto "
                        "com esse código."
                    )

                elif "sem permissão" in mensagem:
                    st.error(
                        "Seu usuário não possui "
                        "permissão para cadastrar produtos."
                    )

                else:
                    st.error(
                        f"Erro ao cadastrar produto: {exc}"
                    )


# ==========================================================
# LISTAR PRODUTOS
# ==========================================================

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
        st.info(
            "Nenhum produto cadastrado."
        )

    else:
        st.metric(
            "Quantidade de produtos",
            len(produtos),
        )

        linhas = []

        for produto in produtos:
            linhas.append(
                {
                    "Código": (
                        produto.get("codigo") or "—"
                    ),
                    "Produto": produto.get("nome"),
                    "Categoria": (
                        produto.get("categoria") or "—"
                    ),
                    "Unidade": produto.get(
                        "unidade_medida"
                    ),
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
                "Código": (
                    st.column_config.TextColumn(
                        "Código",
                        width="small",
                    )
                ),
                "Produto": (
                    st.column_config.TextColumn(
                        "Produto",
                        width="large",
                    )
                ),
                "Categoria": (
                    st.column_config.TextColumn(
                        "Categoria",
                        width="medium",
                    )
                ),
                "Unidade": (
                    st.column_config.TextColumn(
                        "Unidade",
                        width="small",
                    )
                ),
                "Situação": (
                    st.column_config.TextColumn(
                        "Situação",
                        width="small",
                    )
                ),
            },
        )

        # ==================================================
        # EXCLUIR PRODUTO
        # ==================================================

        st.divider()
        st.subheader("Excluir produto")

        st.warning(
            "Produtos que possuem cálculos no histórico "
            "só poderão ser excluídos depois que os "
            "cálculos relacionados forem removidos."
        )

        produtos_por_rotulo = {
            (
                f"{produto['nome']} — "
                f"{produto.get('codigo') or 'sem código'}"
            ): produto
            for produto in produtos
        }

        produto_selecionado_rotulo = st.selectbox(
            "Selecione o produto",
            options=list(
                produtos_por_rotulo.keys()
            ),
            key="produto_para_excluir",
        )

        produto_selecionado = (
            produtos_por_rotulo[
                produto_selecionado_rotulo
            ]
        )

        confirmar_exclusao = st.checkbox(
            (
                "Confirmo que desejo excluir o produto "
                f"{produto_selecionado['nome']}."
            ),
            key="confirmar_exclusao_produto",
        )

        excluir = st.button(
            "Excluir produto",
            type="secondary",
            use_container_width=True,
            disabled=not confirmar_exclusao,
        )

        if excluir:
            try:
                supabase.rpc(
                    "excluir_produto",
                    {
                        "p_produto_id": (
                            produto_selecionado["id"]
                        )
                    },
                ).execute()

                st.session_state[
                    "mensagem_produto"
                ] = (
                    "Produto excluído com sucesso."
                )

                st.rerun()

            except Exception as exc:
                mensagem = str(exc).lower()

                if (
                    "possui cálculos no histórico"
                    in mensagem
                ):
                    st.error(
                        "Este produto possui cálculos "
                        "salvos. Exclua primeiro os "
                        "cálculos relacionados na página "
                        "Calculadora."
                    )

                elif "sem permissão" in mensagem:
                    st.error(
                        "Seu usuário não possui permissão "
                        "para excluir produtos."
                    )

                else:
                    st.error(
                        f"Erro ao excluir produto: {exc}"
                    )

except Exception as exc:
    st.error(
        f"Erro ao carregar produtos: {exc}"
    )