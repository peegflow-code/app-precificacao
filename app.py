from __future__ import annotations

import streamlit as st

from auth import (
    cadastrar_usuario,
    carregar_empresas_usuario,
    criar_empresa,
    fazer_login,
    fazer_logout,
    inicializar_sessao,
)


st.set_page_config(
    page_title="Precifica Fácil",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inicializar_sessao()


# ==========================================================
# LOGIN E CADASTRO
# ==========================================================

def tela_login() -> None:
    st.title("💰 Precifica Fácil")

    st.caption(
        "Calcule preços de venda com base nos custos, "
        "despesas, impostos, taxas e margem."
    )

    _, centro, _ = st.columns([1, 1.2, 1])

    with centro:
        aba_login, aba_cadastro = st.tabs(
            ["Entrar", "Criar conta"]
        )

        with aba_login:
            with st.form("form_login"):
                email = st.text_input("E-mail")

                senha = st.text_input(
                    "Senha",
                    type="password",
                )

                entrar = st.form_submit_button(
                    "Entrar",
                    type="primary",
                    use_container_width=True,
                )

            if entrar:
                sucesso, mensagem = fazer_login(
                    email,
                    senha,
                )

                if sucesso:
                    st.success(mensagem)
                    st.rerun()
                else:
                    st.error(mensagem)

        with aba_cadastro:
            with st.form("form_cadastro"):
                nome = st.text_input("Nome completo")

                email_cadastro = st.text_input(
                    "E-mail",
                    key="email_cadastro",
                )

                senha_cadastro = st.text_input(
                    "Senha",
                    type="password",
                    key="senha_cadastro",
                )

                confirmar_senha = st.text_input(
                    "Confirmar senha",
                    type="password",
                )

                cadastrar = st.form_submit_button(
                    "Criar conta",
                    type="primary",
                    use_container_width=True,
                )

            if cadastrar:
                sucesso, mensagem = cadastrar_usuario(
                    nome,
                    email_cadastro,
                    senha_cadastro,
                    confirmar_senha,
                )

                if sucesso:
                    st.success(mensagem)

                    if st.session_state.get("autenticado"):
                        st.rerun()
                else:
                    st.error(mensagem)


# ==========================================================
# PRIMEIRA EMPRESA
# ==========================================================

def tela_primeira_empresa() -> None:
    st.title("Cadastre sua empresa")

    st.info(
        "Sua conta ainda não está vinculada a uma empresa."
    )

    with st.form("form_primeira_empresa"):
        nome_fantasia = st.text_input(
            "Nome fantasia *"
        )

        razao_social = st.text_input(
            "Razão social"
        )

        cnpj = st.text_input("CNPJ")

        coluna1, coluna2 = st.columns(2)

        with coluna1:
            email = st.text_input(
                "E-mail da empresa"
            )

        with coluna2:
            telefone = st.text_input(
                "Telefone"
            )

        salvar = st.form_submit_button(
            "Criar empresa",
            type="primary",
            use_container_width=True,
        )

    if salvar:
        sucesso, mensagem = criar_empresa(
            nome_fantasia,
            razao_social,
            cnpj,
            email,
            telefone,
        )

        if sucesso:
            st.success(mensagem)
            st.rerun()
        else:
            st.error(mensagem)


# ==========================================================
# NAVEGAÇÃO
# ==========================================================

if not st.session_state.get("autenticado"):
    pagina = st.navigation(
        [
            st.Page(
                tela_login,
                title="Entrar",
                icon="🔐",
            )
        ],
        position="hidden",
    )

    pagina.run()
    st.stop()


empresas = st.session_state.get("empresas_usuario", [])

if not empresas:
    empresas = carregar_empresas_usuario()

if not empresas:
    pagina = st.navigation(
        [
            st.Page(
                tela_primeira_empresa,
                title="Cadastrar empresa",
                icon="🏢",
            )
        ],
        position="hidden",
    )

    pagina.run()
    st.stop()


# ==========================================================
# EMPRESA ATIVA
# ==========================================================

empresa_ativa_id = st.session_state.get(
    "empresa_ativa_id"
)

ids_empresas = {
    empresa["id"]
    for empresa in empresas
}

if empresa_ativa_id not in ids_empresas:
    st.session_state.empresa_ativa_id = empresas[0]["id"]
    st.session_state.empresa_ativa_nome = empresas[0][
        "nome_fantasia"
    ]


# ==========================================================
# MENU DO SISTEMA
# ==========================================================

pagina = st.navigation(
    {
        "Sistema": [
            st.Page(
                "pages/0_Dashboard.py",
                title="Visão geral",
                icon="🏠",
                default=True,
            ),
            st.Page(
                "pages/1_Produtos.py",
                title="Produtos",
                icon="📦",
            ),
            st.Page(
                "pages/2_Despesas.py",
                title="Despesas",
                icon="🧾",
            ),
            st.Page(
                "pages/3_Calculadora.py",
                title="Calculadora",
                icon="🧮",
            ),
        ]
    }
)


# ==========================================================
# INFORMAÇÕES COMUNS DA BARRA LATERAL
# ==========================================================

with st.sidebar:
    st.divider()

    st.subheader("Precifica Fácil")

    st.write(
        "Empresa: "
        f"**{st.session_state.get('empresa_ativa_nome')}**"
    )

    usuario = st.session_state.get("usuario")
    email_usuario = getattr(usuario, "email", "")

    if email_usuario:
        st.caption(email_usuario)

    if st.button(
        "Sair",
        use_container_width=True,
    ):
        fazer_logout()
        st.rerun()


pagina.run()