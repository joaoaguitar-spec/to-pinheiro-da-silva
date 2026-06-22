"""
Arquivo Tó Pinheiro da Silva — CRIATURA
Ponto de partida (v0) para o site privado. O Claude Code parte daqui e completa.

Estrutura esperada:
  streamlit_app.py
  requirements.txt
  content/                      <- colocar aqui os ficheiros do source pack
    to_pinheiro_biografia_e_obra.md
    album_credits_aurora_bem_bonda.md
    to_pinheiro_da_silva_criatura_evidence.jsonl
    to_pinheiro_da_silva_criatura_knowledge_base.md
    to_pinheiro_manual_memories.md

Correr localmente:  pip install -r requirements.txt  &&  streamlit run streamlit_app.py
Palavra-passe: definir em .streamlit/secrets.toml ->  app_password = "Batman"
(enquanto não existir, usa "Batman " — mudar antes de qualquer deploy)
"""

from pathlib import Path
import json

import streamlit as st
import streamlit.components.v1 as components

try:
    import pandas as pd
except Exception:
    pd = None

st.set_page_config(page_title="Arquivo Tó Pinheiro da Silva", layout="wide")

CONTENT = Path(__file__).parent / "content"


# ---------- palavra-passe (espaço privado) ----------
def check_password() -> bool:
    if st.session_state.get("auth_ok"):
        return True
    st.title("Arquivo Tó Pinheiro da Silva")
    st.caption("Espaço privado da banda")
    with st.form("login"):
        pw = st.text_input("Palavra-passe", type="password")
        submitted = st.form_submit_button("Entrar")
    if submitted:
        try:
            expected = st.secrets["app_password"]
        except Exception:
            expected = "criatura"
        if pw == expected:
            st.session_state.auth_ok = True
            st.rerun()
        else:
            st.error("Palavra-passe incorreta.")
    return False


if not check_password():
    st.stop()


# ---------- helpers ----------
def read_md(name: str) -> str:
    p = CONTENT / name
    if p.exists():
        return p.read_text(encoding="utf-8")
    return f"_(falta o ficheiro `content/{name}`)_"


def load_jsonl(name: str) -> list:
    p = CONTENT / name
    out = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


EVIDENCE_FILE = "to_pinheiro_da_silva_criatura_evidence.jsonl"


# ---------- navegação ----------
st.sidebar.title("Arquivo Tó")
st.sidebar.caption("Engenheiro de som · CRIATURA")
page = st.sidebar.radio(
    "Navegar",
    ["Início", "Ouvir", "Álbuns", "Cronologia", "Evidência", "Memórias", "Validação"],
)


# ---------- páginas ----------
if page == "Início":
    st.title("Tó Pinheiro da Silva")
    st.caption("Um arquivo vivo — quem é o Tó e o que fez com a CRIATURA")
    st.markdown(read_md("to_pinheiro_biografia_e_obra.md"))

elif page == "Ouvir":
    st.title("Ouvir")
    st.write("Os dois álbuns que o Tó **misturou e masterizou**.")
    st.subheader("Aurora (2016)")
    components.iframe(
        "https://bandcamp.com/EmbeddedPlayer/album=1417799381/size=large/"
        "bgcol=ffffff/linkcol=0687f5/tracklist=true/transparent=true/",
        height=472,
    )
    st.subheader("Bem Bonda (2021)")
    components.iframe(
        "https://bandcamp.com/EmbeddedPlayer/album=4156733895/size=large/"
        "bgcol=ffffff/linkcol=0687f5/tracklist=true/transparent=true/",
        height=472,
    )

elif page == "Álbuns":
    st.title("Álbuns")
    st.markdown(read_md("album_credits_aurora_bem_bonda.md"))

elif page == "Cronologia":
    st.title("Cronologia")
    st.write("Marcos confirmados do percurso do Tó com a CRIATURA.")
    milestones = [
        ("2014–2015", "Gravação de *Aurora* (Musibéria · Kimahera · Quarto ao Lado)."),
        ("5 fev 2016", "Lançamento de *Aurora* — mistura e masterização: Tó."),
        ("mar 2019 – out 2020", "Gravação de *Bem Bonda* (Namouche · Haus · Camaleão)."),
        ("30 out – 5 nov 2020", "Sessões de mistura com o Tó."),
        ("10 dez 2020", "Ficha técnica de *Bem Bonda* partilhada no grupo."),
        ("5 fev 2021", "Lançamento de *Bem Bonda* — mistura e masterização: Tó."),
    ]
    for when, what in milestones:
        st.markdown(f"**{when}** — {what}")
    st.info("A enriquecer com datas da base de evidência.")

elif page == "Evidência":
    st.title("Evidência (WhatsApp)")
    records = load_jsonl(EVIDENCE_FILE)
    if not records:
        st.warning(f"falta `content/{EVIDENCE_FILE}`")
    elif pd is None:
        st.error("instalar pandas (ver requirements.txt)")
    else:
        df = pd.DataFrame(records)
        q = st.text_input("Procurar na mensagem")
        c1, c2, c3 = st.columns(3)
        sec = c1.selectbox("Secção", ["(todas)"] + sorted(df["primary_section"].dropna().unique()))
        stt = c2.selectbox("Estado", ["(todos)"] + sorted(df["evidence_status"].dropna().unique()))
        snd = c3.selectbox("Autor", ["(todos)"] + sorted(df["sender"].dropna().unique()))

        f = df
        if q:
            f = f[f["original_message"].str.contains(q, case=False, na=False)]
        if sec != "(todas)":
            f = f[f["primary_section"] == sec]
        if stt != "(todos)":
            f = f[f["evidence_status"] == stt]
        if snd != "(todos)":
            f = f[f["sender"] == snd]

        st.caption(f"{len(f)} de {len(df)} registos")
        st.dataframe(
            f[["date", "time", "sender", "evidence_status", "primary_section", "original_message"]],
            width="stretch",
            hide_index=True,
        )

elif page == "Memórias":
    st.title("Memórias")
    st.write("Histórias e fotos da banda. (O formulário para adicionar entra na versão completa.)")
    st.markdown(read_md("to_pinheiro_manual_memories.md"))

elif page == "Validação":
    st.title("Validação — privado")
    st.write("Os registos por confirmar. Marcar e, na versão completa, guardar a decisão.")
    records = load_jsonl(EVIDENCE_FILE)
    vq = [r for r in records if r.get("evidence_status") in ("To Confirm", "Probable / To Confirm")]
    st.caption(f"{len(vq)} registos por validar")
    for r in vq:
        with st.expander(f"{r.get('evidence_id','?')} — {r.get('date','')} — {r.get('sender','')}"):
            st.code(r.get("original_message", ""))
            if r.get("analytical_note"):
                st.caption(r["analytical_note"])
            st.radio(
                "Decisão",
                ["(por decidir)", "Confirmado", "Não é o Tó", "Precisa de contexto"],
                key=f"dec_{r.get('evidence_id')}",
                horizontal=True,
            )
    st.info("As decisões serão persistidas na versão completa (Claude Code).")
