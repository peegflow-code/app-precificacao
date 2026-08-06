from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from auth import restaurar_cliente_autenticado


st.set_page_config(
    page_title="Despesas",
    page_icon="🧾",
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

st.title("🧾 Despesas mensais")
st.caption(f"Empresa: {empresa_nome}")

with st.expander("Cadastrar nova despesa", expanded=True):
    with st.form("form_despesa", clear_on_submit=True):
        coluna1, coluna2 = st.columns(2)

        with coluna1:
            descricao = st.text_input("Descrição *")

            valor = st.number_input(
                "Valor",
                min_value=0.0,
                step=10.0,
                format="%.2f",
            )

        with coluna2:
            mes = st.date_input(
                "Mês de referência",
                value=date.today().replace(day=1),
            )

            recorrente = st.checkbox("Despesa recorrente")

        observacoes = st.text_area("Observações")

        salvar = st.form_submit_button(
            "Salvar despesa",
            type="primary",
            use_container_width=True,
        )

    if salvar:
        if not descricao.strip():
            st.error("Informe a descrição da despesa.")
        elif valor <= 0:
            st.error("O valor precisa ser maior que zero.")
        else:
            try:
                (
                    supabase.table("despesas")
                    .insert(
                        {
                            "empresa_id": empresa_id,
                            "descricao": descricao.strip(),
                            "mes_referencia": mes.replace(day=1).isoformat(),
                            "valor": float(valor),
                            "recorrente": recorrente,
                            "observacoes": observacoes.strip() or None,
                        }
                    )
                    .execute()
                )

                st.success("Despesa cadastrada com sucesso.")
                st.rerun()

            except Exception as exc:
                st.error(f"Erro ao cadastrar despesa: {exc}")

st.subheader("Despesas cadastradas")

try:
    resposta = (
        supabase.table("despesas")
        .select(
            "id, descricao, mes_referencia, valor, "
            "recorrente, observacoes"
        )
        .eq("empresa_id", empresa_id)
        .order("mes_referencia", desc=True)
        .execute()
    )

    despesas = resposta.data or []

    total = sum(float(item["valor"]) for item in despesas)

    st.metric(
        "Total das despesas cadastradas",
        f"R$ {total:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", "."),
    )

    if not despesas:
        st.info("Nenhuma despesa cadastrada.")
    else:
        tabela = pd.DataFrame(despesas)

        tabela = tabela.rename(
            columns={
                "descricao": "Descrição",
                "mes_referencia": "Mês",
                "valor": "Valor",
                "recorrente": "Recorrente",
                "observacoes": "Observações",
            }
        )

        st.dataframe(
            tabela[
                [
                    "Descrição",
                    "Mês",
                    "Valor",
                    "Recorrente",
                    "Observações",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

except Exception as exc:
    st.error(f"Erro ao carregar despesas: {exc}")