import streamlit as st
import pandas as pd
import json, io, zipfile
from pathlib import Path

from scripts.piqi_eval import PIQIEvaluator, load_loinc_codes_from_csv, load_cpt_codes_from_csv, load_plausibility_yaml
from scripts.fhir_convert_backend import split_messages, convert_message_to_bundle, detect_message_type

st.set_page_config(page_title="HL7 v2 → FHIR Converter + PIQI Scorecard", layout="wide")
st.title("HL7 v2 → FHIR Converter + PIQI Scorecard")
st.caption("Upload HL7 v2 files (ADT / ORU / DFT). We'll split on MSH, convert each message to a FHIR Bundle, and score with PIQI.")

with st.sidebar:
    st.header("Export Options")
    as_ndjson = st.checkbox("Export as NDJSON", value=False)
    pretty_json = st.checkbox("Pretty-print JSON (ZIP only)", value=True)

    st.header("PIQI")
    do_piqi = st.checkbox("Run PIQI evaluation", value=True)
    sam_lib_path = st.text_input("SAM Library YAML", "piqi_sam_library.yaml")
    clinical_profile_path = st.text_input("Clinical Profile YAML", "profiles/profile_clinical_minimal.yaml")
    claims_profile_path = st.text_input("Claims Profile YAML", "profiles/profile_claims_minimal.yaml")
    loinc_csv = st.text_input("LOINC file (CSV/TSV)", value="ref/loinc.csv")
    cpt_csv   = st.text_input("CPT file (CSV)", value="ref/cpt.csv")
    plaus_yaml = st.text_input("Plausibility YAML", value="ref/plausibility.yaml")

piqi_rows = []
piqi_results_by_file = {}

uploaded_files = st.file_uploader("Drop .hl7 or .txt files", type=["hl7","txt"], accept_multiple_files=True)

summary = []
bundles_by_file = {}

if uploaded_files:
    for uf in uploaded_files:
        raw = uf.read().decode("utf-8", errors="ignore")
        messages = split_messages(raw)
        file_bundles = []
        for i, msg in enumerate(messages, start=1):
            bundle, mtype = convert_message_to_bundle(msg)
            file_bundles.append(bundle)
            patient_id = next((e["resource"]["id"] for e in bundle["entry"] if e["resource"]["resourceType"]=="Patient"), None)
            summary.append({
                "file": uf.name,
                "msg_idx": i,
                "type": mtype,
                "patient": patient_id,
                "resource_types": ", ".join(sorted({e["resource"]["resourceType"] for e in bundle["entry"]}))
            })
        bundles_by_file[uf.name] = file_bundles

if summary:
    st.subheader("Parsed Messages")
    st.dataframe(pd.DataFrame(summary), use_container_width=True)

    st.subheader("Bundle Downloads")
    if as_ndjson:
        if st.button("Build NDJSON ZIP"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for fname, bundles in bundles_by_file.items():
                    lines = [json.dumps(b) for b in bundles]
                    zf.writestr(Path(fname).with_suffix(".ndjson").name, ("\n".join(lines)).encode("utf-8"))
            st.download_button("Download NDJSON ZIP", data=buf.getvalue(), file_name="fhir_bundles_ndjson.zip")
    else:
        if st.button("Build Bundles ZIP"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for fname, bundles in bundles_by_file.items():
                    base = Path(fname).stem
                    for idx, b in enumerate(bundles, start=1):
                        data = json.dumps(b, indent=2) if pretty_json else json.dumps(b)
                        zf.writestr(f"{base}/bundle_{idx:03d}.json", data.encode("utf-8"))
            st.download_button("Download Bundles ZIP", data=buf.getvalue(), file_name="fhir_bundles.zip")

# ---- PIQI evaluation ----
if summary and do_piqi:
    # Load value sets once
    loinc_codes = load_loinc_codes_from_csv(loinc_csv) if loinc_csv else set()
    cpt_codes = load_cpt_codes_from_csv(cpt_csv) if cpt_csv else set()
    plaus_cfg = load_plausibility_yaml(plaus_yaml)

    evaluator = PIQIEvaluator(
        sam_library_path=sam_lib_path,
        profile_paths=[clinical_profile_path, claims_profile_path],
        loinc_codes=loinc_codes,
        cpt_codes=cpt_codes,
        plausibility_cfg=plaus_cfg,
    )

    # Pick profile based on bundle contents (ORU→Clinical, DFT→Claims, else Clinical)
    def choose_profile(b):
        rtypes = {e["resource"]["resourceType"] for e in b["entry"]}
        if "Claim" in rtypes:
            return "Claims-Minimal"
        return "Clinical-Minimal"

    for fname, bundles in bundles_by_file.items():
        file_results = []
        for b in bundles:
            prof = choose_profile(b)
            res = evaluator.evaluate_bundle(b, profile_name=prof)
            file_results.append(res)
            piqi_rows.append({
                "file": fname,
                "messageId": res.get("messageId"),
                "sendingFacility": res.get("sendingFacility"),
                "profile": prof,
                "piqiIndex": res.get("piqiIndex"),
                "piqiWeightedIndex": res.get("piqiWeightedIndex"),
                "denominator": res.get("denominator"),
                "numerator": res.get("numerator"),
                "criticalFails": res.get("criticalFailureCount"),
            })
        piqi_results_by_file[fname] = file_results

if piqi_rows:
    st.subheader("PIQI Scorecard — Per Message")
    df = pd.DataFrame(piqi_rows)
    st.dataframe(df, use_container_width=True)

    # ---- Aggregations (Scorecard view) ----
    st.subheader("PIQI Scorecard — Summary")

    def _agg_mean(cols):
        return {
            "count": ("piqiIndex", "count"),
            "mean_piqi": ("piqiIndex", "mean"),
            "mean_critical_fails": ("criticalFails", "mean"),
        }

    # by Profile
    by_profile = df.groupby("profile").agg(**_agg_mean(df)).reset_index()
    by_profile["mean_piqi"] = by_profile["mean_piqi"].round(2)
    by_profile["mean_critical_fails"] = by_profile["mean_critical_fails"].round(2)
    st.markdown("**By Profile**")
    st.dataframe(by_profile, use_container_width=True)

    # by File
    by_file = df.groupby("file").agg(**_agg_mean(df)).reset_index()
    by_file["mean_piqi"] = by_file["mean_piqi"].round(2)
    by_file["mean_critical_fails"] = by_file["mean_critical_fails"].round(2)
    st.markdown("**By File**")
    st.dataframe(by_file, use_container_width=True)

    # by Sending Facility (if present)
    if "sendingFacility" in df.columns and df["sendingFacility"].notna().any():
        by_fac = df.groupby("sendingFacility").agg(**_agg_mean(df)).reset_index()
        by_fac["mean_piqi"] = by_fac["mean_piqi"].round(2)
        by_fac["mean_critical_fails"] = by_fac["mean_critical_fails"].round(2)
        st.markdown("**By Sending Facility**")
        st.dataframe(by_fac, use_container_width=True)
    if st.button("Download PIQI Results (JSON)"):
        import io, zipfile, json
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for fname, rows in piqi_results_by_file.items():
                zf.writestr(Path(fname).with_suffix(".piqi.json").name, json.dumps(rows, indent=2).encode("utf-8"))
        st.download_button("Download PIQI ZIP", data=buf.getvalue(), file_name="piqi_results.zip")

    # ---- Quick charts ----
    with st.expander("Charts (quick look)"):
        st.bar_chart(by_profile.set_index("profile")["mean_piqi"])
        st.bar_chart(by_file.set_index("file")["mean_piqi"])

    # ---- Exports (Scorecard) ----
    st.markdown("**Scorecard Exports**")

    # CSV
    csv_buf = io.StringIO()
    pd.concat(
        {
            "by_profile": by_profile,
            "by_file": by_file,
            **({"by_sendingFacility": by_fac} if "by_fac" in locals() else {})
        }
    ).to_csv(csv_buf)
    st.download_button("Download Scorecard (CSV)", data=csv_buf.getvalue().encode("utf-8"), file_name="piqi_scorecard.csv")

    # Markdown (similar to CLI tool)
    md_lines = []
    total_msgs = len(df)
    md_lines.append(f"# PIQI Summary\n")
    md_lines.append(f"Total messages: **{total_msgs}**\n")

    def _mk_md(tbl, title):
        if tbl.empty:
            return
        md_lines.append(f"## {title}\n")
        cols = ["count", "mean_piqi", "mean_critical_fails"]
        header = f"| {tbl.columns[0]} | Count | Mean PIQI | Mean Critical Fails |"
        sep = "|---|---:|---:|---:|"
        md_lines.append(header)
        md_lines.append(sep)
        for _, row in tbl.iterrows():
            md_lines.append(f"| {row.iloc[0]} | {int(row['count'])} | {row['mean_piqi']:.2f} | {row['mean_critical_fails']:.2f} |")
        md_lines.append("")

    _mk_md(by_profile, "By Profile")
    _mk_md(by_file, "By File")
    if "by_fac" in locals():
        _mk_md(by_fac, "By Sending Facility")

    md_bytes = "\n".join(md_lines).encode("utf-8")
    st.download_button("Download Scorecard (Markdown)", data=md_bytes, file_name="piqi_summary.md")

    # ---- Drill-down (per file) ----
    st.subheader("Drill-down (Per File)")
    for fname, rows in piqi_results_by_file.items():
        with st.expander(f"{fname} — {len(rows)} messages"):
            st.dataframe(pd.DataFrame([{
                "messageId": r.get("messageId"),
                "profile": next((x["profile"] for x in df[df["messageId"]==r.get("messageId")].to_dict("records")), None),
                "piqiIndex": r.get("piqiIndex"),
                "criticalFails": r.get("criticalFailureCount"),
                "sendingFacility": r.get("sendingFacility"),
            } for r in rows]), use_container_width=True)

            if st.checkbox(f"Show raw JSON for {fname}", key=f"rawjson-{fname}"):
                st.code(json.dumps(rows, indent=2))
    