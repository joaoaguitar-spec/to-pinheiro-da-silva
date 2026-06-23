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
    # Estética mínima: título centrado e a caixa de login limitada a uma
    # largura fixa (não mais larga que o título) e centrada. O CSS só é
    # injectado no ecrã de login — nas páginas autenticadas esta função
    # retorna cedo, por isso não afecta o formulário das Memórias.
    # Limita toda a coluna do login a uma largura fixa e centrada — assim o
    # título, a foto e a caixa de login ficam todos alinhados ao centro.
    # Só é injectado no ecrã de login (esta função retorna cedo após auth).
    st.markdown(
        "<style>"
        ".block-container{max-width:600px;}"
        "div[data-testid='stForm']{margin-top:1rem;}"
        "</style>"
        "<h1 style='text-align:center;margin-bottom:1.25rem;'>"
        "Arquivo Tó Pinheiro da Silva</h1>",
        unsafe_allow_html=True,
    )
    login_img = Path(__file__).parent / "assets" / "to_pinheiro_login.jpg"
    if login_img.exists():
        st.image(str(login_img), width="stretch")
    with st.form("login"):
        pw = st.text_input("Palavra-passe", type="password")
        submitted = st.form_submit_button("Entrar", width="stretch")
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


@st.cache_data
def load_discography() -> list[dict]:
    """Carrega a discografia (Discogs) a partir do ficheiro versionado.

    O ficheiro ``content/discography.json`` é uma cópia deliberada e versionada
    do output do scraper (que fica fora do Git). As capas usam o ``cover_url``
    remoto do Discogs, para não ser preciso versionar centenas de imagens.
    """
    import json

    p = CONTENT / "discography.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


PAGES = ["Início", "Ouvir", "Álbuns", "Cronologia", "Memórias"]


def go_to(target: str) -> None:
    """Callback de navegação (usado nos botões do Início).

    Tem de correr como ``on_click`` — só dentro de um callback é permitido
    alterar o valor de um widget já instanciado (a radio tem ``key="nav"``).
    Fazê-lo no corpo do script levantaria ``StreamlitAPIException``.
    """
    st.session_state.nav = target


# ---------- navegação ----------
st.sidebar.title("Arquivo Tó")
st.sidebar.caption("Engenheiro de som · CRIATURA")
if "nav" not in st.session_state:
    st.session_state.nav = "Início"
page = st.sidebar.radio("Navegar", PAGES, key="nav")

st.sidebar.divider()
if st.sidebar.button("Sair", width="stretch"):
    st.session_state.auth_ok = False
    st.rerun()


# ---------- páginas ----------
if page == "Início":
    st.title("Tó Pinheiro da Silva")
    st.markdown(
        "O Tó — **António Pinheiro da Silva** — é o engenheiro de som que "
        "**misturou e masterizou** os dois álbuns da CRIATURA. Este arquivo é um "
        "**tributo em vida** à sua obra e ao que a banda viveu com ele."
    )

    # ----- Estatísticas (dados Discogs) -----
    st.markdown(
        """
        <div style='display:flex;gap:2.5rem;flex-wrap:wrap;margin:1.5rem 0 0.5rem;'>
          <div>
            <div style='font-size:3rem;font-weight:800;line-height:1;'>353</div>
            <div style='opacity:0.7;'>créditos</div>
          </div>
          <div>
            <div style='font-size:3rem;font-weight:800;line-height:1;'>277</div>
            <div style='opacity:0.7;'>discos</div>
          </div>
          <div>
            <div style='font-size:3rem;font-weight:800;line-height:1;'>1976–2025</div>
            <div style='opacity:0.7;'>quase 50 anos</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Fonte: Discogs · perfil de António Pinheiro da Silva")

    st.divider()

    # ----- Links para as outras páginas -----
    st.markdown("#### Explorar o arquivo")
    c1, c2, c3, c4 = st.columns(4)
    c1.button("🎧 Ouvir", width="stretch", on_click=go_to, args=("Ouvir",))
    c2.button("💿 Álbuns", width="stretch", on_click=go_to, args=("Álbuns",))
    c3.button("🗓️ Cronologia", width="stretch", on_click=go_to, args=("Cronologia",))
    c4.button("📝 Memórias", width="stretch", on_click=go_to, args=("Memórias",))

elif page == "Ouvir":
    # A página Ouvir é renderizada como um único bloco HTML (grelha de 3
    # colunas, cartões uniformes, tema escuro). O ficheiro versionado
    # ``ouvir_standalone.html`` é a fonte de verdade para o layout, o estilo e
    # os URLs dos embeds (2 Bandcamp + 8 Spotify, todos a 352px).
    ouvir_html_path = Path(__file__).parent / "ouvir_standalone.html"
    if ouvir_html_path.exists():
        components.html(
            ouvir_html_path.read_text(encoding="utf-8"),
            height=2400,
            scrolling=True,
        )
    else:
        st.warning("Layout indisponível (falta `ouvir_standalone.html`).")

elif page == "Álbuns":
    st.title("Álbuns")
    st.markdown(
        "A discografia do Tó tal como documentada no **Discogs** — quase 50 anos "
        "de trabalho, de 1976 a 2025. Cada ficha indica o **papel** dele no disco "
        "(participação, mistura, produção) e liga à página do Discogs."
    )

    # Créditos curados dos dois álbuns da CRIATURA (preservados num expander).
    with st.expander("💿 Créditos detalhados — Aurora & Bem Bonda (CRIATURA)"):
        st.markdown(read_md("album_credits_aurora_bem_bonda.md"))

    discography = load_discography()
    if not discography:
        st.warning("Discografia indisponível (falta `content/discography.json`).")
    else:
        # ----- Filtros: década e papel -----
        def decade_of(year) -> str:
            if not isinstance(year, int) or year <= 0:
                return "Sem data"
            return f"{(year // 10) * 10}s"

        decades = sorted(
            {decade_of(r.get("year")) for r in discography},
            key=lambda d: (d == "Sem data", d),
        )
        roles = sorted({r.get("role") for r in discography if r.get("role")})

        col_d, col_r = st.columns(2)
        sel_decade = col_d.selectbox("Década", ["Todas"] + decades)
        sel_role = col_r.selectbox("Papel", ["Todos"] + roles)

        filtered = [
            r
            for r in discography
            if (sel_decade == "Todas" or decade_of(r.get("year")) == sel_decade)
            and (sel_role == "Todos" or r.get("role") == sel_role)
        ]
        # Mais recentes primeiro; sem data no fim.
        filtered.sort(key=lambda r: (r.get("year") or 0), reverse=True)

        st.caption(f"{len(filtered)} de {len(discography)} registos")
        st.divider()

        # ----- Grelha (4 por linha) -----
        PER_ROW = 4
        for i in range(0, len(filtered), PER_ROW):
            cols = st.columns(PER_ROW)
            for col, rec in zip(cols, filtered[i : i + PER_ROW]):
                with col:
                    cover = rec.get("cover_url")
                    if cover:
                        st.image(cover, width='stretch')
                    title = rec.get("title") or "—"
                    url = rec.get("discogs_url")
                    if url:
                        st.markdown(f"**[{title}]({url})**")
                    else:
                        st.markdown(f"**{title}**")
                    st.caption(
                        f"{rec.get('artist') or '—'}  \n"
                        f"{rec.get('year') or 's/d'} · {rec.get('role') or '—'}"
                    )

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
                    "quote": meta.get("Citação", ""),
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
            if mem["quote"]:
                st.markdown(f"> *{mem['quote']}*")
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
        quote = st.text_input(
            "Citação (opcional) — uma frase do Tó ou sobre o Tó"
        )
        privacy = st.selectbox(
            "Nível de privacidade",
            [
                "Banda",
                "Privado",
                "Público",
            ],
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
            if quote.strip():
                block += f"**Citação:** {quote.strip()}\n"
            block += f"\n{story.strip()}\n\n---\n\n"

            path = CONTENT / MEMORIES_FILE
            # Guard: if the file doesn't end in a newline, the appended "## ..."
            # heading would glue onto the last line and fail to parse. Prepend a
            # newline only when needed (skip for empty/new files).
            existing = path.read_text(encoding="utf-8") if path.exists() else ""
            prefix = "" if (not existing or existing.endswith("\n")) else "\n"
            with path.open("a", encoding="utf-8") as f:
                f.write(prefix + block)

            st.success(
                "✅ Memória guardada. Obrigado por contribuíres para o arquivo."
            )
            st.rerun()
