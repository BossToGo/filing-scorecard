# Scorecard page: design spec

For Simon (member D). Proposed on 23 November 2026 by Igor (A), written with Claude Code (see `AI-USAGE.md`); the
SPEC wording it needs is in SPEC 2.4.2 §3. Target: [`mockup.html`](mockup.html) in this folder (Coca-Cola, real
figures, light then dark, then the states; open it in a browser; the dashed pink notes explain, they are not part of
the design). The screen still only shows what `src/` returns.

The page is a panel in a bank's buy step. It should read like a bank's research note: modern, calm, stern, every
figure traceable.

## 1. Design rules

From Igor's design rules for an earlier app of his (not its look) and the public skill repositories listed in §8.

| Rule | Here |
|---|---|
| Six type roles: weight, not many sizes | 28, 24, 18, 16, 14, 12 px, set in `config.toml` |
| 4-point grid, two radii | Gaps 4 to 48; radius 4 for marks, 8 for widgets |
| One left edge, values on the right | Figures right-aligned, tabular numerals |
| One job per colour | Accent: passed, the button, the selected tab, links. Text colour: failed. Nothing decorative |
| Removal test first | §8 lists what went |
| One depth at a time | Summary, area, check, Sources |
| One thing stands out | Only "Show scorecard" is filled |
| A person wrote it | "**Moderate debt.** Net debt is 109.5% of equity, above the 40% limit." |
| Groups by hairlines, not cards | No boxes, shadows or nested panels |
| One mark shape everywhere | The same 20 px square in the chart, the failed list and the legend |

## 2. Reference patterns

The reference is the app named in `docs/product.md` (Screens and visuals). Its site answered HTTP 403 to our reader,
so the patterns come from 16 screenshots of its mobile app (an Nvidia report; not committed, they are its copyright),
its public `MODEL.markdown` and general knowledge.

1. **Fixed areas of six checks, same order for every company**: companies compare by position.
2. **An area opens with its count, six marks and one sentence with its numbers**: verdict before evidence.
3. **Key figures**: two large amounts, then label and value rows, so check rows stay short.
4. **Checks as statements with the company's figures**, detail one click deeper: a sentence, not a ratio name.
5. **Risks at the top**: our "Failed checks", until strengths and points to watch exist.
6. **Areas as tabs, data sources last**: our Sources tab.

Not taken: the radar shape and its name, red-to-green scores, the dark-and-gold look, gauges, treemaps, numbered
headings, circle ticks, coloured "Label:" checks, AI prompts, upgrade buttons, ownership, insiders, management,
forecasts, news, community, their wording.

## 3. The page, top to bottom (1366×768)

Above the fold even at 125% zoom (about 528 CSS px): inputs, header, area rows, legend, failed list. At 100%, the
open area's score line and sentence too.

| Element | Job | Content | Streamlit |
|---|---|---|---|
| Menu, top right | Theme switch | Light, Dark, System | `toolbarMode = "viewer"` keeps it, hides Deploy |
| Input bar | Company and price (a bank's order ticket would supply both) | Company, Share price (USD), Demo mode, **Show scorecard** | One `st.columns([3,2,2,1.5], vertical_alignment="bottom")`; keys unchanged |
| Start screen | What to do | "Filing Scorecard", one sentence (§6) | `st.title`, `st.markdown` under the inputs |
| Header | Which company, how fresh | SEC name, muted ticker, industry, fiscal year end, 10-K and retrieval dates; typed price on the right | `st.columns([4,1])`, markdown; warnings `st.warning` |
| Area rows | Result at a glance | Name, six marks, "4 passed of 4 assessed", muted "2 not assessed yet" ("yet" only when a later version brings the input, as for P4 and P5; a figure missing in the filings is "not assessed") | HTML in one `st.markdown(unsafe_allow_html=True)`, left of `st.columns([2,1], gap="large")` |
| Legend | Read the marks | Four marks with words, and "not a rating of the share and not advice" | Same block |
| Failed checks | What to read first | Mark, check name, area; empty: "No check failed." | Right column, rows aligned with the area rows |
| Tabs | Open one area | Four areas, then Sources | `st.tabs` |
| Score line, sentence | Area verdict | Six marks, score, one sentence with check values | Markdown; E's template filled through `ui.format` |
| Check rows | One test per line | Icon, **name.**, sentence with figures and limit | `st.expander(label)`, icon in the label |
| Check detail | Proof | Rule; working (the module's explanation); figures; filing link; "Check H3" small | Markdown, HTML table |
| Key figures | Base amounts | Two large amounts, then the area's other input figures | Right column; two `st.metric`; same table |
| Footer | Source and method credit | Two muted lines | `st.divider()`, markdown |

Charts, later and only if the group amends product.md ("tables, not charts"): at most two, Plotly with
`theme="streamlit"`, colours from `chartCategoricalColors`: current assets against liabilities (in the mockup), and
revenue with net income over five years. Both from saved SEC figures only.

## 4. Tokens

| Size | Weight | Role | Set by |
|---|---|---|---|
| 28 | 600 | Company name, start title | `headingFontSizes[0]` |
| 24 | 600 | Large amounts | `metricValueFontSize/Weight` |
| 18 | 600 | Page sections (Sources) | `headingFontSizes[1]` |
| 16 | 400, 600 | Sentences, row names, scores | `baseFontSize`, `headingFontSizes[2]` |
| 14 | 400, 600 | Labels, metadata, tabs, legend | Streamlit's small size |
| 12 | 400 | Check ID, chart labels | CSS |

Spacing 4, 8, 12, 16, 24, 32, 48; side padding 32; content at most 1200 wide; rows 40 high. Radii 4 and 8. No
shadow, gradient or glow. System font stack.

| Role | Key | Light | vs page | Dark | vs page |
|---|---|---|---|---|---|
| Page | `backgroundColor` | `#FFFFFF` | | `#0E1217` | |
| Inputs, open row | `secondaryBackgroundColor` | `#F3F5F8` | | `#181E26` | |
| Text, failed mark | `textColor` | `#121821` | 17.8 | `#E4E8EE` | 15.3 |
| Accent | `primaryColor` | `#1D5AA6` | 6.9; white on it 6.9 | `#3D74C0` | 4.0; white on it 4.7 |
| Links | `linkColor` | `#1D5AA6` | 6.9 | `#8DB2E8` | 8.7 |
| Muted text, 68% text | `grayTextColor`, CSS | `#5E6268` | 6.1 | `#A0A4A9` | 7.5 |
| Hairline, 20% text | CSS | | 1.4 | | 1.5 |

The dark accent is for fills and icons (3:1 suffices): Streamlit writes white on primary buttons, and no blue passes
4.5:1 against both white and a dark page. So the selected tab's text takes the text colour and links take `linkColor`.
Warnings and errors keep Streamlit's semantic colours.

| State | Bar mark, 20 px | Row icon in the label |
|---|---|---|
| Passed | Accent square, check | `:primary[:material/check_box:]` |
| Failed | Text-colour square, cross | `:material/disabled_by_default:` |
| Not assessed | Dashed muted outline | `:gray[:material/check_box_outline_blank:]` |
| Does not apply | Hairline outline, muted dash | `:gray[:material/indeterminate_check_box:]` |

Shape and fill differ, so colour is never alone. Each bar has `role="img"` and an `aria-label` ("Financial health: 3
passed of 6 assessed"); each mark a `title`. Streamlit's icons carry their own `aria-label`.

```toml
[client]
toolbarMode = "viewer"

[theme]                       # light, the default; test_theme.py reads these
base = "light"
primaryColor = "#1D5AA6"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F3F5F8"
textColor = "#121821"
linkColor = "#1D5AA6"
grayTextColor = "#5E6268"
font = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
baseFontSize = 16
baseRadius = "8px"
headingFontSizes = ["28px", "18px", "16px"]
headingFontWeights = [600, 600, 600]
metricValueFontSize = "24px"
metricValueFontWeight = 600
paddingTop = "16px"

[theme.dark]                  # inherits sizes and font
primaryColor = "#3D74C0"
backgroundColor = "#0E1217"
secondaryBackgroundColor = "#181E26"
textColor = "#E4E8EE"
linkColor = "#8DB2E8"
grayTextColor = "#A0A4A9"
```

The CSS block replaces `_style()` in `ui/scorecard.py`. It reads colours from the theme, so the no-colour-in-code test
holds; Streamlit sets `color-scheme` on the app root, so `light-dark()` follows the active theme:

```python
def _style() -> str:
    o = st.get_option
    pair = lambda k: f"light-dark({o('theme.' + k)}, {o('theme.dark.' + k) or o('theme.' + k)})"
    return f"""<style>
.stApp {{--fs-accent:{pair('primaryColor')}; --fs-page:{pair('backgroundColor')}; --fs-text:{pair('textColor')};
  --fs-muted:color-mix(in srgb, currentColor 68%, transparent); --fs-line:color-mix(in srgb, currentColor 20%, transparent);
  font-variant-numeric:tabular-nums}}
[data-testid="stMainBlockContainer"] {{max-width:1200px; padding-left:32px; padding-right:32px}}
[data-testid="stExpander"] details {{border:0; border-bottom:1px solid var(--fs-line); border-radius:0}}
[data-testid="stExpander"] summary span[role="img"] {{font-size:20px; vertical-align:-4px}}
[data-testid="stTab"][aria-selected="true"], [data-testid="stTab"][aria-selected="true"] p {{color:var(--fs-text)}}
.fs-muted {{color:var(--fs-muted)}}  .fs-ticker {{font-size:16px; font-weight:400; color:var(--fs-muted); margin-left:8px}}
.fs-row {{display:flex; align-items:center; gap:16px; height:40px; border-bottom:1px solid var(--fs-line)}}
.fs-bar {{display:inline-flex; gap:4px}}
.fs-mk {{width:20px; height:20px; border-radius:4px; box-sizing:border-box; display:inline-grid; place-items:center}}
.fs-mk svg {{width:12px; height:12px; fill:none; stroke:var(--fs-page); stroke-width:2.5; stroke-linecap:round}}
.fs-pass {{background:var(--fs-accent)}}  .fs-fail {{background:currentColor}}
.fs-wait {{border:1.5px dashed var(--fs-muted)}}  .fs-none {{border:1px solid var(--fs-line)}}  .fs-none svg {{stroke:var(--fs-muted)}}
.stMarkdown table.fs-kv {{width:100%; border-collapse:collapse}}
.stMarkdown table.fs-kv td {{padding:8px 0; border:0; border-bottom:1px solid var(--fs-line)}}
.stMarkdown table.fs-kv td:last-child {{text-align:right}}
</style>"""
```

Glyphs are two-path inline SVGs, as in the mockup. Checked on Streamlit 1.67.0 in a scratch app: the theme switch,
`light-dark()` in both modes, the icons, sizes, expander and tab rules. The default theme follows the viewer's system
setting and the browser remembers a choice; for the demo, pick Light in the menu once.

## 5. On-screen text

Write like a careful person: short sentences, plain words, the subject first; no filler ("it is important to note"), no
hype, no exclamation marks or emoji. For a finance page:

1. **Information, not advice.** Never buy, sell, undervalued, overvalued, cheap, expensive, fair value ("the
   estimate"), safe, risky, strong, weak, should. Add them to E's texts test.
2. **Unit and period on every figure**, from `ui/format.py`.
3. **The limit and the side**: "above the 40% limit".
4. **Relative years**: "four years earlier", never FY0.
5. **One name per thing** (avoid-ai-writing): net income throughout; liabilities for all owed, debt for borrowings.
6. **No false agency or absolute claims** (stop-slop): "the annual report lists", not "the data shows".
7. **No internal codes**: check IDs only at the end of a detail; tags and SIC code on Sources; "derived" is "Calculated".
8. **One label per state** (issue #32 point 5): Passed, Failed, Not assessed (reason, when), Does not apply (reason).
9. **Errors give the problem, then the fix** (impeccable; SPEC §3); raw message under "Technical details".

Row, before: `✓ Passed · P3 Profit growth is speeding up`. After: icon, **Profit growth is speeding up.** Net income
grew 23.3% in the latest year, faster than its average of 7.6% a year over four years.

Detail, before: "How it is calculated: Latest annual net income growth > compound annual growth over four intervals:
(FY0/FY-4)^(1/4) - 1", rows named `net_income`. After, as numbered steps:

1. Latest year: USD 13,107 m ÷ USD 10,631 m − 1 = 23.3%
2. Average over four years: (USD 13,107 m ÷ USD 9,771 m) to the power ¼, minus 1 = 7.6%

Names settled with E on 25 November (#32, #55): "Short-term liabilities covered" (H1, H2 likewise), "Debt falling
against equity" (H4), "No large dividend cut" (D3). SPEC §7 uses the names shown on screen.

## 6. States

| State | What shows |
|---|---|
| Start | Under the inputs: `st.title("Filing Scorecard")` and one sentence on what to type |
| Loading | `st.spinner("Reading the saved annual reports…")`; live: "Fetching the annual reports from the SEC…" |
| Valuation in v0.1 | Six dashed marks, "Not part of this version"; the tab says what the checks will compare |
| Not assessed | Empty-box icon; "Not assessed yet. It needs the industry average, which comes in the next version." |
| Does not apply (Amazon) | D1 failed, five dash marks, "No dividend paid", muted "0 passed of 1 assessed" |
| Error, invalid price | `st.error`: the problem, then the fix; raw message in a "Technical details" expander |
| Not fully checked | `st.warning`: "**Not fully checked.** This company's figures were read automatically and not compared by hand with its annual report." |
| Old report | `st.warning`: "The latest annual report is older than 15 months (filed …). Newer figures may exist." |

Exact texts are in the mockup's States section.

## 7. Implementation list (about one working day)

Per item (karpathy-guidelines): change only the function named; no new module and one new helper (`_table()` for the
two figure tables); pytest green after each item; done when its check passes. Review the pull request on two separate
axes (mattpocock code-review): SPEC §3, then AGENTS.md and code standards.

| # | Change; done when | Gain | Effort | File | Needs |
|---|---|---|---|---|---|
| 1 | Themes, sizes, toolbar; menu shows Light and Dark, a new test checks `[theme.dark]` | High | S | `.streamlit/config.toml`, `test_theme.py` | |
| 2 | CSS block; right accent in both themes | High | S | `ui/scorecard.py` `_style` | |
| 3 | Inputs in one row; title and sentence only on the start screen | High | S | `main.py` | |
| 4 | Header: ticker, meta without SIC code, typed price, two warnings | High | S | `render_header` | warning texts (E, S11) |
| 5 | Area rows, four marks, legend, failed list; AppTest finds "3 passed of 6 assessed" | High | M | `render_score_chart`, `_block`, `_label` | "not assessed" count in `src/scores.py`, test first |
| 6 | Tabs per area, Sources last | High | S | `main.py`, `render_checks` | |
| 7 | Check rows; until E's sentences: "Passed. USD 31,044 m against USD 21,281 m." | High | S | `render_check` | pass and fail sentences (E) |
| 8 | Check detail: rule, working, figures, filing | Medium | S | `render_check`, `_table` | plain figure names (E) |
| 9 | Area score line, sentence, key figures | Medium | M | `render_checks` | area templates (E) |
| 10 | Sources: plain headers, link column | Medium | S | `ui/sources.py` | |
| 11 | Footer, valuation empty state | Low | S | `ui/scorecard.py` | |
| 12 | Tests asserting old labels updated, each with a written reason the student agrees to; look at 1366×768, 1280×720, 125%, both themes | | S | `tests/app/` | |

S is under an hour, M one to two. Later: the two charts, one Company field accepting a typed ticker
(`accept_new_options=True`), strengths and points to watch in place of the failed list, the valuation section,
wording per error class (S11), definitions as `help=` tooltips, a sticky tab bar.

## 8. Decisions for the group

Items 1 to 5 are written into SPEC 2.4.2 §3 and `docs/product.md` by the pull request that adds this folder; 6 and 7
stay open.

1. §3 "calm and light" (product.md too): "calm; a light and a dark theme with the same structure, both defined once in
   `app/.streamlit/config.toml`; the app follows the viewer's system setting and the viewer switches in the app menu".
2. §3 item 3: not applicable as "an empty slot with a dash, 'does not apply'"; label "4 passed of 5 assessed, 1 not
   assessed"; "not assessed" on screen instead of "insufficient data".
3. §3 item 4: until tier 3, the failed checks sit next to the score chart.
4. §3 item 5: a collapsed check shows its mark, name and one sentence with figures.
5. §3 colours: warnings and errors keep Streamlit's semantic colours; muted text and hairlines are mixes of the text
   colour.
6. product.md "tables, not charts", if the group accepts the charts.
7. Open: Amazon's D1 shows a cross (SPEC); issue #32 point 6 asks for a neutral bar.

Audit of the mockup (MengTo method; impeccable's ten dimensions and craft floor; ban lists of Laith0003/ux-skill and
vibecoded-design-tells). Removed: the product banner; text in every block; boxed expanders; Unicode glyph marks; the
SEC code in the header; two large ratios that repeated the sentence and the rows (three times on one screen); a heading
over the area rows. Not added: eyebrows, section numbers, side stripes, shadows, gradients, red and green, a total
score (it would read as a rating). Fixed: misaligned hairlines between the summary columns; the legend below the 125%
fold.

Sources, all public GitHub repositories. Design: ehmo/platform-design-skills (web: 16 px body, 4.5:1 and 3:1 contrast,
never colour alone, tabular figures), arjitj2/swiftui-design-principles (type by weight), MengTo/Skills (removal
test), pbakaus/impeccable (ten dimensions, craft floor), nextlevelbuilder/ui-ux-pro-max-skill (banking: Swiss
minimalism, accessible, navy; not its gold), Laith0003/ux-skill and JCarterJohnson/vibecoded-design-tells (ban
lists). Writing (§5): blader/humanizer, conorbronsdon/avoid-ai-writing, hardikpandya/stop-slop, sho-das/clear-english.
Working (§7): multica-ai/andrej-karpathy-skills, mattpocock/skills. vabole/apple-skills skipped as iOS-only.
