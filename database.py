from __future__ import annotations

import streamlit as st
from supabase import Client, create_client


def get_supabase_client() -> Client:
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
    except KeyError as exc:
        raise RuntimeError(
            "As credenciais do Supabase não foram configuradas."
        ) from exc

    return create_client(
        supabase_url,
        supabase_key,
    )