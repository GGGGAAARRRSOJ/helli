import random
import re
import unicodedata
import streamlit as st
from collections import deque

# ====================== Page & Styles ======================
st.set_page_config(page_title="Angelic ⇄ Demonic Translator — v3.4", page_icon="🕊️", layout="wide")

st.markdown(
    """
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Cinzel+Decorative:wght@400;700&family=Cormorant+Garamond:wght@400;600&family=Uncial+Antiqua&family=UnifrakturMaguntia&family=Fruktur&family=Metal+Mania&family=Nosifer&display=swap" rel="stylesheet">
<style>
  :root{ --bg:#0c0f14; --panel:#171a1e; --ink:#e9edf2; --muted:#98a0a8; --gold:#f7e9b5; --gold2:#ffe39a; --aura1:rgba(255,226,140,.55); --aura2:rgba(255,238,170,.75); }
  .wrap{max-width:1060px;margin:0 auto}
  .panel{background:var(--panel);border:1px solid #283038;border-radius:14px;padding:14px;margin-bottom:14px;box-shadow:0 0 0 1px #0a0b0c inset,0 8px 22px rgba(0,0,0,.35)}
  .output{min-height:150px;padding:14px;background:#0e1115;border:1px solid #283038;border-radius:10px;overflow-wrap:anywhere;word-break:break-word}
  .label{color:var(--muted);font-size:.95rem;margin-bottom:6px}
  .angel-1{font-family:"Cormorant Garamond","Uncial Antiqua","Cinzel",serif;color:var(--gold);text-shadow:0 0 .6px #c9b,0 0 8px var(--aura1);letter-spacing:.18px;text-align:center;line-height:1.75}
  .angel-2{font-family:"Uncial Antiqua","Cormorant Garamond","Cinzel Decorative",serif;color:var(--gold);text-shadow:0 0 1px #dcc,0 0 14px var(--aura1),0 0 22px rgba(255,210,120,.45);letter-spacing:.24px;text-align:center;line-height:1.85}
  .angel-3{font-family:"Cinzel Decorative","Uncial Antiqua","Cormorant Garamond",serif;color:var(--gold2);text-shadow:0 0 2px #efe,0 0 24px var(--aura2),0 0 40px rgba(255,220,150,.6);letter-spacing:.3px;text-align:center;line-height:1.92}
  .demon-1{font-family:"Fruktur","UnifrakturMaguntia",serif;letter-spacing:.15px;text-shadow:0 0 1px rgba(180,0,0,.35)}
  .demon-2{font-family:"UnifrakturMaguntia","Fruktur",serif;letter-spacing:.2px;text-shadow:0 0 2px rgba(210,0,0,.5)}
  .demon-3{font-family:"Metal Mania","Nosifer","UnifrakturMaguntia",serif;letter-spacing:.28px;text-shadow:0 0 3px rgba(255,40,0,.65),0 0 10px rgba(255,100,0,.35)}
  .muted{color:var(--muted)}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="wrap">', unsafe_allow_html=True)
st.markdown("<h1>🕊️ Angelic ⇄ Demonic Translator — v3.4</h1>", unsafe_allow_html=True)
st.markdown('<div class="muted">Inline • Equal insert frequency • Verse intro for angel • Strong decoder</div>', unsafe_allow_html=True)

# ====================== Helpers ======================
HALO = "\u030A"
TOK_RE = re.compile(r"(\w+|\s+|[^\w\s]+)", re.UNICODE)

def tokenize(s: str):
    return TOK_RE.findall(s) or []

def pick(a):
    return a[random.randrange(len(a))]

def rep_all(s: str, a: str, b: str) -> str:
    return s if not s else s.replace(a, b)

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def var_scale(base: float, variation: float, length: int = 5) -> float:
    len_boost = min(0.15, max(0.0, (length - 5) * 0.02))
    return clamp01(base * (0.5 + variation * 0.9 + len_boost))

def safe_norm(s: str, form: str) -> str:
    try:
        return unicodedata.normalize(form, s)
    except Exception:
        return s

class InsertPicker:
    """Shuffled round-robin to keep frequencies balanced across a list of inserts."""
    def __init__(self, items):
        self.source = list(items)
        self._reset()

    def _reset(self):
        self.queue = list(self.source)
        random.shuffle(self.queue)
        self.idx = 0

    def next(self):
        if not self.queue:
            return ""
        val = self.queue[self.idx]
        self.idx += 1
        if self.idx >= len(self.queue):
            self._reset()
        return val

# ====================== Verse-style intros for angel mode ======================
VERSE_PREFIXES = [
    '(PSALM 23:4) — "',
    '(REVELATION 22:13) — "',
    '(GENESIS 1:3) — "',
    '(ISAIAH 41:10) — "',
    '(HALLELUJAH) — "',
    '(GLORIA IN EXCELSIS) — "',
    'In the name of the Light, let this be spoken: ',
    '✧ Thus speaks the Archangel: ',
    '✧ Words from the Throne of Heaven: ',
    '(SANCTUS) — "',
    '(ALLELUIA) — "',
    '(DEO GRATIAS) — "',
    '(TYRAEL 3:16) — "',
    '(AURIEL 7:7) — "',
    'By the eternal covenant, hear this: ',
    '(PAX VOBISCUM) — "',
    '(IMPERIUS 12:4) — "',
    '(BRAHMA SPEAKS) — "',
    '(VISHNU 9:11) — "',
    '(SHIVA 8:8) — "',
]

# ====================== Packs ======================
ANG_PACKS = {
    "liturgical": {
        "vowels": {"a":"ā","e":"ē","i":"ī","o":"ō","u":"ū","y":"ȳ"},
        "digraphs": [[("the","θe"),("The","Θe")],[("ph","φ"),("Ph","Φ")],[("sh","š"),("Sh","Š")]],
        "pre": ["el’","al’","ael’","iel’"],
        "suf": ["-ael","-iel","-elion","-hael"],
        "inserts": ["(AMEN)","(ALLELUIA)","(GLORIA)","(SANCTUS)","(PAX)","(DEO GRATIAS)","(FIAT LUX)","(GOD)"],
    },
    "high_heavens": {
        "vowels": {"a":"ā","e":"ē","i":"ī","o":"ō","u":"ū","y":"ȳ"},
        "digraphs": [[("the","θe"),("The","Θe")],[("th","þ"),("Th","Þ")]],
        "pre": ["aer’","cel’","aur’"],
        "suf": ["-ael","-iel","-arion"],
        "inserts": ["(TYRAEL)","(AURIEL)","(IMPERIUS)","(SILVER CITY)","(HIGH HEAVENS)"],
    },
    "elvish": {
        "vowels": {"a":"ā","e":"ē","i":"ī","o":"ō","u":"ū","y":"ȳ"},
        "digraphs": [[("sh","š"),("Sh","Š")]],
        "pre": ["loth’","galad’","el’","al’"],
        "suf": ["-iel","-ielë","-elion"],
        "inserts": ["(HALLELUJAH)","(ALHAMDOULILLAH)","(ALLAH)","(BRAHMA)","(VISHNU)","(SHIVA)"],
    },
}

DEM_PACKS = {
    "prime_evils": {
        "vowels": {"a":"â","e":"ê","i":"î","o":"ô","u":"û","y":"ŷ"},
        "digraphs": [[("the","ðe"),("The","Ðe")],[("th","þ"),("Th","Þ")],[("ph","ƒ"),("Ph","Ƒ")]],
        "pre": ["ba’","me’","za’","dra’","kr’"],
        "suf": ["-oth","-’rim","-rax","-goth","-krath","-zoth"],
        "inserts": ["(INFERNO)","(PRIME EVIL)","(HELLFIRE)","(LORD OF TERROR)","(ABYSS)","(IBLIS)","(SHAYTAN)"],
    },
    "occult_gothic": {
        "vowels": {"a":"â","e":"ê","i":"î","o":"ô","u":"û","y":"ŷ"},
        "digraphs": [[("sh","ʃ"),("Sh","ʃ")],[("ch","χ"),("Ch","Χ")]],
        "pre": ["noct’","mal’","blasp’","prof’","void’"],
        "suf": ["-mal","-hex","-blight","-gore","-bane"],
        "inserts": ["(BLOOD)","(CURSE)","(OMEN)","(RITUAL)","(SEAL)","(MARID)"],
    },
    "leviathan": {
        "vowels": {"a":"â","e":"ê","i":"î","o":"ô","u":"û","y":"ŷ"},
        "digraphs": [[("th","þ"),("Th","Þ")]],
        "pre": ["levi’","aby’","krak’","dred’"],
        "suf": ["-maw","-depth","-brine","-void"],
        "inserts": ["(MAELSTROM)","(DROWN)","(DEEP)","(BLACKWATER)","(RIFT)","(RAKSHASA)","(ASURA)","(KALI)"],
    },
}

# Common angel inserts + equal-frequency pickers
ANG_COMMON_INSERTS = sorted({ins for p in ANG_PACKS.values() for ins in p.get("inserts", [])})

# ====================== Per-token stylers ======================
ANG_SEP = ["✧","❖","✺","✶","✵","✦"]
DEM_SEP = ["☠","☲","☵","⚸","𖤍","𖤐"]
CM_ABOVE = ["\u0300","\u0301","\u0302","\u0303","\u0304","\u0306","\u0307","\u0308","\u030A","\u0311","\u0336","\u034f"]
CM_BELOW = ["\u0323","\u0324","\u0325","\u0326","\u032C","\u0331"]
CONS_ORN = {"s":"ſ","t":"†","r":"ŕ"}
HALO = "\u030A"

def pack_for(mode: str, lvl: int):
    if mode == "angel":
        key = ["liturgical", "high_heavens", "elvish"][(lvl-1)%3]
        return ANG_PACKS[key]
    key = ["prime_evils", "occult_gothic", "leviathan"][(lvl-1)%3]
    return DEM_PACKS[key]

def angelify_token(token: str, pack: dict, lvl: int, variation: float, density: float) -> str:
    if not re.search(r"\w", token):
        return token
    letters = re.sub(r"[^A-Za-z]", "", token)
    L = len(letters) or 1

    def repl_vowel(ch):
        lc = ch.lower()
        rep = pack.get("vowels", {}).get(lc, ch)
        p = var_scale([0, .34, .5, .74][lvl], variation, L)
        return rep.upper() if (random.random() < p and ch.isupper()) else (rep if random.random() < p else ch)

    out = re.sub(r"[aeiouyAEIOUY]", lambda m: repl_vowel(m.group(0)), token)

    if re.match(r"^[A-Za-z]", out) and random.random() < var_scale([0,.10,.18,.30][lvl], variation, L):
        out += HALO

    if pack.get("digraphs"):
        dig = random.choice(pack["digraphs"])
        for a, b in dig:
            out = rep_all(out, a, b)

    preP = var_scale([0,.06,.10,.14][lvl], variation, L) * (0.4 + density * 0.8)
    sufP = var_scale([0,.06,.10,.14][lvl], variation, L) * (0.4 + density * 0.8)
    if pack.get("pre") and random.random() < preP:
        out = pick(pack["pre"]) + out
    if pack.get("suf") and random.random() < sufP:
        out = out + pick(pack["suf"])

    if random.random() < var_scale(0.1, variation, L):
        out = re.sub(r"(ae|io|el|or|ea|ie|eo|ai)", lambda m: m.group(0)[0] + "·" + m.group(0)[1] if random.random() < 0.5 else m.group(0), out, flags=re.IGNORECASE)

    return out

def demonify_token(token: str, pack: dict, lvl: int, variation: float, density: float) -> str:
    if not re.search(r"\w", token):
        return token
    letters = re.sub(r"[^A-Za-z]", "", token)
    L = len(letters) or 1

    def repl_vowel(ch):
        lc = ch.lower()
        rep = pack.get("vowels", {}).get(lc, ch)
        p = var_scale([0,.26,.38,.52][lvl], variation, L)
        return rep.upper() if (random.random() < p and ch.isupper()) else (rep if random.random() < p else ch)

    out = re.sub(r"[aeiouyAEIOUY]", lambda m: repl_vowel(m.group(0)), token)

    def orn_cons(m):
        c = m.group(0)
        return CONS_ORN.get(c, c) if random.random() < var_scale([0,.10,.14,.22][lvl], variation, L) else c

    out = re.sub(r"[str]", orn_cons, out)

    def add_marks(m):
        c = m.group(0)
        if random.random() < var_scale([0,.00,.015,.05][lvl], variation, L):
            above = pick(CM_ABOVE)
            below = pick(CM_BELOW) if random.random() < 0.35 else ""
            return c + above + below
        return c

    out = re.sub(r"[A-Za-z]", add_marks, out)

    if pack.get("digraphs"):
        dig = random.choice(pack["digraphs"])
        for a, b in dig:
            out = rep_all(out, a, b)

    if random.random() < var_scale([0,.06,.10,.16][lvl], variation, L) and len(out) > 3:
        idx = 1 + random.randrange(len(out) - 2)
        out = out[:idx] + "·" + out[idx:]

    preP = var_scale([0,.10,.14,.18][lvl], variation, L) * (0.45 + density * 0.8)
    sufP = var_scale([0,.10,.14,.18][lvl], variation, L) * (0.45 + density * 0.8)
    if pack.get("pre") and random.random() < preP:
        out = pick(pack["pre"]) + out
    if pack.get("suf") and random.random() < sufP:
        out = out + pick(pack["suf"])

    return out

# ====================== Encoder ======================
def encode_sentence(mode: str, lvl: int, text: str, variation: float, density: float, poetry: float) -> str:
    pack = pack_for(mode, lvl)
    toks = tokenize(text)
    out = []

    words = [t for t in toks if re.search(r"\w", t)]
    base_pct = 0.05 + random.random() * 0.05
    level_boost = (lvl - 1) * 0.012
    poetry_boost = poetry * 0.02
    pct = min(0.12, base_pct + level_boost + poetry_boost)
    target_inserts = max(0, int(len(words) * pct))
    inserted = 0

    # Equal-frequency pickers
    if mode == "angel":
        picker = InsertPicker(ANG_COMMON_INSERTS)
    else:
        picker = InsertPicker(pack.get("inserts", []))

    def maybe_insert(i):
        nonlocal inserted
        if inserted >= target_inserts:
            return
        if ((i + 1) % 3) == 0:
            if random.random() < 0.6:
                out.append(picker.next())
                inserted += 1

    sep_bag = ANG_SEP if mode == "angel" else DEM_SEP

    for i, t in enumerate(toks):
        if re.search(r"\w", t):
            styl = angelify_token(t, pack, lvl, variation, density) if mode == "angel" else demonify_token(t, pack, lvl, variation, density)
            out.append(styl)
            if ((i + 1) % (7 if mode == "angel" else 6)) == 0 and random.random() < 0.45:
                out.append(pick(sep_bag))
            maybe_insert(i)
        else:
            out.append(t)

    text_out = "".join(out)

    # Prepend verse-style intro for angel mode
    if mode == "angel":
        intro = pick(VERSE_PREFIXES)
        text_out = intro + text_out

    return text_out

# ====================== Decoder ======================
ALL_PRE = set(sum([p.get("pre", []) for p in ANG_PACKS.values()], []) + sum([p.get("pre", []) for p in DEM_PACKS.values()], []))
ALL_SUF = set(sum([p.get("suf", []) for p in ANG_PACKS.values()], []) + sum([p.get("suf", []) for p in DEM_PACKS.values()], []))

def esc_regex(s: str) -> str:
    return re.escape(s)

AFFIX_PRE = re.compile(r"\b(?:" + "|".join(sorted(map(esc_regex, ALL_PRE), key=len, reverse=True)) + r")", re.IGNORECASE) if ALL_PRE else None
AFFIX_SUF = re.compile(r"(?:" + "|".join(sorted(map(esc_regex, ALL_SUF), key=len, reverse=True)) + r")\b", re.IGNORECASE) if ALL_SUF else None

def decode_to_english(input_text: str) -> str:
    if not input_text:
        return ""
    s = str(input_text)
    s = s.replace("’","'").replace("‘","'").replace("“",'"').replace("”",'"')
    s = re.sub(r"⟨[^⟩]*⟩", "", s)
    s = re.sub(r"[✧❖✺✶✵✦☠☲☵⚸𖤍𖤐·]", "", s)

    # Normalize + strip combining marks
    s = safe_norm(s, "NFKC")
    s = safe_norm(s, "NFD")
    s = re.sub(r"[\u0300-\u036f]", "", s)

    # reverse digraphs
    for a, b in [
        ("ðe","the"),("Ðe","The"),("þ","th"),("Þ","Th"),
        ("ʃ","sh"),("Χ","Ch"),("χ","ch"),("ƒ","ph"),("Ƒ","Ph"),
        ("θ","th"),("Θ","Th"),("š","sh"),("Š","Sh"),("φ","ph"),("Φ","Ph"),
    ]:
        s = s.replace(a, b)

    s = s.replace("ſ","s").replace("†","t").replace("ŕ","r")

    frm = "âêîôûŷÂÊÎÔÛŶäëïöü ÄËÏÖÜĀĒĪŌŪȲāēīōūȳ"
    to  = "aeiouyAEIOUYaeiouAEIOUAEIOUYaeiouy"
    trans = str.maketrans({frm[i]: to[i] for i in range(len(to))})
    s = s.translate(trans)

    # Strip inserts and most verse prefixes in parentheses
    s = re.sub(r"\([^)]{1,160}\)", "", s)

    def strip_affix_word(m):
        w = m.group(0)
        if AFFIX_PRE:
            w = AFFIX_PRE.sub("", w)
        if AFFIX_SUF:
            before = None
            guard = 0
            while before != w and guard < 5:
                before = w
                w = AFFIX_SUF.sub("", w)
                guard += 1
        return w

    s = re.sub(r"\b[^\s]+\b", strip_affix_word, s)
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"[^A-Za-z0-9 ,.\-–—!?:;'()\"_\n]", "", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

# ====================== UI ======================
with st.container():
    cols = st.columns([1,1,1,1,1,1])
    mode = cols[0].selectbox("Mode", ["angel","demon"], index=0)
    level = cols[1].selectbox("Level", ["1","2","3"], index=1)
    variation = cols[2].slider("Variation", 0, 100, 55) / 100.0
    density = cols[3].slider("Density", 0, 100, 45) / 100.0
    poetry = cols[4].slider("Poetry", 0, 100, 30) / 100.0
    seed_text = cols[5].text_input("Seed (optional)", value="")

    if seed_text:
        try:
            random.seed(int(seed_text))
        except ValueError:
            random.seed(abs(hash(seed_text)) % (2**32))

st.markdown('<div class="panel">', unsafe_allow_html=True)
plain = st.text_area("Enter plain English", height=140, placeholder="Type here…")

stylized = encode_sentence(mode, int(level), plain or "", variation, density, poetry)
decoded = decode_to_english(stylized)

visual_cls = f"{'angel' if mode=='angel' else 'demon'}-{level}"
st.markdown('<div class="label">Stylized</div>', unsafe_allow_html=True)
st.markdown(f'<div class="output {visual_cls}">{stylized}</div>', unsafe_allow_html=True)
st.markdown('<div class="label" style="margin-top:10px">Decoded preview (auto)</div>', unsafe_allow_html=True)
st.text_area("Decoded preview", value=decoded, height=150, label_visibility="collapsed")

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="label">🔁 Retranslate any stylized text back to normal</div>', unsafe_allow_html=True)
paste = st.text_area("Paste angelic/demonic text here…", height=120, key="paste")
decoded2 = ""
if st.button("Decode This"):
    decoded2 = decode_to_english(paste or "")
st.markdown('<div class="label" style="margin-top:10px">Result</div>', unsafe_allow_html=True)
st.text_area("Result", value=decoded2, height=150, label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
