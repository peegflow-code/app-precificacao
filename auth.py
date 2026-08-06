from __future__ import annotations

from typing import Any

import streamlit as st

from database import get_supabase_client


def inicializar_sessao() -> None:
    valores_padrao: dict[str, Any] = {
        "autenticado": False,
        "usuario": None,
        "access_token": None,
        "refresh_token": None,
        "empresa_ativa_id": None,
        "empresa_ativa_nome": None,
        "empresas_usuario": [],
    }

    for chave, valor in valores_padrao.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


def restaurar_cliente_autenticado():
    supabase = get_supabase_client()

    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")

    if access_token and refresh_token:
        supabase.auth.set_session(
            access_token,
            refresh_token,
        )

    return supabase


def fazer_login(email: str, senha: str) -> tuple[bool, str]:
    email = email.strip().lower()

    if not email:
        return False, "Informe o e-mail."

    if not senha:
        return False, "Informe a senha."

    try:
        supabase = get_supabase_client()

        resposta = supabase.auth.sign_in_with_password(
            {
                "email": email,
                "password": senha,
            }
        )

        if resposta.user is None or resposta.session is None:
            return False, "Não foi possível realizar o login."

        st.session_state.autenticado = True
        st.session_state.usuario = resposta.user
        st.session_state.access_token = resposta.session.access_token
        st.session_state.refresh_token = resposta.session.refresh_token

        carregar_empresas_usuario()

        return True, "Login realizado com sucesso."

    except Exception as exc:
        mensagem = str(exc).lower()

        if "invalid login credentials" in mensagem:
            return False, "E-mail ou senha incorretos."

        if "email not confirmed" in mensagem:
            return False, "Confirme seu e-mail antes de entrar."

        return False, f"Erro ao entrar: {exc}"


def cadastrar_usuario(
    nome: str,
    email: str,
    senha: str,
    confirmar_senha: str,
) -> tuple[bool, str]:
    nome = nome.strip()
    email = email.strip().lower()

    if len(nome) < 2:
        return False, "Informe seu nome."

    if not email:
        return False, "Informe o e-mail."

    if len(senha) < 8:
        return False, "A senha deve possuir pelo menos 8 caracteres."

    if senha != confirmar_senha:
        return False, "As senhas não coincidem."

    try:
        supabase = get_supabase_client()

        resposta = supabase.auth.sign_up(
            {
                "email": email,
                "password": senha,
                "options": {
                    "data": {
                        "nome": nome,
                    }
                },
            }
        )

        if resposta.user is None:
            return False, "Não foi possível criar o usuário."

        if resposta.session is not None:
            st.session_state.autenticado = True
            st.session_state.usuario = resposta.user
            st.session_state.access_token = resposta.session.access_token
            st.session_state.refresh_token = resposta.session.refresh_token

            return True, "Cadastro realizado com sucesso."

        return (
            True,
            "Cadastro realizado. Verifique seu e-mail para confirmar a conta.",
        )

    except Exception as exc:
        mensagem = str(exc).lower()

        if "already registered" in mensagem:
            return False, "Esse e-mail já está cadastrado."

        return False, f"Erro ao criar a conta: {exc}"


def carregar_empresas_usuario() -> list[dict]:
    if not st.session_state.get("autenticado"):
        return []

    try:
        supabase = restaurar_cliente_autenticado()

        resposta = (
            supabase.table("membros_empresa")
            .select(
                "empresa_id, perfil_acesso, ativo, "
                "empresas(id, nome_fantasia, razao_social, ativo)"
            )
            .eq("ativo", True)
            .execute()
        )

        empresas: list[dict] = []

        for vinculo in resposta.data or []:
            empresa = vinculo.get("empresas")

            if not empresa:
                continue

            if not empresa.get("ativo", True):
                continue

            empresas.append(
                {
                    "id": empresa["id"],
                    "nome_fantasia": empresa["nome_fantasia"],
                    "razao_social": empresa.get("razao_social"),
                    "perfil_acesso": vinculo["perfil_acesso"],
                }
            )

        st.session_state.empresas_usuario = empresas

        if empresas and not st.session_state.get("empresa_ativa_id"):
            st.session_state.empresa_ativa_id = empresas[0]["id"]
            st.session_state.empresa_ativa_nome = empresas[0][
                "nome_fantasia"
            ]

        return empresas

    except Exception as exc:
        st.error(f"Erro ao carregar empresas: {exc}")
        return []


def criar_empresa(
    nome_fantasia: str,
    razao_social: str,
    cnpj: str,
    email: str,
    telefone: str,
) -> tuple[bool, str]:
    if not nome_fantasia.strip():
        return False, "Informe o nome fantasia."

    try:
        supabase = restaurar_cliente_autenticado()

        resposta = supabase.rpc(
            "criar_empresa",
            {
                "p_nome_fantasia": nome_fantasia.strip(),
                "p_razao_social": razao_social.strip() or None,
                "p_cnpj": cnpj.strip() or None,
                "p_email": email.strip() or None,
                "p_telefone": telefone.strip() or None,
            },
        ).execute()

        empresa_id = resposta.data

        carregar_empresas_usuario()

        st.session_state.empresa_ativa_id = empresa_id
        st.session_state.empresa_ativa_nome = nome_fantasia.strip()

        return True, "Empresa criada com sucesso."

    except Exception as exc:
        return False, f"Erro ao criar empresa: {exc}"


def fazer_logout() -> None:
    try:
        supabase = restaurar_cliente_autenticado()
        supabase.auth.sign_out()
    except Exception:
        pass

    for chave in list(st.session_state.keys()):
        del st.session_state[chave]

    inicializar_sessao()