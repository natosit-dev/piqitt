import io
import json
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st

from scripts.fhir_convert_backend import convert_message_to_bundle, split_messages
from scripts.piqi_eval import (
    PIQIEvaluator,
    load_cpt_codes_from_csv,
    load_loinc_codes_from_csv,
    load_plausibility_yaml,
)
from scripts.run_repo import RunRepository
from scripts.wap_runner import EvaluationConfig, run_piqitt

st.set_page_config(page_title="HL7 v2 → FHIR Converter + PIQI Scorecard", layout="wide")
st.title("HL7 v2 → FHIR Converter + PIQI Scorecard")
st.caption(
    "Interactive uploads for small samples, or point PIQITT at a backend file/folder for large runs."
)

with st.sidebar:
    st.header("Input")
    input_mode = st.radio("Input mode", ["Upload files", "Backend path"], index=0)

    st.header("Export Options")
    as_ndjson = st.checkbox("Export as NDJSON", value=False)
    pretty_json = st.checkbox("Pretty-print JSON (ZIP only)", value=True)

    st.header("PIQI")
    do_piqi = st.checkbox("Run PIQI evaluation", value=True)
    sam_lib_path = st.text_input("SAM Library YAML", "piqi_sam_library.yaml")
    clinical_profile_path = st.text_input(
        "Clinical Profile YAML", "profiles/profile_clinical_minimal.yaml"
    )
    claims_profile_path = st.text_input(
        "Claims Profile YAML", "profiles/profile_claims_minimal.yaml"
    )
    loinc_csv = st.text_input("LOINC file (CSV/TSV)", value="ref/loinc.csv")
    cpt_csv = st.text_input("CPT file (CSV)", value="ref/cpt.csv")
    plaus_yaml = st.text_input("Plausibility YAML", value="ref/plausibility.yaml")


def build_evaluator() -> PIQIEvaluator:
    loinc_codes = load_loinc_codes_from_csv(loinc_csv) if loinc_csv else set()
    cpt_codes = load_cpt_codes_from_csv(cpt_csv) if cpt_csv else set()
    plaus_cfg = load_plausibility_yaml(plaus_yaml)
    return PIQIEvaluator(
        sam_library_path=sam_lib_path,
        profile_paths=[clinical_profile_path, claims_profile_path],
        loinc_codes=loinc_codes,
        cpt_codes=cpt_codes,
        plausibility_cfg=plaus_cfg,
    )


def choose_profile(bundle):
    rtypes = {
        entry["resource"]["resourceType"]
        for entry in bundle.get("entry", [])
        if entry.get("resource")
    }
    return "Claims-Minimal" if "Claim" in rtypes else "Clinical-Minimal"


def agg_mean(frame: pd.DataFrame) -> dict:
    return {
        "count": ("piqiIndex", "count"),
        "mean_piqi": ("piqiIndex", "mean"),
        "mean_critical_fails": ("criticalFails", "mean"),
    }


def render_scorecard(piqi_rows, piqi_results_by_file):
    if not piqi_rows:
        return

    st.subheader("PIQI Scorecard — Per Message")
    df = pd.DataFrame(piqi_rows)
    st.dataframe(df, use_container_width=True)

    st.subheader("PIQI Scorecard — Summary")
    by_profile = df.groupby("profile").agg(**agg_mean(df)).reset_index()
    by_profile["mean_piqi"] = by_profile["mean_piqi"].round(2)
    by_profile["mean_critical_fails"] = by_profile["mean_critical_fails"].round(2)
    st.markdown("**By Profile**")
    st.dataframe(by_profile, use_container_width=True)

    by_file = df.groupby("file").agg(**agg_mean(df)).reset_index()
    by_file["mean_piqi"] = by_file["mean_piqi"].round(2)
    by_file["mean_critical_fails"] = by_file["mean_critical_fails"].round(2)
    st.markdown("**By File**")
    st.dataframe(by_file, use_container_width=True)

    by_fac = None
    if "sendingFacility" in df.columns and df["sendingFacility"].notna().any():
        by_fac = df.groupby("sendingFacility").agg(**agg_mean(df)).reset_index()
        by_fac["mean_piqi"] = by_fac["mean_piqi"].round(2)
        by_fac["mean_critical_fails"] = by_fac["mean_critical_fails"].round(2)
        st.markdown("**By Sending Facility**")
        st.dataframe(by_fac, use_container_width=True)

    if st.button("Download PIQI Results (JSON)"):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for fname, rows in piqi_results_by_file.items():
                zf.writestr(
                    Path(fname).with_suffix(".piqi.json").name,
                    json.dumps(rows, indent=2).encode("utf-8"),
                )
        st.download_button(
            "Download PIQI ZIP", data=buf.getvalue(), file_name="piqi_results.zip"
        )

    with st.expander("Charts (quick look)"):
        st.bar_chart(by_profile.set_index("profile")["mean_piqi"])
        st.bar_chart(by_file.set_index("file")["mean_piqi"])

    st.markdown("**Scorecard Exports**")
    tables = {"by_profile": by_profile, "by_file": by_file}
    if by_fac is not None:
        tables["by_sendingFacility"] = by_fac
    csv_buf = io.StringIO()
    pd.concat(tables).to_csv(csv_buf)
    st.download_button(
        "Download Scorecard (CSV)",
        data=csv_buf.getvalue().encode("utf-8"),
        file_name="piqi_scorecard.csv",
    )

    md_lines = ["# PIQI Summary", "", f"Total messages: **{len(df)}**", ""]

    def mk_md(tbl, title):
        if tbl.empty:
            return
        md_lines.extend(
            [
                f"## {title}",
                "",
                f"| {tbl.columns[0]} | Count | Mean PIQI | Mean Critical Fails |",
                "|---|---:|---:|---:|",
            ]
        )
        for _, row in tbl.iterrows():
            md_lines.append(
                f"| {row.iloc[0]} | {int(row['count'])} | "
                f"{row['mean_piqi']:.2f} | {row['mean_critical_fails']:.2f} |"
            )
        md_lines.append("")

    mk_md(by_profile, "By Profile")
    mk_md(by_file, "By File")
    if by_fac is not None:
        mk_md(by_fac, "By Sending Facility")
    st.download_button(
        "Download Scorecard (Markdown)",
        data="\n".join(md_lines).encode("utf-8"),
        file_name="piqi_summary.md",
    )

    st.subheader("Drill-down (Per File)")
    for fname, rows in piqi_results_by_file.items():
        with st.expander(f"{fname} — {len(rows)} messages"):
            profile_lookup = dict(zip(df["messageId"], df["profile"]))
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "messageId": row.get("messageId"),
                            "profile": profile_lookup.get(row.get("messageId")),
                            "piqiIndex": row.get("piqiIndex"),
                            "criticalFails": row.get("criticalFailureCount"),
                            "sendingFacility": row.get("sendingFacility"),
                        }
                        for row in rows
                    ]
                ),
                use_container_width=True,
            )
            if st.checkbox(f"Show raw JSON for {fname}", key=f"rawjson-{fname}"):
                st.code(json.dumps(rows, indent=2))


def render_upload_mode():
    piqi_rows = []
    piqi_results_by_file = {}
    summary = []
    bundles_by_file = {}

    uploaded_files = st.file_uploader(
        "Drop .hl7 or .txt files", type=["hl7", "txt"], accept_multiple_files=True
    )
    if not uploaded_files:
        return

    for uploaded in uploaded_files:
        raw = uploaded.read().decode("utf-8", errors="ignore")
        messages = split_messages(raw)
        file_bundles = []
        for index, message in enumerate(messages, start=1):
            bundle, message_type = convert_message_to_bundle(message)
            file_bundles.append(bundle)
            patient_id = next(
                (
                    entry["resource"]["id"]
                    for entry in bundle.get("entry", [])
                    if entry.get("resource", {}).get("resourceType") == "Patient"
                ),
                None,
            )
            summary.append(
                {
                    "file": uploaded.name,
                    "msg_idx": index,
                    "type": message_type,
                    "patient": patient_id,
                    "resource_types": ", ".join(
                        sorted(
                            {
                                entry["resource"]["resourceType"]
                                for entry in bundle.get("entry", [])
                                if entry.get("resource")
                            }
                        )
                    ),
                }
            )
        bundles_by_file[uploaded.name] = file_bundles

    st.subheader("Parsed Messages")
    st.dataframe(pd.DataFrame(summary), use_container_width=True)

    st.subheader("Bundle Downloads")
    if as_ndjson:
        if st.button("Build NDJSON ZIP"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for fname, bundles in bundles_by_file.items():
                    lines = [json.dumps(bundle) for bundle in bundles]
                    zf.writestr(
                        Path(fname).with_suffix(".ndjson").name,
                        ("\n".join(lines)).encode("utf-8"),
                    )
            st.download_button(
                "Download NDJSON ZIP",
                data=buf.getvalue(),
                file_name="fhir_bundles_ndjson.zip",
            )
    else:
        if st.button("Build Bundles ZIP"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for fname, bundles in bundles_by_file.items():
                    base = Path(fname).stem
                    for index, bundle in enumerate(bundles, start=1):
                        data = json.dumps(bundle, indent=2) if pretty_json else json.dumps(bundle)
                        zf.writestr(
                            f"{base}/bundle_{index:03d}.json", data.encode("utf-8")
                        )
            st.download_button(
                "Download Bundles ZIP",
                data=buf.getvalue(),
                file_name="fhir_bundles.zip",
            )

    if not do_piqi:
        return

    evaluator = build_evaluator()
    for fname, bundles in bundles_by_file.items():
        file_results = []
        for bundle in bundles:
            profile = choose_profile(bundle)
            result = evaluator.evaluate_bundle(bundle, profile_name=profile)
            file_results.append(result)
            piqi_rows.append(
                {
                    "file": fname,
                    "messageId": result.get("messageId"),
                    "sendingFacility": result.get("sendingFacility"),
                    "profile": profile,
                    "piqiIndex": result.get("piqiIndex"),
                    "piqiWeightedIndex": result.get("piqiWeightedIndex"),
                    "denominator": result.get("denominator"),
                    "numerator": result.get("numerator"),
                    "criticalFails": result.get("criticalFailureCount"),
                }
            )
        piqi_results_by_file[fname] = file_results

    render_scorecard(piqi_rows, piqi_results_by_file)


def render_backend_mode():
    st.subheader("Backend File / Folder Run")
    st.caption(
        "The path is resolved on the machine running PIQITT. Large files stay on the backend; "
        "Streamlit only starts the run and displays status."
    )

    backend_path = st.text_input("Input file or folder path", key="wap_input_path")
    backend_profile_label = st.selectbox(
        "Profile",
        ["Auto (Claims for DFT, Clinical otherwise)", "Clinical-Minimal", "Claims-Minimal"],
    )
    backend_profile = "AUTO" if backend_profile_label.startswith("Auto") else backend_profile_label

    with st.expander("Run storage"):
        db_path = st.text_input("DuckDB run repository", "data/piqitt_runs.duckdb")
        output_root = st.text_input("Run artifact folder", "runs")

    if st.button("Start Backend Run", type="primary", disabled=not bool(backend_path.strip())):
        status_line = st.empty()
        progress_line = st.empty()
        file_line = st.empty()

        config = EvaluationConfig(
            sam_library_path=sam_lib_path,
            clinical_profile_path=clinical_profile_path,
            claims_profile_path=claims_profile_path,
            loinc_csv=loinc_csv,
            cpt_csv=cpt_csv,
            plausibility_yaml=plaus_yaml,
            profile_name=backend_profile,
        )

        def progress(event):
            kind = event.get("event")
            if kind == "run_started":
                status_line.info(
                    f"Run {event['run_id']} started — {event['file_count']} file(s) discovered"
                )
            elif kind == "file_started":
                file_line.write(
                    f"File {event['file_number']}/{event['file_count']}: **{event['file_name']}**"
                )
            elif kind == "progress":
                progress_line.write(
                    f"{event['file_message_count']:,} messages in current file · "
                    f"{event['run_message_count']:,} messages in run · "
                    f"mean PIQI {event['run_mean_piqi']:.2f}"
                )
            elif kind == "file_failed":
                file_line.error(
                    f"FAILED {event['file_name']}: {event['error_message']} — continuing"
                )
            elif kind == "file_complete":
                file_line.success(
                    f"COMPLETE {event['file_name']}: {event['message_count']:,} messages, "
                    f"PIQI {event['mean_piqi']:.2f}"
                )

        try:
            result = run_piqitt(
                backend_path.strip(),
                config=config,
                db_path=db_path,
                output_root=output_root,
                progress_callback=progress,
            )
            st.session_state["wap_last_run"] = result
            if result["status"] == "COMPLETE":
                status_line.success(
                    f"Run {result['run_id']} complete — {result['message_count']:,} messages"
                )
            else:
                status_line.warning(
                    f"Run {result['run_id']} finished with failed file(s). "
                    "Completed work was preserved."
                )
        except Exception as exc:
            st.exception(exc)

    result = st.session_state.get("wap_last_run")
    if result:
        st.markdown("### Last Backend Run")
        top = pd.DataFrame(
            [
                {
                    "run_id": result["run_id"],
                    "status": result["status"],
                    "files": result["file_count"],
                    "messages": result["message_count"],
                    "mean_piqi": result["mean_piqi"],
                    "critical_failures": result["critical_failure_count"],
                    "elapsed_seconds": result["elapsed_seconds"],
                }
            ]
        )
        st.dataframe(top, use_container_width=True)
        st.dataframe(pd.DataFrame(result["files"]), use_container_width=True)

    db_file = Path(db_path).expanduser()
    if db_file.exists():
        with st.expander("Recent Runs"):
            try:
                with RunRepository(db_file) as repo:
                    recent = repo.recent_runs(limit=25)
                if recent:
                    st.dataframe(pd.DataFrame(recent), use_container_width=True)
                else:
                    st.caption("No runs recorded yet.")
            except Exception as exc:
                st.warning(f"Could not read run history: {exc}")


if input_mode == "Upload files":
    render_upload_mode()
else:
    render_backend_mode()
