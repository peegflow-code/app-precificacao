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
)

inicializar_sessao()


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
            with st.form("login"):
                email = st.text_input("E-mail")
                senha = st.text_input("Senha", type="password")

                entrar = st.form_submit_button(
                    "Entrar",
                    type="primary",
                    use_container_width=True,
                )

            if entrar:
                sucesso, mensagem = fazer_login(email, senha)

                if sucesso:
                    st.success(mensagem)
                    st.rerun()
                else:
                    st.error(mensagem)

        with aba_cadastro:
            with st.form("cadastro"):
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


def tela_empresa() -> None:
    st.title("Cadastre sua empresa")

    with st.form("empresa"):
        nome_fantasia = st.text_input("Nome fantasia *")
        razao_social = st.text_input("Razão social")
        cnpj = st.text_input("CNPJ")
        email = st.text_input("E-mail da empresa")
        telefone = st.text_input("Telefone")

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


def area_principal() -> None:
    empresas = st.session_state.get("empresas_usuario", [])

    if not empresas:
        empresas = carregar_empresas_usuario()

    if not empresas:
        tela_empresa()
        return

    with st.sidebar:
        st.header("Precifica Fácil")

        empresa = empresas[0]

        st.write(
            f"Empresa: **{empresa['nome_fantasia']}**"
        )

        if st.button("Sair", use_container_width=True):
            fazer_logout()
            st.rerun()

    st.title("Visão geral")

    st.success(
        f"Empresa ativa: {empresa['nome_fantasia']}"
    )

    coluna1, coluna2, coluna3 = st.columns(3)

    coluna1.metric("Produtos", 0)
    coluna2.metric("Despesas do mês", "R$ 0,00")
    coluna3.metric("Cálculos realizados", 0)


if st.session_state.get("autenticado"):
    area_principal()
else:
    tela_login()