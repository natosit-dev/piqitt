
import streamlit as st
import pandas as pd
import json, io, zipfile
from pathlib import Path

from scripts.piqi_eval import PIQIEvaluator, load_loinc_codes_from_csv, load_cpt_codes_from_csv, load_plausibility_yaml
from scripts.fhir_convert_backend import split_messages, convert_message_to_bundle, detect_message_type

st.set_page_config(page_title="HL7 v2 → FHIR Converter", layout="wide")
st.title("HL7 v2 → FHIR Converter")
st.caption("Upload HL7 v2 files (ADT / ORU / DFT). We'll split on MSH and convert each message to a FHIR Bundle.")

with st.sidebar:
    st.header("Export Options")
    as_ndjson = st.checkbox("Export as NDJSON", value=False)
    pretty_json = st.checkbox("Pretty-print JSON (ZIP only)", value=True)

    st.header("PIQI")
    do_piqi = st.checkbox("Run PIQI evaluation", value=True)
    sam_lib_path = st.text_input("SAM Library YAML", "piqi_sam_library.yaml")
    clinical_profile_path = st.text_input("Clinical Profile YAML", "profiles/profile_clinical_minimal.yaml")
    claims_profile_path = st.text_input("Claims Profile YAML", "profiles/profile_claims_minimal.yaml")
    # in fhir_convert_app.py (sidebar)
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
    st.dataframe(pd.DataFrame(summary), width='stretch')
    st.subheader("Download")
    if as_ndjson:
        # One NDJSON per input file, packaged into a ZIP
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
                "messageId": res["messageId"],
                #"sendingFacility": res["sendingFacility"],
                "profile": prof,
                "piqiIndex": res["piqiIndex"],
                "den": res["denominator"],
                "num": res["numerator"],
                #"criticalFails": res["criticalFailureCount"],
                "status": res["status"],
                #"code": res["code"],
                #"display": res["display"],
                #"values": res["values"],
                #"valuePreview": res["valuePreview"],
            })
        piqi_results_by_file[fname] = file_results

if piqi_rows:
    st.subheader("PIQI Scorecard (per message)")
    st.dataframe(pd.DataFrame(piqi_rows), width='stretch')

    # Optional: download verbose PIQI results JSON
    if st.button("Download PIQI Results (JSON)"):
        import io, zipfile, json
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for fname, rows in piqi_results_by_file.items():
                zf.writestr(Path(fname).with_suffix(".piqi.json").name, json.dumps(rows, indent=2).encode("utf-8"))
        st.download_button("Download PIQI ZIP", data=buf.getvalue(), file_name="piqi_results.zip")
st.markdown("---")
st.write("Ready to extend to additional standard IG or custom mappings")
