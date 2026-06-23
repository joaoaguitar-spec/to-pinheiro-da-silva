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
(enquanto não existir, usa "Batman" — mudar antes de qualquer deploy)
"""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

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
            expected = "Batman"
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


# ---------- navegação ----------
st.sidebar.title("Arquivo Tó")
st.sidebar.caption("Engenheiro de som · CRIATURA")
page = st.sidebar.radio(
    "Navegar",
    ["Início", "Ouvir", "Álbuns", "Cronologia", "Memórias"],
)


# ---------- páginas ----------
if page == "Início":
    st.title("Tó Pinheiro da Silva")
    st.caption("Engenheiro de som · CRIATURA")
    st.markdown(
        "O Tó — **António Pinheiro da Silva** — é o engenheiro de som que "
        "**misturou e masterizou** os dois álbuns da CRIATURA: *Aurora* (2016) "
        "e *Bem Bonda* (2021). É uma das figuras mais importantes da produção "
        "discográfica portuguesa, com mais de 150 discos gravados ao longo de "
        "décadas. Este arquivo é um **tributo em vida** — a memória do que a "
        "banda viveu e aprendeu com ele."
    )
    st.info(
        "📺 **Arquivo RTP — 1989**\n\n"
        "Em Junho de 1989, Tó Pinheiro da Silva apareceu no programa "
        "*Haja Música — Parte II* (RTP 2), ao lado de Pedro Ayres Magalhães, "
        "falando sobre António Variações. É um dos únicos registos audiovisuais "
        "conhecidos de Tó em câmara.\n\n"
        "👉 [Ver no Arquivo RTP](https://arquivos.rtp.pt/conteudos/haja-musica-parte-ii-2/)\n"
        "*(O vídeo abre em nova aba — não pode ser incorporado por direitos de autor RTP.)*"
    )
    st.divider()
    st.markdown(read_md("to_pinheiro_biografia_e_obra.md"))

elif page == "Ouvir":
    st.title("Ouvir")
    st.caption("Os dois álbuns que o Tó misturou e masterizou")
    st.markdown(
        "Aqui ficam os **dois álbuns da CRIATURA** em que o Tó assinou a "
        "**mistura e a masterização**: *Aurora* (2016) e *Bem Bonda* (2021). "
        "São o testemunho sonoro do trabalho que a banda fez com ele — podem "
        "ouvi-los na íntegra a partir do Bandcamp, aqui mesmo."
    )
    st.divider()
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
    st.markdown(
        "Esta página reúne os **créditos oficiais** dos dois álbuns de estúdio "
        "da CRIATURA — *Aurora* (2016) e *Bem Bonda* (2021). Em ambos, o Tó foi "
        "o responsável pela **mistura e masterização**, ou seja, pelo som final "
        "do disco. Abaixo ficam as fichas completas, com fontes e estado de "
        "confirmação de cada facto."
    )
    st.divider()
    st.markdown(read_md("album_credits_aurora_bem_bonda.md"))

elif page == "Cronologia":
    st.title("Cronologia")
    st.markdown(
        "Esta cronologia segue o trabalho **documentado** do Tó com a CRIATURA, "
        "da gravação ao lançamento dos dois álbuns. Cada marco está sustentado "
        "pelos créditos oficiais e pela prova recolhida no arquivo. É um fio "
        "condutor do percurso que a banda fez com ele em estúdio."
    )
    st.divider()
    st.markdown(
        "**📺 1989 — Televisão** · "
        "*Haja Música — Parte II*, RTP 2, 9 de Junho de 1989. "
        "Tó Pinheiro da Silva e Pedro Ayres Magalhães falam sobre António Variações. "
        "Tó aparece em câmara a partir de ~20:43. "
        "[🎬 Ver no arquivo RTP](https://arquivos.rtp.pt/conteudos/haja-musica-parte-ii-2/)"
    )
    st.caption("Nota: o vídeo abre em nova aba — não pode ser incorporado por direitos de autor RTP.")
    st.markdown("")
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

elif page == "Memórias":
    MEMORIES_FILE = "to_pinheiro_manual_memories.md"

    PRIVACY_COLORS = {
        "Público": "#27ae60",
        "Banda": "#f39c12",
        "Privado": "#c0392b",
    }

    def parse_memories(text: str) -> list[dict]:
        """Extract real memory entries from the manual memories markdown.

        A ``##`` block only counts as a memory if it contains BOTH the
        ``**Quem:**`` and ``**Privacidade:**`` metadata lines. This keeps the
        template scaffolding (## Como usar, ## Categorias, ## EXEMPLO, etc.)
        from being rendered as memory cards — none of those carry that
        metadata, so a template-only file parses to zero memories.
        """
        memories: list[dict] = []
        # Split on level-2 headings ("## ..."); keep heading text via lookahead.
        import re

        blocks = re.split(r"(?m)^##\s+", text)
        for block in blocks:
            if not block.strip():
                continue
            lines = block.splitlines()
            title = lines[0].strip()
            body_lines = lines[1:]
            meta: dict[str, str] = {}
            story_lines: list[str] = []
            for raw in body_lines:
                line = raw.strip()
                m = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", line)
                if m:
                    meta[m.group(1).strip()] = m.group(2).strip()
                    continue
                # Stop the story at a horizontal rule terminating the block.
                if line == "---":
                    break
                story_lines.append(raw)
            # Only a real memory if it has the required metadata.
            if "Quem" not in meta or "Privacidade" not in meta:
                continue
            story = "\n".join(story_lines).strip()
            memories.append(
                {
                    "title": title,
                    "author": meta.get("Quem", ""),
                    "when": meta.get("Quando", ""),
                    "privacy": meta.get("Privacidade", ""),
                    "added": meta.get("Adicionado em", ""),
                    "photo_note": meta.get("Nota fotográfica", ""),
                    "story": story,
                }
            )
        return memories

    st.title("Memórias")
    st.caption(
        "Histórias, momentos e recordações sobre o Tó — escritas por quem esteve lá."
    )

    # ----- Secção 1 — memórias existentes -----
    memories = parse_memories(read_md(MEMORIES_FILE))

    if not memories:
        st.info(
            "Ainda não há memórias adicionadas.\n\n"
            "Usa o formulário abaixo para adicionar a primeira."
        )
    else:
        for mem in memories:
            color = PRIVACY_COLORS.get(mem["privacy"], "#7f8c8d")
            pill = (
                f"<span style='background-color:{color};color:#ffffff;"
                "padding:2px 10px;border-radius:12px;font-size:0.75rem;"
                f"font-weight:600;'>{mem['privacy']}</span>"
            )
            st.markdown(f"### {mem['title']}")
            subline = f"Por {mem['author']}"
            if mem["when"]:
                subline += f" · {mem['when']}"
            st.caption(subline)
            st.markdown(pill, unsafe_allow_html=True)
            if mem["story"]:
                st.markdown(mem["story"])
            if mem["photo_note"]:
                st.caption(f"📷 {mem['photo_note']}")
            st.divider()

    # ----- Secção 2 — adicionar uma memória -----
    st.subheader("Adicionar uma memória")

    with st.form("add_memory", clear_on_submit=True):
        title = st.text_input("Título da memória")
        author = st.text_input("O teu nome (ou iniciais)")
        when = st.text_input("Quando foi? (data, período, ou época aproximada)")
        story = st.text_area(
            "Conta o momento (em português, na tua língua natural)"
        )
        privacy = st.selectbox(
            "Nível de privacidade",
            [
                "Banda",
                "Privado",
                "Público",
            ],
        )
        photo_note = st.text_input(
            "Tens uma foto associada? (descreve-a ou deixa em branco)"
        )
        submitted = st.form_submit_button("Guardar memória")

    if submitted:
        errors = []
        if not title.strip():
            errors.append("O título não pode ficar em branco.")
        if not author.strip():
            errors.append("O teu nome não pode ficar em branco.")
        if len(story.strip()) < 20:
            errors.append("A memória tem de ter pelo menos 20 caracteres.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            from datetime import date

            when_value = when.strip() if when.strip() else "Não especificado"
            block = (
                f"## {title.strip()}\n\n"
                f"**Quem:** {author.strip()}\n"
                f"**Quando:** {when_value}\n"
                f"**Privacidade:** {privacy}\n"
                f"**Adicionado em:** {date.today().isoformat()}\n"
            )
            if photo_note.strip():
                block += f"**Nota fotográfica:** {photo_note.strip()}\n"
            block += f"\n{story.strip()}\n\n---\n\n"

            path = CONTENT / MEMORIES_FILE
            with path.open("a", encoding="utf-8") as f:
                f.write(block)

            st.success(
                "✅ Memória guardada. Obrigado por contribuíres para o arquivo."
            )
            st.rerun()
