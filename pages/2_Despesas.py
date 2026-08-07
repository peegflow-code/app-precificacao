from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import streamlit as st

from auth import restaurar_cliente_autenticado


# ==========================================================
# SESSÃO
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
# FUNÇÕES
# ==========================================================

def formatar_moeda(valor: float) -> str:
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def formatar_mes(data_iso: str) -> str:
    try:
        data = datetime.fromisoformat(
            data_iso.replace("Z", "+00:00")
        )

        meses = [
            "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
            "Jul", "Ago", "Set", "Out", "Nov", "Dez"
        ]

        return f"{meses[data.month - 1]}/{data.year}"

    except Exception:
        return data_iso


# ==========================================================
# CABEÇALHO
# ==========================================================

st.title("🧾 Despesas mensais")
st.caption(
    f"Empresa: {empresa_nome} · "
    "Cadastre as despesas que serão rateadas na precificação."
)

if st.session_state.get("mensagem_despesa"):
    st.success(
        st.session_state.pop("mensagem_despesa")
    )


# ==========================================================
# CADASTRO
# ==========================================================

with st.expander(
    "➕ Cadastrar nova despesa",
    expanded=False,
):
    with st.form(
        "form_nova_despesa",
        clear_on_submit=True,
    ):
        coluna1, coluna2 = st.columns(2)

        with coluna1:
            descricao = st.text_input(
                "Descrição *",
                placeholder="Ex.: Aluguel",
            )

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

            recorrente = st.checkbox(
                "Despesa recorrente"
            )

        observacoes = st.text_area(
            "Observações"
        )

        salvar = st.form_submit_button(
            "Salvar despesa",
            type="primary",
            use_container_width=True,
        )

    if salvar:
        if not descricao.strip():
            st.error(
                "Informe a descrição da despesa."
            )

        elif valor <= 0:
            st.error(
                "Informe um valor maior que zero."
            )

        else:
            try:
                (
                    supabase.table("despesas")
                    .insert(
                        {
                            "empresa_id": empresa_id,
                            "descricao": descricao.strip(),
                            "mes_referencia": (
                                mes.replace(day=1).isoformat()
                            ),
                            "valor": float(valor),
                            "recorrente": recorrente,
                            "observacoes": (
                                observacoes.strip() or None
                            ),
                        }
                    )
                    .execute()
                )

                st.session_state[
                    "mensagem_despesa"
                ] = "Despesa cadastrada com sucesso."

                st.rerun()

            except Exception as exc:
                st.error(
                    f"Erro ao cadastrar despesa: {exc}"
                )


# ==========================================================
# CARREGAR DESPESAS
# ==========================================================

try:
    resposta = (
        supabase.table("despesas")
        .select(
            "id, descricao, mes_referencia, "
            "valor, recorrente, observacoes"
        )
        .eq("empresa_id", empresa_id)
        .order("mes_referencia", desc=True)
        .execute()
    )

    despesas = resposta.data or []

except Exception as exc:
    st.error(
        f"Erro ao carregar despesas: {exc}"
    )
    st.stop()


# ==========================================================
# FILTRO
# ==========================================================

st.subheader("Despesas cadastradas")

if not despesas:
    st.info("Nenhuma despesa cadastrada.")
    st.stop()

meses_disponiveis = sorted(
    list(
        {
            item["mes_referencia"]
            for item in despesas
        }
    ),
    reverse=True,
)

mes_atual = date.today().replace(day=1).isoformat()

indice_padrao = (
    meses_disponiveis.index(mes_atual)
    if mes_atual in meses_disponiveis
    else 0
)

mes_filtro = st.selectbox(
    "Mês",
    options=meses_disponiveis,
    index=indice_padrao,
    format_func=formatar_mes,
)

despesas_filtradas = [
    item
    for item in despesas
    if item["mes_referencia"] == mes_filtro
]

total_mes = sum(
    float(item["valor"])
    for item in despesas_filtradas
)

coluna1, coluna2, coluna3 = st.columns(3)

coluna1.metric(
    "Total do mês",
    formatar_moeda(total_mes),
)

coluna2.metric(
    "Quantidade de despesas",
    len(despesas_filtradas),
)

recorrentes = sum(
    1
    for item in despesas_filtradas
    if item.get("recorrente")
)

coluna3.metric(
    "Despesas recorrentes",
    recorrentes,
)


# ==========================================================
# TABELA
# ==========================================================

linhas = []

for item in despesas_filtradas:
    linhas.append(
        {
            "Descrição": item["descricao"],
            "Valor": float(item["valor"]),
            "Recorrente": (
                "Sim"
                if item.get("recorrente")
                else "Não"
            ),
            "Observações": (
                item.get("observacoes") or "—"
            ),
        }
    )

tabela = pd.DataFrame(linhas)

st.dataframe(
    tabela,
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
# EDITAR DESPESA
# ==========================================================

st.divider()

with st.expander("✏️ Editar despesa"):
    despesas_por_rotulo = {
        (
            f"{item['descricao']} — "
            f"{formatar_moeda(float(item['valor']))}"
        ): item
        for item in despesas_filtradas
    }

    rotulo_edicao = st.selectbox(
        "Selecione a despesa",
        options=list(
            despesas_por_rotulo.keys()
        ),
        key="despesa_edicao",
    )

    despesa_edicao = despesas_por_rotulo[
        rotulo_edicao
    ]

    with st.form("form_editar_despesa"):
        descricao_editada = st.text_input(
            "Descrição",
            value=despesa_edicao["descricao"],
        )

        coluna1, coluna2 = st.columns(2)

        with coluna1:
            valor_editado = st.number_input(
                "Valor",
                min_value=0.0,
                value=float(
                    despesa_edicao["valor"]
                ),
                step=10.0,
                format="%.2f",
            )

        with coluna2:
            data_despesa = datetime.fromisoformat(
                despesa_edicao[
                    "mes_referencia"
                ]
            ).date()

            mes_editado = st.date_input(
                "Mês",
                value=data_despesa,
            )

        recorrente_editado = st.checkbox(
            "Despesa recorrente",
            value=bool(
                despesa_edicao.get(
                    "recorrente"
                )
            ),
        )

        observacoes_editadas = st.text_area(
            "Observações",
            value=(
                despesa_edicao.get(
                    "observacoes"
                )
                or ""
            ),
        )

        atualizar = st.form_submit_button(
            "Salvar alterações",
            type="primary",
            use_container_width=True,
        )

    if atualizar:
        try:
            supabase.rpc(
                "atualizar_despesa",
                {
                    "p_despesa_id": (
                        despesa_edicao["id"]
                    ),
                    "p_descricao": (
                        descricao_editada.strip()
                    ),
                    "p_mes_referencia": (
                        mes_editado
                        .replace(day=1)
                        .isoformat()
                    ),
                    "p_valor": float(
                        valor_editado
                    ),
                    "p_recorrente": (
                        recorrente_editado
                    ),
                    "p_observacoes": (
                        observacoes_editadas.strip()
                        or None
                    ),
                },
            ).execute()

            st.session_state[
                "mensagem_despesa"
            ] = "Despesa atualizada com sucesso."

            st.rerun()

        except Exception as exc:
            st.error(
                f"Erro ao atualizar despesa: {exc}"
            )


# ==========================================================
# EXCLUIR DESPESA
# ==========================================================

with st.expander("🗑️ Excluir despesa"):
    rotulo_exclusao = st.selectbox(
        "Despesa a excluir",
        options=list(
            despesas_por_rotulo.keys()
        ),
        key="despesa_exclusao",
    )

    despesa_exclusao = despesas_por_rotulo[
        rotulo_exclusao
    ]

    st.warning(
        "A exclusão não altera cálculos de "
        "precificação já salvos no histórico."
    )

    confirmar = st.checkbox(
        (
            "Confirmo a exclusão de "
            f"{despesa_exclusao['descricao']}."
        ),
        key="confirmar_exclusao_despesa",
    )

    excluir = st.button(
        "Excluir despesa",
        disabled=not confirmar,
        use_container_width=True,
    )

    if excluir:
        try:
            supabase.rpc(
                "excluir_despesa",
                {
                    "p_despesa_id": (
                        despesa_exclusao["id"]
                    )
                },
            ).execute()

            st.session_state[
                "mensagem_despesa"
            ] = "Despesa excluída com sucesso."

            st.rerun()

        except Exception as exc:
            st.error(
                f"Erro ao excluir despesa: {exc}"
            )