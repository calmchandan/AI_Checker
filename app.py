"""
app.py
Streamlit dashboard for the Academic Writing Analyzer & Natural Writing
Optimizer. Run with:  streamlit run app.py
"""
import subprocess, sys 
subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
import streamlit as st
import pandas as pd
from analyzer import run_analysis
from file_io import load_text_from_upload, export_json, export_txt, export_csv
from revision import mechanical_clean_pass

st.set_page_config(page_title="Academic Writing Analyzer", page_icon="📝", layout="wide")

st.title("📝 Academic Writing Analyzer & Natural Writing Optimizer")
st.caption(
    "Evaluates sentence structure, vocabulary diversity, repetition, readability, "
    "specificity, passive voice, and paragraph structure — with transparent scoring "
    "and revision suggestions."
)
st.info(
    "**Scope:** this tool measures writing-quality characteristics only. It does **not** "
    "determine or estimate whether text was written by AI, and it is not designed to "
    "help evade Turnitin, GPT detectors, or other academic-integrity systems.",
    icon="ℹ️",
)

# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

col_in1, col_in2 = st.columns([2, 1])
with col_in1:
    uploaded = st.file_uploader("Upload a file (.txt, .md, .docx, .pdf)", type=["txt", "md", "docx", "pdf"])
with col_in2:
    st.write("")
    st.write("")
    use_paste = st.toggle("Or paste text instead", value=uploaded is None)

text = ""
filename = ""

if use_paste or uploaded is None:
    text = st.text_area("Paste text to analyze", height=220, placeholder="Paste your draft here...")
    filename = "pasted_text"
elif uploaded is not None:
    try:
        text = load_text_from_upload(uploaded)
        filename = uploaded.name
        with st.expander("Preview extracted text"):
            st.text(text[:2000] + ("..." if len(text) > 2000 else ""))
    except Exception as e:
        st.error(f"Could not read file: {e}")

run = st.button("Analyze", type="primary", disabled=not text.strip())

if run and text.strip():
    with st.spinner("Analyzing..."):
        report = run_analysis(text, filename=filename)
    st.session_state["report"] = report
    st.session_state["source_text"] = text

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

if "report" in st.session_state:
    report = st.session_state["report"]
    m = report["meta"]

    st.divider()
    top1, top2, top3, top4 = st.columns(4)
    top1.metric("Overall Score", f"{report['overall']['overall_score']} / 100")
    top2.metric("Words", m["word_count"])
    top3.metric("Sentences", m["sentence_count"])
    top4.metric("Paragraphs", m["paragraph_count"])
    st.caption(f"**{report['overall']['interpretation']}**")

    tabs = st.tabs([
        "Overview", "Sentences", "Vocabulary", "Repetition",
        "Readability", "Specificity", "Style (Passive/Filler)",
        "Paragraphs", "AI Pattern Indicators", "Suggestions", "Before/After", "Export",
    ])

    with tabs[0]:
        st.subheader("Sub-scores")
        sub_df = pd.DataFrame(
            [{"Component": k.replace("_", " ").title(), "Score": v}
             for k, v in report["subscores"].items()]
        )
        st.bar_chart(sub_df.set_index("Component"))
        st.dataframe(sub_df, use_container_width=True, hide_index=True)

    with tabs[1]:
        s = report["sentence_analysis"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Mean length (words)", s["mean_length"])
        c2.metric("Length CV", s["cv"])
        c3.metric("Complex sentences", f"{s['complex_sentence_pct']}%")
        st.write("Sentence length distribution:")
        st.bar_chart(pd.Series(s["length_distribution"], name="words"))
        if s["flagged_sentences"]:
            st.write("Flagged sentences:")
            st.dataframe(pd.DataFrame(s["flagged_sentences"]), use_container_width=True, hide_index=True)

    with tabs[2]:
        v = report["vocabulary"]
        c1, c2, c3 = st.columns(3)
        c1.metric("TTR", v["ttr"])
        c2.metric("MTLD", v["mtld"])
        c3.metric("HD-D", v["hdd"])
        st.caption(f"Recommended metric for this length: **{v['recommended_metric']}**")
        st.write("Most frequent words:")
        st.dataframe(pd.DataFrame(v["top_words"], columns=["word", "count"]), use_container_width=True, hide_index=True)

    with tabs[3]:
        r = report["repetition"]
        c1, c2 = st.columns(2)
        c1.metric("Repeated 3-grams", f"{r['repeated_trigram_pct']}%")
        c2.metric("Repeated 4-grams", f"{r['repeated_fourgram_pct']}%")
        if r["top_repeated_trigrams"]:
            st.write("Top repeated 3-grams:")
            st.dataframe(pd.DataFrame(r["top_repeated_trigrams"]), use_container_width=True, hide_index=True)
        if r["overused_words"]:
            st.write("Overused content words:")
            st.dataframe(pd.DataFrame(r["overused_words"]), use_container_width=True, hide_index=True)

    with tabs[4]:
        rd = report["readability"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Flesch Reading Ease", rd["flesch_reading_ease"])
        c2.metric("Flesch-Kincaid Grade", rd["flesch_kincaid_grade"])
        c3.metric("Gunning Fog", rd["gunning_fog"])
        c4.metric("SMOG Index", rd["smog_index"])
        st.write(rd["interpretation"])

    with tabs[5]:
        sp = report["specificity"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Named entities", sp["entity_count"])
        c2.metric("Numbers/figures", sp["number_count"])
        c3.metric("Specificity score", sp["specificity_score"])
        if sp["unique_entities"]:
            st.write("Entities found:", ", ".join(sp["unique_entities"][:30]))
        if sp["vague_quantifier_hits"]:
            st.write("Vague quantifiers (unsupported by nearby numbers/citations):")
            st.dataframe(pd.DataFrame(sp["vague_quantifier_hits"]), use_container_width=True, hide_index=True)

    with tabs[6]:
        st_ = report["style"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Passive voice", f"{st_['passive_voice_pct']}%")
        c2.metric("Transition density", f"{st_['transition_density_pct']}%")
        c3.metric("Filler density", f"{st_['filler_density_pct']}%")
        if st_["passive_sentence_examples"]:
            st.write("Passive-voice examples:")
            for ex in st_["passive_sentence_examples"]:
                st.markdown(f"- {ex}")
        if st_["filler_phrase_hits"]:
            st.write("Filler phrases found:")
            st.dataframe(pd.DataFrame(st_["filler_phrase_hits"], columns=["phrase", "count"]), use_container_width=True, hide_index=True)

    with tabs[7]:
        pg = report["paragraphs"]
        st.metric("Unsupported paragraphs (>60 words, no evidence found)", pg["unsupported_paragraph_count"])
        if pg["flagged_paragraphs"]:
            st.dataframe(pd.DataFrame(pg["flagged_paragraphs"]), use_container_width=True, hide_index=True)

    with tabs[8]:
        ai = report["ai_pattern_indicators"]
        st.warning(ai["caveat"], icon="⚠️")
        c1, c2 = st.columns(2)
        c1.metric("Composite pattern score", f"{ai['composite_pattern_score']} / 100")
        c2.metric("Confidence", ai["confidence_note"].split("—")[0].strip())
        st.caption(ai["confidence_note"])
        st.write("Component breakdown:")
        comp_df = pd.DataFrame(
            [{"Component": k.replace("_", " ").title(), "Score": v} for k, v in ai["components"].items()]
        )
        st.bar_chart(comp_df.set_index("Component"))
        st.write("Raw metrics (these are what actually drive the score above):")
        rm = ai["raw_metrics"]
        st.markdown(f"- **Burstiness:** {rm['burstiness']} — {rm['burstiness_note']}")
        st.markdown(f"- **Word predictability (Zipf):** {rm['word_predictability_zipf']} — {rm['word_predictability_note']}")
        st.markdown(f"- **Generic phrase density:** {rm['generic_phrase_density_pct']}%")
        st.markdown(f"- **Paragraph uniformity (CV):** {rm['paragraph_uniformity_cv']} — {rm['paragraph_uniformity_note']}")
        if ai["generic_phrase_hits"]:
            st.write("Generic/hedge phrases found:")
            st.dataframe(pd.DataFrame(ai["generic_phrase_hits"]), use_container_width=True, hide_index=True)

    with tabs[9]:
        if report["suggestions"]:
            for s in report["suggestions"]:
                with st.container(border=True):
                    st.markdown(f"**{s['area']}** — {s['issue']}")
                    st.markdown(f"→ {s['suggestion']}")
        else:
            st.success("No major issues flagged against the configured thresholds.")

    with tabs[10]:
        st.caption(
            "Mechanical clean pass: removes only exact filler-phrase matches. "
            "It never rewrites sentences or paraphrases — facts, numbers, and "
            "citations are guaranteed untouched. Use the Suggestions tab for "
            "everything that needs a human judgment call."
        )
        cleaned, removed = mechanical_clean_pass(st.session_state["source_text"])
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Before**")
            st.text_area("before", st.session_state["source_text"], height=300, label_visibility="collapsed")
        with c2:
            st.write("**After (filler removed)**")
            st.text_area("after", cleaned, height=300, label_visibility="collapsed")
        if removed:
            st.caption(f"Removed {len(removed)} filler phrase instance(s): " + ", ".join(sorted(set(removed))))

    with tabs[11]:
        st.write("Export the full report:")
        e1, e2, e3 = st.columns(3)
        e1.download_button("Download JSON", export_json(report), file_name="writing_report.json", mime="application/json")
        e2.download_button("Download TXT", export_txt(report), file_name="writing_report.txt", mime="text/plain")
        e3.download_button("Download CSV", export_csv(report), file_name="writing_report.csv", mime="text/csv")
