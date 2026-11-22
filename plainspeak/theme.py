"""The look of PlainSpeak: colors, fonts, page layout and line icons (the Nov 22 design).
Fixed strings only: nothing from a letter or the AI is ever put into this CSS."""

# Line icons (Lucide, ISC license), drawn in the current text color.
_PATHS = {
    "folder": '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    "message": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "money": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/>',
    "shield": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
    "help": '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    "sms": '<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M12 18h.01"/>',
    "chat": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    "pencil": '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>',
    "clip": '<path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>',
    "camera": '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3z"/><circle cx="12" cy="13" r="3"/>',
    "cog": '<circle cx="12" cy="12" r="3"/><path d="M12 1v3M12 20v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12M1 12h3M20 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12"/>',
}


def icon(name: str, size: int = 20) -> str:
    """An inline line icon. Decorative: screen readers skip it (the text next to it says the same)."""
    return (f'<svg class="ps-i" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
            f'{_PATHS[name]}</svg>')


CSS = """
<style>
:root {
  --cream: #F1ECE2; --green: #1F3B2D; --orange: #B84E25; --orange-text: #9E3F1A; --orange-big: #C4572D;
  --gold: #F2C46D; --muted: #4A5D52; --line: #D6CCB8; --soft: #E7DFCF;
  --serif: "Fraunces", Georgia, "Times New Roman", serif;
}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarCollapseButton"]
    {display: none !important;}
[data-testid="stHeader"] {background: transparent;}
.block-container, [data-testid="stMainBlockContainer"] {max-width: 1160px; padding-top: 2.2rem; padding-bottom: 5rem;}
.ps-card, .ps-quote, .ps-step, [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"]
    {overflow-wrap: anywhere;}
.ps-i {display: inline-block; vertical-align: -0.2em; flex: none;}
.ps-muted {color: var(--muted);}

/* ---- top bar ---- */
.ps-brand {font-family: var(--serif) !important; font-weight: 700 !important; font-size: 1.9rem !important; color: var(--green) !important; margin: 0 !important;
  letter-spacing: -.01em; white-space: nowrap;}
.st-key-ps-top {margin-bottom: 1.2rem;}
.st-key-ps-top [data-testid="stCheckbox"] p {font-size: .92rem; color: var(--green);}
.st-key-nav-letters button {background: var(--green) !important; color: #fff !important; border: none !important;
  font-weight: 700; box-shadow: 0 6px 16px rgba(31,59,45,.18);}
.st-key-nav-letters button * {color: #fff !important;}
.ps-on .st-key-nav-letters button, .st-key-nav-letters.ps-on button {background: var(--orange) !important;}

/* ---- buttons: pills ---- */
.stButton button, .stDownloadButton button, .stLinkButton a, [data-testid="stFormSubmitButton"] button
    {border-radius: 999px !important; font-weight: 700; padding: .55rem 1.3rem; min-height: 2.75rem;}
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"]
    {background: var(--orange) !important; border: none !important; color: #fff !important;
     box-shadow: 0 8px 18px rgba(184,78,37,.28);}
[data-testid="stBaseButton-primary"]:hover {background: #A44420 !important;}
[data-testid="stBaseButton-secondary"], .stDownloadButton button
    {background: transparent !important; border: 1.5px solid var(--green) !important; color: var(--green) !important;}
[data-testid="stBaseButton-secondary"]:hover, .stDownloadButton button:hover {background: rgba(31,59,45,.06) !important;}

/* ---- headings ---- */
h1.ps-bigtitle {font-family: var(--serif) !important; font-weight: 500 !important; font-size: 4.2rem !important;
  line-height: 1.05 !important; letter-spacing: -.02em; color: var(--green) !important; text-align: center;
  padding: .6rem 0 .4rem !important; margin: 0 !important;}
h1.ps-bigtitle em, .ps-share h2 em {color: var(--orange-big); font-style: italic;}
h1.ps-h1, h2.ps-h2 {font-family: var(--serif) !important; font-weight: 500 !important; font-size: 2rem !important;
  color: var(--green) !important; display: flex !important; align-items: center !important; gap: .75rem !important; line-height: 1.15 !important;
  margin: 2.4rem 0 1rem !important; padding: 0 !important; letter-spacing: -.01em;}
h1.ps-h1 .ps-i, h2.ps-h2 .ps-i, h3.ps-h3 .ps-i {color: var(--orange);}
h3.ps-h3 {font-family: var(--serif) !important; font-weight: 500 !important; font-size: 1.35rem !important;
  color: var(--green) !important; display: flex !important; align-items: flex-start !important; gap: .7rem !important; line-height: 1.2 !important;
  margin: .4rem 0 .8rem !important; padding: 0 !important;}
h3.ps-h3 .ps-i {margin-top: .2rem;}
.ps-h1 > span[data-heading-text], .ps-h2 > span[data-heading-text], .ps-h3 > span[data-heading-text]
    {display: flex; align-items: center; gap: .75rem;}
.ps-h3 > span[data-heading-text] {align-items: flex-start; gap: .65rem;}
.ps-doc > span[data-heading-text] {display: inline;}
[class*="st-key-step-"], [class*="st-key-doc-"] {width: 100% !important;}
[class*="st-key-step-"] p, [class*="st-key-doc-"] p {white-space: normal !important; overflow: visible !important;
  text-overflow: clip !important;}
.ps-label {font-size: .72rem !important; font-weight: 700 !important; letter-spacing: .12em; text-transform: uppercase;
  color: var(--orange-text) !important; margin: 0 0 .5rem !important;}

/* ---- hero ---- */
.ps-hero {display: grid; grid-template-columns: 1.25fr 1fr; border-radius: 28px; overflow: hidden;
  box-shadow: 0 18px 40px rgba(31,59,45,.14); margin: .4rem 0 .5rem; background: #fff;}
.ps-hero-l {background: var(--green); color: #fff; padding: 2rem 2.2rem 1.8rem; position: relative;}
.ps-hero-r {background: #fff; padding: 2rem 2.2rem; display: flex; flex-direction: column; justify-content: center;}
.ps-badge {display: inline-flex; align-items: center; gap: .4rem; font-size: .72rem; font-weight: 700;
  letter-spacing: .1em; text-transform: uppercase; padding: .32rem .75rem; border-radius: 999px;
  background: var(--orange); color: #fff;}
.ps-badge.medium {background: var(--gold); color: var(--green);}
.ps-badge.low {background: #CFE3D3; color: var(--green);}
h1.ps-doc {font-family: var(--serif) !important; font-weight: 500 !important; font-size: 1.9rem !important;
  line-height: 1.2 !important; color: #fff !important; margin: 1rem 0 .3rem !important; padding: 0 !important;
  padding-right: 120px !important;}
h1.ps-doc em {color: var(--gold); font-style: italic; font-weight: 400;}
.ps-count {font-family: var(--serif); font-weight: 600; font-size: 5.4rem; line-height: 1; letter-spacing: -.035em;
  color: var(--gold); margin: .6rem 0 1rem;}
.ps-count.small {font-size: 2.2rem; letter-spacing: -.01em;}
.ps-next {color: #E8E1D2 !important; font-size: .95rem !important; margin: 0 !important;}
.ps-next b {color: #fff;}
.ps-ring {position: absolute; top: 1.4rem; right: 1.6rem; width: 104px; height: 104px;}
.ps-ring svg {width: 104px; height: 104px; transform: rotate(-90deg);}
.ps-ring .num {position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center;
  justify-content: center; font-family: var(--serif); color: #fff; font-size: 1.45rem; font-weight: 600; line-height: 1;}
.ps-ring .num small {font-family: inherit; font-size: .58rem; letter-spacing: .14em; text-transform: uppercase;
  color: #E8E1D2; margin-top: .25rem; font-weight: 500;}
.ps-why {color: var(--orange-text) !important; font-size: .95rem !important; display: flex; gap: .55rem; margin: 0 0 1.4rem !important;}
.ps-why .ps-i {margin-top: .15rem;}
.ps-first {font-family: var(--serif) !important; font-weight: 600 !important; font-size: 1.5rem !important; line-height: 1.25 !important; color: var(--green) !important;
  margin: 0 0 1.2rem !important;}
a.ps-pill {display: inline-flex; align-items: center; gap: .55rem; align-self: flex-start; background: var(--orange);
  color: #fff !important; text-decoration: none !important; font-weight: 700; padding: .7rem 1.4rem;
  border-radius: 999px; box-shadow: 0 8px 18px rgba(184,78,37,.3);}
a.ps-pill:hover {background: #A44420;}
.ps-from {color: var(--muted) !important; font-size: .85rem !important; margin: .4rem 0 1rem .3rem !important;}

/* ---- summary ---- */
.ps-summary {font-family: var(--serif) !important; font-size: 1.42rem !important; line-height: 1.5 !important; color: var(--green) !important; margin: 0 0 1.4rem !important;}
.ps-summary mark {background: linear-gradient(transparent 62%, var(--gold) 62%); color: inherit; font-weight: 600;
  padding: 0 .05em;}
.ps-divider {border: none; border-top: 1px solid var(--line); margin: .2rem 0 1.2rem;}
.ps-grade {font-size: .78rem; color: var(--muted); display: grid; grid-template-columns: auto 1fr auto;
  gap: .35rem .7rem; align-items: center; max-width: 330px; margin-left: auto;}
.ps-grade {grid-template-columns: auto 150px auto !important; width: max-content;}
.ps-grade .track {display: block; width: 150px;}
.ps-grade .bar {display: block; height: 7px; border-radius: 99px; background: #CDBF9F;}
.ps-grade .bar.sum {background: #2F7A4F;}
.ps-grade b {color: var(--green);}

/* ---- dates, steps, quotes ---- */
.ps-date {display: flex; gap: 1.4rem; align-items: center; margin: .3rem 0 .6rem;}
.ps-tile {width: 74px; flex: none; border-radius: 14px; background: #fff; overflow: hidden; text-align: center;
  box-shadow: 0 6px 16px rgba(31,59,45,.12);}
.ps-tile .m {background: var(--orange); color: #fff; font-size: .7rem; font-weight: 700; letter-spacing: .12em;
  padding: .3rem 0;}
.ps-tile .d {font-family: var(--serif); font-size: 2.1rem; font-weight: 600; color: var(--green); line-height: 1.1;
  padding-top: .25rem;}
.ps-tile .w {font-size: .58rem; letter-spacing: .12em; color: var(--muted); padding-bottom: .45rem; text-transform: uppercase;}
.ps-tile.bad .m {background: #7A1F12;}
.ps-date-t {font-family: var(--serif); font-weight: 600; font-size: 1.45rem; color: var(--green); line-height: 1.2;}
.ps-date-w {color: var(--muted); font-size: 1rem; margin-top: .2rem;}
.ps-quote {font-size: .84rem; color: var(--muted); border-left: 2px solid var(--line); padding: .1rem 0 .1rem .8rem;
  margin: .35rem 0 1rem; line-height: 1.6;}
.ps-chip {display: inline-flex; align-items: center; gap: .25rem; font-size: .76rem; font-weight: 700;
  border-radius: 999px; padding: .08rem .55rem; margin-left: .35rem; white-space: nowrap;}
.ps-chip.ok, .ps-ok {background: #DDEEDF; color: #1E6B3C;}
.ps-chip.bad {background: #F9DCD3; color: #8A2A12; white-space: normal;}
.ps-ok {font-weight: 700;}
.ps-warn {color: #8A2A12; font-weight: 700;}
.ps-step-q {margin: -.2rem 0 1.1rem 2.05rem; padding-bottom: 1.1rem; border-bottom: 1px solid var(--line);}
.ps-step-q .ps-quote {margin-bottom: 0;}
[class*="st-key-step-"] [data-testid="stCheckbox"] p, [class*="st-key-doc-"] [data-testid="stCheckbox"] p
    {font-family: var(--serif); font-weight: 600; font-size: 1.15rem; line-height: 1.35; color: var(--green);}

/* ---- side card ---- */
.st-key-ps-side {background: #fff; border-radius: 28px; padding: 1.9rem 1.7rem 1.6rem;
  box-shadow: 0 18px 40px rgba(31,59,45,.10); margin-top: 1.4rem;}
.ps-list {margin: 0 0 1.6rem; padding-left: 1.15rem; color: var(--green); font-size: .93rem; line-height: 1.6;}
.ps-list li {margin-bottom: .55rem;}
.ps-sep {border: none; border-top: 1px solid var(--soft); margin: 1.4rem 0;}
.ps-banner {background: var(--gold); border-radius: 22px; padding: 1.2rem 1.3rem; display: flex; gap: .9rem;
  color: var(--green); font-size: .92rem; line-height: 1.55; margin: .6rem 0 1.6rem;}
.ps-banner.calm {background: #DDEEDF;}
.ps-banner .ico {width: 38px; height: 38px; border-radius: 12px; background: var(--green); color: var(--gold);
  display: flex; align-items: center; justify-content: center; flex: none;}
.ps-help {display: flex; gap: .7rem; font-size: .9rem; color: var(--muted); line-height: 1.55; margin: .2rem 0 .9rem;}
.ps-help .ps-i {color: var(--orange); margin-top: .2rem;}
.ps-help b, .ps-help a {color: var(--green) !important;}
.ps-share-btns {display: flex; flex-direction: column; gap: .65rem; margin-top: .2rem;}
.ps-share-btns a {display: flex; align-items: center; justify-content: center; gap: .55rem; border: 1.5px solid var(--green);
  border-radius: 999px; padding: .62rem 1rem; color: var(--green) !important; text-decoration: none !important;
  font-weight: 700; font-size: .95rem;}
.ps-share-btns a:hover {background: rgba(31,59,45,.06);}

/* ---- money and contacts ---- */
.ps-grid {display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1.6rem 2.4rem; margin-bottom: 1rem;}
.ps-amt {font-family: var(--serif); font-weight: 600; font-size: 3.3rem; color: var(--orange-big); line-height: 1.05;
  letter-spacing: -.03em;}
.ps-amt.bad {color: #7A1F12;}
.ps-amt-w {color: var(--muted); font-size: .92rem; margin: .2rem 0 .5rem;}
.ps-contact {border-left: 1px solid var(--line); padding-left: 1.4rem;}
.ps-contact:first-child {border-left: none; padding-left: 0;}
.ps-contact .n {font-family: var(--serif); font-weight: 600; font-size: 1.15rem; color: var(--green); line-height: 1.3;}
.ps-contact .y {color: var(--muted); font-size: .88rem; margin: .2rem 0 .6rem;}
.ps-contact .l {display: flex; gap: .5rem; align-items: flex-start; font-size: .95rem; margin: .3rem 0; color: var(--muted);}
.ps-contact .l .ps-i {color: var(--orange); margin-top: .15rem;}
.ps-contact a {color: var(--orange-text) !important; font-weight: 700; text-decoration: none;}

/* ---- ask and reply ---- */
[data-testid="stForm"] {border: none !important; background: #fff; border-radius: 999px; padding: .45rem .5rem .45rem 1.2rem;
  box-shadow: 0 6px 18px rgba(31,59,45,.08);}
[data-testid="stForm"] [data-testid="stTextInputRootElement"], [data-testid="stForm"] [data-baseweb="input"]
    {border: none !important; background: transparent !important;}
[data-testid="stForm"] input {background: transparent !important;}
[data-testid="stRadio"] [role="radiogroup"] {gap: .6rem; flex-wrap: wrap;}
[data-testid="stRadioOption"] {border: 1.5px solid var(--line); border-radius: 999px; padding: .5rem 1.05rem .5rem .75rem;
  margin: 0 !important; background: transparent;}
[data-testid="stRadioOption"][data-selected="true"] {background: var(--green); border-color: var(--green);}
[data-testid="stRadioOption"][data-selected="true"] p {color: #fff !important;}
[data-testid="stExpander"] details {border: none; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line);
  border-radius: 0; background: transparent;}
[data-testid="stExpander"] summary p {font-family: var(--serif); font-weight: 600; font-size: 1.1rem;}

/* ---- my letters + start page ---- */
.st-key-ps-narrow [data-testid="stExpander"] details {border-top: none;}
.st-key-ps-narrow [data-testid="stExpander"] summary {background: transparent !important; padding: 1.15rem 0;}
.st-key-ps-narrow [data-testid="stExpander"] summary > span > span:first-child {display: none;}
.st-key-ps-narrow [data-testid="stExpander"] summary > span {width: 100%;}
.st-key-ps-narrow [data-testid="stExpander"] summary p {font-size: 1.3rem !important;}
.st-key-ps-narrow [data-testid="stExpander"] summary::after {content: "+"; color: var(--orange); font-size: 1.7rem;
  line-height: 1; margin-left: auto; padding-left: 1rem;}
.st-key-ps-narrow [data-testid="stExpander"] details[open] summary::after {content: "×";}
.st-key-ps-narrow [data-testid="stExpander"] summary {display: flex; align-items: center;}
.st-key-ps-narrow [data-testid="stExpanderDetails"] {padding-left: 0; padding-right: 3rem; color: var(--muted);}
.st-key-ps-narrow {max-width: 964px; margin: 0 auto;}
.ps-center {text-align: center;}
.ps-icotile {width: 80px; height: 80px; border-radius: 22px; background: var(--orange); color: #fff; display: inline-flex;
  align-items: center; justify-content: center; box-shadow: 0 10px 24px rgba(184,78,37,.3); margin-top: 1.4rem;}
.ps-icotile.soft {width: 62px; height: 62px; border-radius: 16px; background: #F6DED2; color: var(--orange); box-shadow: none; margin-top: .2rem;}
.ps-sub {color: var(--muted) !important; font-size: 1.2rem !important; line-height: 1.6 !important; text-align: center; max-width: 620px; margin: .6rem auto 2.2rem !important;}
.st-key-ps-empty {border: 2px dashed #CDBF9F; border-radius: 28px; padding: 2.4rem 1rem 2.6rem;}
.ps-empty-t {font-family: var(--serif); font-weight: 600; font-size: 1.8rem; color: var(--green); margin: .8rem 0 .2rem;}
.ps-empty-s {color: var(--muted); font-size: 1rem; margin-bottom: .6rem;}
.ps-disc {background: var(--green); color: #E8E1D2; border-radius: 999px; padding: 1.3rem 2.2rem; display: flex; gap: 1rem;
  align-items: center; font-size: .95rem; line-height: 1.55; margin: 2.6rem 0 1rem;}
.ps-disc .ps-i {color: var(--gold);}
.ps-disc b {color: #fff;}
.ps-saved {display: flex; justify-content: space-between; align-items: center; gap: 1rem;}
.ps-steps {display: grid; grid-template-columns: repeat(3, 1fr); gap: .9rem; margin: 0 0 1.6rem;}
.ps-step {background: #fff; border-radius: 22px; padding: 1.2rem 1rem; text-align: center; color: var(--muted);
  font-size: .92rem; box-shadow: 0 8px 20px rgba(31,59,45,.07);}
.ps-step b {display: block; font-family: var(--serif); font-size: 1.1rem; color: var(--green); margin: .5rem 0 .2rem;}
.ps-step .ps-icotile.soft {width: 48px; height: 48px; border-radius: 14px;}
.ps-card {border-radius: 20px; padding: 1rem 1.3rem; margin: .5rem 0; background: #fff; border: 1px solid var(--soft);}
.ps-card.ps-high {border: 2px solid #B84E25;}
.ps-card.ps-medium {border: 2px solid #C99A3B;}
.ps-card.ps-low {border: 2px solid #2F7A4F;}

@media (max-width: 820px) {
  .ps-hero {grid-template-columns: 1fr;}
  .ps-hero-l, .ps-hero-r {padding: 1.5rem 1.4rem;}
  .ps-count {font-size: 3.6rem;}
  .ps-ring, .ps-ring svg {width: 84px; height: 84px;}
  h1.ps-doc {font-size: 1.5rem !important; padding-right: 92px !important;}
  h1.ps-bigtitle {font-size: 2.8rem !important;}
  h2.ps-h2 {font-size: 1.6rem !important;}
  .ps-summary {font-size: 1.2rem !important;}
  .ps-amt {font-size: 2.5rem;}
  .ps-contact {border-left: none; padding-left: 0;}
  .ps-disc {border-radius: 24px; padding: 1.1rem 1.3rem;}
  .ps-steps {grid-template-columns: 1fr;}
  .ps-grade {margin-left: 0;}
  [data-testid="stForm"] {border-radius: 24px;}
}
</style>
"""

BIG_TEXT = """<style>
.stMarkdown p, .stMarkdown li, .ps-card, label p, button p, .stCaption, [data-testid="stCaptionContainer"],
.ps-list, .ps-help, .ps-banner, .ps-why, .ps-next, .ps-date-w, .ps-amt-w, .ps-contact .y, .ps-contact .l, .ps-sub,
.ps-disc, .ps-share-btns a, .ps-step
    {font-size: 1.3rem !important; line-height: 1.6 !important;}
.ps-quote {font-size: 1.1rem !important;}
.ps-summary {font-size: 1.75rem !important;}
.ps-first {font-size: 1.8rem !important;}
[class*="st-key-step-"] [data-testid="stCheckbox"] p, [class*="st-key-doc-"] [data-testid="stCheckbox"] p
    {font-size: 1.4rem !important;}
</style>"""

HIGH_CONTRAST = """<style>
.stApp, [data-testid="stHeader"], .ps-card, .ps-hero, .ps-hero-l, .ps-hero-r, .ps-banner, .ps-disc, .ps-tile,
.ps-tile .m, .ps-step, .st-key-ps-side, .st-key-ps-empty, .ps-icotile, .ps-badge, .ps-chip, [data-testid="stForm"],
[data-testid="stSelectbox"] div, [data-baseweb="select"] div, [data-baseweb="select"] input,
[data-baseweb="popover"] *, [role="listbox"] *,
[data-testid="stAlert"], [data-testid="stAlertContainer"], [data-testid="stAlert"] *,
textarea, input, [data-testid="stFileUploaderDropzone"], [data-testid="stExpander"] details
    {background: #000 !important; color: #fff !important; box-shadow: none !important;}
.stApp *, .ps-hero * {color: #fff !important;}
.ps-hero-l, .ps-hero-r, .ps-banner, .ps-disc, .ps-tile, .st-key-ps-side, .st-key-ps-empty, .ps-step, .ps-card,
[data-testid="stForm"], [data-testid="stAlertContainer"], .ps-badge, .ps-chip, .ps-icotile
    {border: 2px solid #ffff00 !important;}
[data-baseweb="select"] > div, textarea, button, a.ps-pill, .ps-share-btns a, [data-testid="stFileUploaderDropzone"],
[data-testid="stRadioOption"]
    {border: 2px solid #ffff00 !important; background: #000 !important; box-shadow: none !important;}
.ps-count, .ps-amt, h1.ps-doc em, h1.ps-bigtitle em, .ps-ring .num {color: #ffff00 !important;}
.ps-summary mark {background: none !important; text-decoration: underline 3px #ffff00 !important;}
.ps-ring circle {stroke: #ffff00 !important;}
.ps-grade .bar {background: #fff !important;}
a, .stApp a {color: #00ffff !important; text-decoration: underline !important;}
.ps-ok, .ps-chip.ok {color: #7CFC00 !important;} .ps-warn, .ps-warn *, .ps-chip.bad {color: #ffff00 !important;}
.ps-quote {border-left-color: #ffff00 !important;}
</style>"""
