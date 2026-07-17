#!/usr/bin/env python3
"""Knowledge Prism Research Exoskeleton - local operational GUI v0.3.

Run from the project root:
    python3 gui/knowledge_prism_app.py
"""
from __future__ import annotations

import json
import sys
import webbrowser
from pathlib import Path
from tkinter import BooleanVar, StringVar, Tk, Toplevel, filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from zipfile import ZipFile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gui.services import (  # noqa: E402
    concept_fit,
    draft_diagnosis,
    draft_intake,
    project_state,
    query_lens,
    report_writer,
    safety,
    scholar_brief,
    scholar_input_reports,
    scholar_input_backend,
    scholar_input_schema,
)


OUTPUT_TYPES = [
    "reading list",
    "verification queue",
    "evidence brief",
    "literature review scaffold",
    "ontology proposal",
    "teaching note",
    "research memo",
]

LAYER_OPTIONS = ["A", "B", "AB", "Peripheral", "Ambiguous"]
REPORT_FORMATS = ["markdown", "json", "csv"]


class KnowledgePrismApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Knowledge Prism Research Exoskeleton")
        self.root.geometry("1320x860")
        self.root.minsize(980, 700)

        self.write_mode = BooleanVar(value=False)
        self.report_format = StringVar(value="markdown")
        self.output_type = StringVar(value=OUTPUT_TYPES[2])
        self.layer_choice = StringVar(value="AB")
        self.current_lens: query_lens.QueryLens | None = None
        self.current_input: query_lens.ResearchInput | None = None
        self.fragments: list[draft_intake.ResearchFragment] = []
        self.organ_map = draft_intake.empty_organ_map()
        self.last_literature_plan: dict | None = None
        self.current_scholar_input: dict | None = None
        self.current_scholar_validation: list[scholar_input_schema.ValidationItem] = []
        self.current_scholar_seed_preview: dict | None = None
        self.scholar_inbox_records: list[scholar_input_schema.InboxRecord] = []
        self.scholar_persistent_records: list[dict] = []
        self.scholar_source_view = StringVar(value="Local JSON")
        self.scholar_selected_import_path: Path | None = None
        self.scholar_dry_run_report: scholar_input_backend.ImportReport | None = None
        self.scholar_review_actor = StringVar(value="")
        self.scholar_review_lens_type = StringVar(value="research_question")
        self.selected_persistent_scholar: dict | None = None
        self.scholar_status_filter = StringVar(value="All")
        self.scholar_source_filter = StringVar(value="All")
        self.scholar_organ_filter = StringVar(value="All")
        self.scholar_search_query = StringVar(value="")
        self.idea_input_type = StringVar(value=draft_intake.INPUT_TYPES[0])
        self.idea_source_note = StringVar(value=draft_intake.SOURCE_NOTES[0])
        self.idea_confidence = StringVar(value=draft_intake.CONFIDENCE_LEVELS[0])

        self._build_header()
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._build_tabs()
        self.refresh_project_state()

    def _build_header(self) -> None:
        frame = ttk.Frame(self.root, padding=(10, 10, 10, 8))
        frame.pack(fill="x")
        title = ttk.Label(frame, text="Knowledge Prism Research Exoskeleton", font=("TkDefaultFont", 18, "bold"))
        title.grid(row=0, column=0, sticky="w")
        subtitle = ttk.Label(
            frame,
            text="A governed interface for turning research questions into evidence-traceable research outputs.",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Checkbutton(
            frame,
            text="Governed write mode",
            variable=self.write_mode,
            command=self._toggle_write_mode,
        ).grid(row=0, column=1, sticky="e", padx=10)
        self.mode_label = ttk.Label(frame, text=safety.READ_ONLY_WARNING, foreground="#176b56")
        self.mode_label.grid(row=1, column=1, sticky="e", padx=10)
        frame.columnconfigure(0, weight=1)

    def _build_tabs(self) -> None:
        self.tabs: dict[str, ttk.Frame] = {}
        for name in [
            "Idea Capture",
            "Research Organ Builder",
            "Draft Diagnosis",
            "Concept & Ontology Fit",
            "Literature Search Plan",
            "Supervisor Brief",
            "Scholar Input Inbox",
            "Research Input",
            "Query Lens",
            "Retrieval Console",
            "Verification Queue",
            "Sampling Workbench",
            "Evidence Review",
            "Functional Interpretation",
            "Ontology Status",
            "Reports and Exports",
            "Project State",
        ]:
            tab = ttk.Frame(self.notebook, padding=12)
            self.tabs[name] = tab
            self.notebook.add(tab, text=name)

        self._tab_idea_capture()
        self._tab_organ_builder()
        self._tab_draft_diagnosis()
        self._tab_concept_fit()
        self._tab_literature_search_plan()
        self._tab_supervisor_brief()
        self._tab_scholar_input_inbox()
        self._tab_research_input()
        self._tab_query_lens()
        self._tab_retrieval()
        self._tab_verification_queue()
        self._tab_sampling()
        self._tab_evidence_review()
        self._tab_functional_interpretation()
        self._tab_ontology()
        self._tab_reports()
        self._tab_project_state()

    def _tab_idea_capture(self) -> None:
        tab = self.tabs["Idea Capture"]
        intro = (
            "Capture thoughts, dictated notes, fragments, partial paragraphs, or full drafts. "
            f"Every captured item is labelled {draft_intake.FRAGMENT_LABEL}; it is seed material, not evidence."
        )
        ttk.Label(tab, text="Research Rumination and Organ Builder", font=("TkDefaultFont", 14, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w"
        )
        ttk.Label(tab, text=intro).grid(row=1, column=0, columnspan=4, sticky="w", pady=(2, 10))

        ttk.Label(tab, text="Input type").grid(row=2, column=0, sticky="w")
        ttk.Combobox(tab, textvariable=self.idea_input_type, values=draft_intake.INPUT_TYPES, state="readonly").grid(
            row=3, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Label(tab, text="Source note").grid(row=2, column=1, sticky="w")
        ttk.Combobox(tab, textvariable=self.idea_source_note, values=draft_intake.SOURCE_NOTES, state="readonly").grid(
            row=3, column=1, sticky="ew", padx=(0, 8)
        )
        ttk.Label(tab, text="Confidence").grid(row=2, column=2, sticky="w")
        ttk.Combobox(tab, textvariable=self.idea_confidence, values=draft_intake.CONFIDENCE_LEVELS, state="readonly").grid(
            row=3, column=2, sticky="ew", padx=(0, 8)
        )
        ttk.Label(tab, text="Tags").grid(row=2, column=3, sticky="w")
        self.idea_tags = ttk.Entry(tab)
        self.idea_tags.grid(row=3, column=3, sticky="ew")

        self.idea_text = ScrolledText(tab, height=9, wrap="word")
        self.idea_text.grid(row=4, column=0, columnspan=4, sticky="nsew", pady=8)
        controls = ttk.Frame(tab)
        controls.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(0, 8))
        for label, command in [
            ("Import .txt/.md/.docx", self.import_fragment_file),
            ("Capture Fragment", self.capture_fragment),
            ("Classify Fragment", self.classify_selected_or_current_fragment),
            ("Send to Organ Builder", self.send_fragments_to_organ_builder),
            ("Save Rumination Log", self.save_rumination_log),
        ]:
            ttk.Button(controls, text=label, command=command).pack(side="left", padx=(0, 8))

        self.fragment_tree = self._tree(
            tab,
            ["fragment_id", "input_type", "confidence", "source_note", "label", "assigned_organs", "text"],
            row=6,
        )
        self.fragment_tree.bind("<<TreeviewSelect>>", self._show_fragment_detail)
        self.fragment_detail = ScrolledText(tab, height=6, wrap="word")
        self.fragment_detail.grid(row=8, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        self.idea_status = ttk.Label(tab, text="No scholar fragments captured in this session.")
        self.idea_status.grid(row=9, column=0, columnspan=4, sticky="w", pady=(6, 0))
        for col in range(4):
            tab.columnconfigure(col, weight=1)
        tab.rowconfigure(4, weight=1)
        tab.rowconfigure(6, weight=2)

    def _tab_organ_builder(self) -> None:
        tab = self.tabs["Research Organ Builder"]
        ttk.Label(tab, text="Research Organ Builder", font=("TkDefaultFont", 14, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            tab,
            text="Organ text is draft writing support only. It is not evidence and must not enter evidence tables.",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 8))
        self.organ_tree = self._tree(
            tab,
            ["organ", "status", "confidence", "fragment_count", "suggested_next_action"],
            row=2,
        )
        self.organ_tree.bind("<<TreeviewSelect>>", self._show_organ_detail)
        controls = ttk.Frame(tab)
        controls.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        for label, command in [
            ("Assign Fragment", self.assign_selected_fragment_to_selected_organ),
            ("Move Fragment", self.move_selected_fragment_to_selected_organ),
            ("Merge Fragments", self.merge_fragments_for_selected_organ),
            ("Draft Organ Text", self.draft_selected_organ_text),
            ("Export Organ Map", self.export_organ_map),
            ("Generate Synopsis Skeleton", self.generate_synopsis_skeleton),
        ]:
            ttk.Button(controls, text=label, command=command).pack(side="left", padx=(0, 8))
        self.organ_detail = ScrolledText(tab, height=11, wrap="word")
        self.organ_detail.grid(row=5, column=0, columnspan=2, sticky="nsew")
        self.organ_status = ttk.Label(tab, text="Organ map is empty until fragments are captured.")
        self.organ_status.grid(row=6, column=0, columnspan=2, sticky="w", pady=(6, 0))
        tab.rowconfigure(2, weight=2)
        tab.rowconfigure(5, weight=1)
        tab.columnconfigure(0, weight=1)
        self.refresh_organ_map()

    def _tab_draft_diagnosis(self) -> None:
        tab = self.tabs["Draft Diagnosis"]
        ttk.Label(tab, text="Draft Diagnosis", font=("TkDefaultFont", 14, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(
            tab,
            text="Paste generated organ text, a synopsis, term-paper draft, chapter draft, or literature review draft.",
        ).grid(row=1, column=0, sticky="w", pady=(2, 8))
        self.draft_text = ScrolledText(tab, height=16, wrap="word")
        self.draft_text.grid(row=2, column=0, sticky="nsew")
        controls = ttk.Frame(tab)
        controls.grid(row=3, column=0, sticky="ew", pady=10)
        ttk.Button(controls, text="Diagnose Draft", command=self.diagnose_draft).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Use Synopsis Skeleton", command=self.load_synopsis_into_diagnosis).pack(side="left")
        self.diagnosis_output = ScrolledText(tab, height=13, wrap="word")
        self.diagnosis_output.grid(row=4, column=0, sticky="nsew")
        tab.rowconfigure(2, weight=1)
        tab.rowconfigure(4, weight=1)
        tab.columnconfigure(0, weight=1)

    def _tab_concept_fit(self) -> None:
        tab = self.tabs["Concept & Ontology Fit"]
        ttk.Label(tab, text="Concept & Ontology Fit", font=("TkDefaultFont", 14, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            tab,
            text="Map scholar concepts against Knowledge Prism without treating design-map matches as verified ontology.",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 8))
        self.concept_text = ScrolledText(tab, height=7, wrap="word")
        self.concept_text.grid(row=2, column=0, columnspan=2, sticky="ew")
        controls = ttk.Frame(tab)
        controls.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Button(controls, text="Analyse Concept Fit", command=self.analyse_concept_fit).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Use Captured Concepts", command=self.use_captured_concepts).pack(side="left")
        self.concept_tree = self._tree(
            tab,
            ["concept", "appears_in_scholar_fragments", "fit_label", "next_step"],
            row=4,
        )
        self.concept_status = ttk.Label(
            tab,
            text="Labels include design_map_match_not_verified, sample_supported_related, queue_related, absent_from_project, needs_literature_search.",
        )
        self.concept_status.grid(row=6, column=0, columnspan=2, sticky="w", pady=(6, 0))
        tab.rowconfigure(4, weight=1)
        tab.columnconfigure(0, weight=1)

    def _tab_literature_search_plan(self) -> None:
        tab = self.tabs["Literature Search Plan"]
        ttk.Label(tab, text="Literature Search Plan", font=("TkDefaultFont", 14, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(
            tab,
            text="Convert ruminations and organs into a search strategy. Recoll is not run from this tab.",
        ).grid(row=1, column=0, sticky="w", pady=(2, 8))
        controls = ttk.Frame(tab)
        controls.grid(row=2, column=0, sticky="ew")
        ttk.Button(controls, text="Generate Search Plan", command=self.generate_literature_search_plan).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Export Search Plan", command=self.export_literature_search_plan).pack(side="left")
        self.search_plan_output = ScrolledText(tab, height=29, wrap="word")
        self.search_plan_output.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        tab.rowconfigure(3, weight=1)
        tab.columnconfigure(0, weight=1)

    def _tab_supervisor_brief(self) -> None:
        tab = self.tabs["Supervisor Brief"]
        ttk.Label(tab, text="Supervisor Brief", font=("TkDefaultFont", 14, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(tab, text=scholar_brief.BRIEF_PROVENANCE_NOTE).grid(row=1, column=0, sticky="w", pady=(2, 8))
        controls = ttk.Frame(tab)
        controls.grid(row=2, column=0, sticky="ew")
        ttk.Button(controls, text="Generate Supervisor Brief", command=self.generate_supervisor_brief).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Export Supervisor Brief", command=self.export_supervisor_brief).pack(side="left")
        self.supervisor_brief_output = ScrolledText(tab, height=31, wrap="word")
        self.supervisor_brief_output.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        tab.rowconfigure(3, weight=1)
        tab.columnconfigure(0, weight=1)

    def _tab_scholar_input_inbox(self) -> None:
        tab = self.tabs["Scholar Input Inbox"]
        ttk.Label(tab, text="Scholar Input Inbox", font=("TkDefaultFont", 14, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        ttk.Label(
            tab,
            text=(
                "SCHOLAR INPUT — NOT EVIDENCE. Approval seeds a research question or retrieval lens; "
                "it never sends an idea directly to verification_queue."
            ),
            foreground="#8a3d00",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 8))
        controls = ttk.Frame(tab)
        controls.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        for label, command in [
            ("Refresh Inbox", self.refresh_scholar_inbox),
            ("Load Selected Record", self.load_selected_scholar_record),
            ("Validate Selected", self.validate_selected_scholar_input),
            ("Export Selected Summary", self.export_selected_scholar_summary),
            ("Open Reports Folder", self.open_scholar_reports_folder),
            ("Load Scholar Input JSON", self.load_scholar_input_json),
            ("Run Backend Dry Run", self.run_scholar_import_dry_run),
            ("Open Governed Review", self.open_scholar_review_window),
            ("Preview Research Question Seed", self.preview_scholar_question_seed),
            ("Copy Supervisor Note", self.copy_scholar_supervisor_note),
        ]:
            ttk.Button(controls, text=label, command=command).pack(side="left", padx=(0, 8))
        self.scholar_commit_button = ttk.Button(
            controls, text="Commit Eligible Records", command=self.commit_scholar_import, state="disabled"
        )
        self.scholar_commit_button.pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Reset Filters", command=self.reset_scholar_inbox_filters).pack(side="left", padx=(8, 8))
        filters = ttk.Frame(tab)
        filters.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        ttk.Label(filters, text="View").pack(side="left", padx=(0, 4))
        self.scholar_source_view_combo = ttk.Combobox(
            filters, textvariable=self.scholar_source_view,
            values=["Local JSON", "Persistent Database"], state="readonly", width=20,
        )
        self.scholar_source_view_combo.pack(side="left", padx=(0, 10))
        ttk.Label(filters, text="Status").pack(side="left", padx=(0, 4))
        self.scholar_status_combo = ttk.Combobox(
            filters,
            textvariable=self.scholar_status_filter,
            values=scholar_input_schema.STATUS_FILTER_VALUES,
            state="readonly",
            width=22,
        )
        self.scholar_status_combo.pack(side="left", padx=(0, 10))
        ttk.Label(filters, text="Source").pack(side="left", padx=(0, 4))
        ttk.Combobox(
            filters,
            textvariable=self.scholar_source_filter,
            values=scholar_input_schema.SOURCE_FILTER_VALUES,
            state="readonly",
            width=17,
        ).pack(side="left", padx=(0, 10))
        ttk.Label(filters, text="Draft organ").pack(side="left", padx=(0, 4))
        ttk.Combobox(
            filters,
            textvariable=self.scholar_organ_filter,
            values=scholar_input_schema.ORGAN_FILTER_VALUES,
            state="readonly",
            width=26,
        ).pack(side="left", padx=(0, 10))
        self.scholar_inbox_count = ttk.Label(filters, text="Showing 0 of 0 local scholar-input records")
        self.scholar_inbox_count.pack(side="left", padx=(8, 0))
        for variable in [self.scholar_status_filter, self.scholar_source_filter, self.scholar_organ_filter]:
            variable.trace_add("write", lambda *_: self._render_scholar_inbox_list())
        search = ttk.Frame(tab)
        search.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        ttk.Label(search, text="Search").pack(side="left", padx=(0, 4))
        search_entry = ttk.Entry(search, textvariable=self.scholar_search_query, width=46)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(search, text="Search", command=self._render_scholar_inbox_list).pack(side="left", padx=(0, 8))
        ttk.Button(search, text="Clear Search", command=self.clear_scholar_inbox_search).pack(side="left")
        self.scholar_search_query.trace_add("write", lambda *_: self._render_scholar_inbox_list())
        disabled = ttk.Frame(tab)
        disabled.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        for label in [
            "Seed Research Question",
            "Reject and Archive",
            "Run Retrieval",
            "Send to Verification Queue",
        ]:
            ttk.Button(
                disabled,
                text=f"{label} (disabled)",
                command=self._scholar_input_disabled_factory(label),
            ).pack(side="left", padx=(0, 8))

        inbox_frame = ttk.Frame(tab)
        inbox_frame.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=(0, 8))
        self.scholar_inbox_tree = self._tree(
            inbox_frame,
            [
                "view",
                "filename",
                "scholar_id",
                "captured_ts",
                "imported_ts",
                "source",
                "draft_organ",
                "status",
                "idea",
                "tags",
                "confidence",
                "project_title",
                "course_or_context",
                "content_sha256",
                "validation_status",
            ],
            pack=True,
        )
        self.scholar_inbox_tree.config(height=5)
        self.scholar_inbox_tree.bind("<<TreeviewSelect>>", self._preview_selected_scholar_record)
        self.scholar_card = ScrolledText(tab, height=7, wrap="word")
        self.scholar_card.grid(row=7, column=0, sticky="nsew", padx=(0, 8))
        validation_frame = ttk.Frame(tab)
        validation_frame.grid(row=7, column=1, sticky="nsew", padx=(0, 8))
        self.scholar_validation_tree = self._tree(validation_frame, ["level", "field", "message"], pack=True)
        self.scholar_validation_tree.config(height=7)
        self.scholar_seed_preview = ScrolledText(tab, height=7, wrap="word")
        self.scholar_seed_preview.grid(row=7, column=2, sticky="nsew")
        self.scholar_input_status = ttk.Label(
            tab,
            text="Load a v0.2 scholar input JSON file, or use the sample fixture in outputs/gui_reports/scholar_inputs/.",
        )
        self.scholar_input_status.grid(row=8, column=0, columnspan=3, sticky="w", pady=(8, 0))
        self.scholar_import_report = ScrolledText(tab, height=4, wrap="word")
        self.scholar_import_report.grid(row=9, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        review = ttk.LabelFrame(tab, text="Governed Persistent Review", padding=8)
        review.grid(row=10, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        ttk.Label(review, text="Decision actor (required)").grid(row=0, column=0, sticky="w")
        ttk.Entry(review, textvariable=self.scholar_review_actor).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Label(review, text="Approved seed type").grid(row=0, column=1, sticky="w")
        ttk.Combobox(
            review, textvariable=self.scholar_review_lens_type,
            values=["research_question", "retrieval_lens"], state="readonly",
        ).grid(row=1, column=1, sticky="ew", padx=(0, 8))
        actions = ttk.Frame(review)
        actions.grid(row=1, column=2, sticky="ew")
        self.scholar_start_review_button = ttk.Button(actions, text="Start Review", command=self.start_scholar_review)
        self.scholar_start_review_button.pack(side="left", padx=(0, 6))
        self.scholar_approve_button = ttk.Button(actions, text="Approve to Question", command=self.approve_scholar_to_question)
        self.scholar_approve_button.pack(side="left", padx=(0, 6))
        self.scholar_reject_button = ttk.Button(actions, text="Reject and Archive", command=self.reject_scholar_input)
        self.scholar_reject_button.pack(side="left")
        ttk.Label(review, text="Final approved question/lens text (does not overwrite original idea)").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )
        ttk.Label(review, text="Rejection reason").grid(row=2, column=2, sticky="w", pady=(6, 0))
        self.scholar_final_question = ScrolledText(review, height=4, wrap="word")
        self.scholar_final_question.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=(0, 8))
        self.scholar_rejection_reason = ScrolledText(review, height=4, wrap="word")
        self.scholar_rejection_reason.grid(row=3, column=2, sticky="nsew")
        self.scholar_review_detail = ScrolledText(review, height=5, wrap="word")
        self.scholar_review_detail.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=(0, 8), pady=(8, 0))
        self.scholar_linked_question = ScrolledText(review, height=5, wrap="word")
        self.scholar_linked_question.grid(row=4, column=2, sticky="nsew", pady=(8, 0))
        for col in range(3):
            review.columnconfigure(col, weight=1)
        review.rowconfigure(4, weight=1)
        for col in range(3):
            tab.columnconfigure(col, weight=1)
        tab.rowconfigure(6, weight=0)
        tab.rowconfigure(7, weight=0)
        tab.rowconfigure(9, weight=0)
        tab.rowconfigure(10, weight=2)
        self._set_text(self.scholar_card, "No scholar input loaded.")
        self._set_text(self.scholar_seed_preview, "No research-question seed preview generated.")
        self._set_text(self.scholar_import_report, "No backend dry run performed. Dry run is required before commit.")
        self._set_text(self.scholar_review_detail, "Select a persistent scholar-input record for governed review.")
        self._set_text(self.scholar_linked_question, "No linked research-question record.")
        self._set_scholar_transition_controls(None)
        self.scholar_source_view.trace_add("write", lambda *_: self._scholar_source_view_changed())
        self.refresh_scholar_inbox()

    def _tab_research_input(self) -> None:
        tab = self.tabs["Research Input"]
        self.research_fields: dict[str, ScrolledText] = {}
        fields = [
            ("research_question", "Research question"),
            ("topic_domain", "Topic / domain"),
            ("region", "Region"),
            ("time_period", "Time period"),
            ("key_concepts", "Key concepts"),
            ("required_corpus_scope", "Required corpus scope"),
            ("exclusion_terms", "Exclusion terms"),
            ("scholar_notes", "Notes from scholar"),
        ]
        for index, (key, label) in enumerate(fields):
            row, col = divmod(index, 2)
            box = self._labeled_text(tab, label, row, col)
            self.research_fields[key] = box
        ttk.Label(tab, text="Output type desired").grid(row=4, column=0, sticky="w", pady=(10, 3))
        ttk.Combobox(tab, textvariable=self.output_type, values=OUTPUT_TYPES, state="readonly").grid(
            row=5, column=0, sticky="ew", padx=(0, 10)
        )
        controls = ttk.Frame(tab)
        controls.grid(row=6, column=0, columnspan=2, sticky="ew", pady=12)
        ttk.Button(controls, text="Save Research Input", command=self.save_research_input).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Generate Query Lens", command=self.generate_query_lens).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Clear Draft", command=self.clear_research_input).pack(side="left")
        self.input_status = ttk.Label(tab, text="Draft only. Saving does not create evidence claims or modify ontology.")
        self.input_status.grid(row=7, column=0, columnspan=2, sticky="w")
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)

    def _tab_query_lens(self) -> None:
        tab = self.tabs["Query Lens"]
        ttk.Label(tab, text="Layer hypothesis").grid(row=0, column=0, sticky="w")
        ttk.Combobox(tab, textvariable=self.layer_choice, values=LAYER_OPTIONS, state="readonly").grid(
            row=1, column=0, sticky="ew", pady=(3, 8)
        )
        self.query_preview = ScrolledText(tab, height=28, wrap="word")
        self.query_preview.grid(row=2, column=0, columnspan=3, sticky="nsew")
        controls = ttk.Frame(tab)
        controls.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)
        ttk.Button(controls, text="Preview Query Lens", command=self.generate_query_lens).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Approve Query Lens", command=self._disabled_notice_factory("Approve Query Lens")).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Export Query Lens", command=self.export_query_lens).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Send to Retrieval Console", command=lambda: self.notebook.select(self.tabs["Retrieval Console"])).pack(side="left")
        self.query_status = ttk.Label(tab, text="Planning stage only. Recoll does not run from this tab.")
        self.query_status.grid(row=4, column=0, columnspan=3, sticky="w")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)

    def _tab_retrieval(self) -> None:
        tab = self.tabs["Retrieval Console"]
        self._disabled_panel(
            tab,
            "Retrieval Console",
            "v0.3 does not run Recoll. A future governed retrieval cycle will display the exact query string, ranked clues, duplicate warnings, and queue-selection checkboxes. Every hit remains clue only: not evidence, not sampled, not ontology.",
            ["Run Governed Retrieval", "Load Previous Retrieval Run", "View Raw Hit Summary", "Send Selected Hits to Queue"],
        )

    def _tab_verification_queue(self) -> None:
        tab = self.tabs["Verification Queue"]
        columns = [
            "queue_id", "title", "candidate_type", "status", "source_stage", "layer_prior",
            "duplicate_group_id", "canonical_candidate_id", "approved_by", "approved_ts",
            "sampling_block_no", "rubric_version",
        ]
        self.queue_tree = self._tree(tab, columns, row=0)
        controls = ttk.Frame(tab)
        controls.grid(row=1, column=0, sticky="ew", pady=10)
        for label in [
            "Add Selected Retrieval Hits to Queue",
            "Mark Duplicate",
            "Set Canonical Candidate",
            "Approve for Sampling",
            "Defer",
            "Close Candidate",
            "Export Queue",
        ]:
            command = self.export_queue if label == "Export Queue" else self._disabled_notice_factory(label)
            ttk.Button(controls, text=label, command=command).pack(side="left", padx=(0, 6))
        self.queue_detail = ScrolledText(tab, height=8, wrap="word")
        self.queue_detail.grid(row=2, column=0, sticky="ew")
        self.queue_tree.bind("<<TreeviewSelect>>", self._show_queue_detail)
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        self.refresh_queue()

    def _tab_sampling(self) -> None:
        tab = self.tabs["Sampling Workbench"]
        self._disabled_panel(
            tab,
            "Sampling Workbench",
            "v0.3 prepares the shape of sampling but does not execute it. Sampling requires a queue item with status approved_for_sampling, rubric version, canonical file, concept probes, and explicit approval.",
            ["Prepare Sampling Plan", "Approve Sampling Plan", "Run Sampling", "Save Sampling Extract", "Send to Evidence Review"],
        )

    def _tab_evidence_review(self) -> None:
        tab = self.tabs["Evidence Review"]
        self.evidence_tree = self._tree(
            tab,
            ["title", "thesis_verdict", "thesis_confidence", "disposition", "evidence_grade", "layer_norm"],
            row=0,
        )
        controls = ttk.Frame(tab)
        controls.grid(row=1, column=0, sticky="ew", pady=10)
        for label in [
            "Mark Unsupported",
            "Mark Needs More Sampling",
            "Mark Sample Supported",
            "Create Evidence Verdict",
            "Send to Functional Interpretation",
        ]:
            ttk.Button(controls, text=label, command=self._disabled_notice_factory(label)).pack(side="left", padx=(0, 6))
        self._fill_tree(self.evidence_tree, project_state.evidence_rows())
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)

    def _tab_functional_interpretation(self) -> None:
        tab = self.tabs["Functional Interpretation"]
        self.functional_tree = self._tree(
            tab,
            ["title", "ir_function", "interaction", "layer_norm", "evidence_grade"],
            row=0,
        )
        controls = ttk.Frame(tab)
        controls.grid(row=1, column=0, sticky="ew", pady=10)
        for label in ["Draft Functional Interpretation", "Save Functional Interpretation", "Export Interpretation Card"]:
            ttk.Button(controls, text=label, command=self._disabled_notice_factory(label)).pack(side="left", padx=(0, 6))
        ttk.Label(
            tab,
            text="Functional interpretation does not override evidence grade and cannot convert a text into ontology-core.",
        ).grid(row=2, column=0, sticky="w")
        self._fill_tree(self.functional_tree, project_state.functional_roles())
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)

    def _tab_ontology(self) -> None:
        tab = self.tabs["Ontology Status"]
        panes = ttk.PanedWindow(tab, orient="horizontal")
        panes.grid(row=0, column=0, sticky="nsew")
        left = ttk.Frame(panes, padding=6)
        right = ttk.Frame(panes, padding=6)
        panes.add(left, weight=1)
        panes.add(right, weight=1)
        ttk.Label(left, text="Design Map - status: design_hypothesis", font=("TkDefaultFont", 11, "bold")).pack(anchor="w")
        self.design_tree = self._tree(left, ["node_id", "node_type", "label", "layer", "provenance_status"], pack=True)
        ttk.Label(right, text="Verified Ontology - currently zero ontology-core entries", font=("TkDefaultFont", 11, "bold")).pack(anchor="w")
        self.verified_box = ScrolledText(right, height=18, wrap="word")
        self.verified_box.pack(fill="both", expand=True)
        controls = ttk.Frame(tab)
        controls.grid(row=1, column=0, sticky="ew", pady=10)
        ttk.Button(controls, text="View Design Map", command=self.refresh_ontology).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="View Verified Ontology", command=self.refresh_ontology).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Propose Ontology Candidate", command=self._disabled_notice_factory("Propose Ontology Candidate")).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Export Ontology Status", command=self.export_ontology_status).pack(side="left")
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        self.refresh_ontology()

    def _tab_reports(self) -> None:
        tab = self.tabs["Reports and Exports"]
        ttk.Label(tab, text="Local report format").grid(row=0, column=0, sticky="w")
        ttk.Combobox(tab, textvariable=self.report_format, values=REPORT_FORMATS, state="readonly").grid(
            row=1, column=0, sticky="ew", pady=(3, 12)
        )
        buttons = [
            ("Research input memo", self.save_research_input),
            ("Rumination log", self.save_rumination_log),
            ("Organ map", self.export_organ_map),
            ("Supervisor brief", self.export_supervisor_brief),
            ("Query lens report", self.export_query_lens),
            ("Project state summary", self.export_project_state),
            ("Verification queue report", self.export_queue),
            ("Ontology status report", self.export_ontology_status),
        ]
        for row, (label, command) in enumerate(buttons, start=2):
            ttk.Button(tab, text=label, command=command).grid(row=row, column=0, sticky="ew", pady=3)
        for row, label in enumerate([
            "Retrieval run report", "Sampling report", "Evidence brief", "Functional interpretation card"
        ], start=2):
            ttk.Button(tab, text=label, command=self._disabled_notice_factory(label)).grid(row=row, column=1, sticky="ew", padx=10, pady=3)
        report_row = 2 + max(len(buttons), 4)
        self.report_status = ScrolledText(tab, height=16, wrap="word")
        self.report_status.grid(row=report_row, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        self._report(
            "Reports go under outputs/gui_reports/. Rumination outputs go under outputs/gui_reports/rumination/."
        )
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(report_row, weight=1)

    def _tab_project_state(self) -> None:
        tab = self.tabs["Project State"]
        self.state_box = ScrolledText(tab, height=28, wrap="word")
        self.state_box.grid(row=0, column=0, sticky="nsew")
        controls = ttk.Frame(tab)
        controls.grid(row=1, column=0, sticky="ew", pady=10)
        ttk.Button(controls, text="Refresh State", command=self.refresh_project_state).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Export Project State", command=self.export_project_state).pack(side="left")
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)

    def import_fragment_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Import scholar fragment",
            filetypes=[
                ("Text and Markdown", "*.txt *.md"),
                ("Word document", "*.docx"),
                ("All supported", "*.txt *.md *.docx"),
            ],
        )
        if not path:
            return
        try:
            text = self._read_import_path(Path(path))
        except Exception as exc:  # pragma: no cover - UI safety branch
            messagebox.showerror("Import failed", str(exc))
            return
        self.idea_text.delete("1.0", "end")
        self.idea_text.insert("1.0", text)
        self.idea_status.config(text="Imported file into Idea Capture. Capture it to save as scholar_input_not_evidence.")

    def capture_fragment(self) -> None:
        text = self.idea_text.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("No fragment", "Add text before capturing a scholar fragment.")
            return
        fragment = draft_intake.new_fragment(
            input_type=self.idea_input_type.get(),
            text=text,
            source_note=self.idea_source_note.get(),
            confidence=self.idea_confidence.get(),
            tags=self.idea_tags.get(),
        )
        self.fragments.append(fragment)
        self.refresh_fragment_tree()
        self.refresh_organ_map()
        self.idea_status.config(
            text=f"Captured {fragment.fragment_id} as {draft_intake.FRAGMENT_LABEL}; no evidence or ontology state changed."
        )
        self._report(f"Captured scholar fragment {fragment.fragment_id} as {draft_intake.FRAGMENT_LABEL}.")

    def classify_selected_or_current_fragment(self) -> None:
        fragment = self._selected_fragment()
        if fragment is None:
            text = self.idea_text.get("1.0", "end").strip()
            if not text:
                messagebox.showinfo("No fragment", "Select or enter a fragment before classifying.")
                return
            fragment = draft_intake.new_fragment(
                self.idea_input_type.get(), text, self.idea_source_note.get(), self.idea_confidence.get(), self.idea_tags.get()
            )
            self.fragments.append(fragment)
        draft_intake.classify_fragment(fragment)
        self.refresh_fragment_tree()
        self.refresh_organ_map()
        self.idea_status.config(text=f"Classified {fragment.fragment_id}: {', '.join(fragment.assigned_organs)}")
        self._show_fragment(fragment)

    def send_fragments_to_organ_builder(self) -> None:
        self.refresh_organ_map()
        self.notebook.select(self.tabs["Research Organ Builder"])
        self.organ_status.config(text="Fragments sent to organ builder. They remain scholar_input_not_evidence.")

    def save_rumination_log(self) -> None:
        path = draft_intake.write_rumination_log(self.fragments)
        self.idea_status.config(text=f"Rumination log saved locally: {path.relative_to(ROOT)}")
        self._report(f"Saved rumination log: {path.relative_to(ROOT)}")

    def refresh_fragment_tree(self) -> None:
        if hasattr(self, "fragment_tree"):
            self._fill_tree(self.fragment_tree, draft_intake.fragments_as_rows(self.fragments))

    def refresh_organ_map(self) -> None:
        self.organ_map = draft_intake.build_organ_map(self.fragments)
        if hasattr(self, "organ_tree"):
            self._fill_tree(self.organ_tree, draft_intake.organ_rows(self.organ_map))

    def assign_selected_fragment_to_selected_organ(self) -> None:
        fragment = self._selected_fragment()
        organ = self._selected_organ()
        if fragment is None or organ is None:
            messagebox.showinfo("Selection needed", "Select a fragment in Idea Capture and an organ in Research Organ Builder.")
            return
        if organ not in fragment.assigned_organs:
            fragment.assigned_organs.append(organ)
        fragment.classification_reason = f"Manually assigned to {organ}; label={draft_intake.FRAGMENT_LABEL}"
        self.refresh_fragment_tree()
        self.refresh_organ_map()
        self._show_organ(organ)

    def move_selected_fragment_to_selected_organ(self) -> None:
        fragment = self._selected_fragment()
        organ = self._selected_organ()
        if fragment is None or organ is None:
            messagebox.showinfo("Selection needed", "Select a fragment and destination organ first.")
            return
        fragment.assigned_organs = [organ]
        fragment.classification_reason = f"Manually moved to {organ}; label={draft_intake.FRAGMENT_LABEL}"
        self.refresh_fragment_tree()
        self.refresh_organ_map()
        self._show_organ(organ)

    def merge_fragments_for_selected_organ(self) -> None:
        organ = self._selected_organ()
        if organ is None:
            messagebox.showinfo("Selection needed", "Select an organ first.")
            return
        fragments = self.organ_map.get(organ, {}).get("fragments", [])
        if len(fragments) < 2:
            messagebox.showinfo("Merge not ready", "At least two fragments are needed to merge.")
            return
        merged = draft_intake.new_fragment(
            input_type="paragraph",
            text="\n\n".join(fragment.text for fragment in fragments),
            source_note="self-thought",
            confidence=draft_intake.organ_confidence(fragments),
            tags=f"merged,{organ}",
        )
        merged.assigned_organs = [organ]
        merged.classification_reason = f"Merged from {len(fragments)} fragments for {organ}; label={draft_intake.FRAGMENT_LABEL}"
        self.fragments.append(merged)
        self.refresh_fragment_tree()
        self.refresh_organ_map()
        self._show_organ(organ)

    def draft_selected_organ_text(self) -> None:
        organ = self._selected_organ()
        if organ is None:
            messagebox.showinfo("Selection needed", "Select an organ first.")
            return
        markdown = draft_intake.draft_organ_text(organ, self.organ_map)
        self._set_text(self.organ_detail, markdown)
        self._set_text(self.draft_text, markdown)
        self.notebook.select(self.tabs["Research Organ Builder"])

    def export_organ_map(self) -> None:
        self.refresh_organ_map()
        path = draft_intake.write_organ_map_csv(self.organ_map)
        self.organ_status.config(text=f"Organ map exported locally: {path.relative_to(ROOT)}")
        self._report(f"Exported organ map: {path.relative_to(ROOT)}")

    def generate_synopsis_skeleton(self) -> None:
        self.refresh_organ_map()
        markdown = draft_intake.generate_synopsis_skeleton(self.organ_map)
        path = scholar_brief.write_markdown("synopsis-skeleton", markdown)
        self._set_text(self.organ_detail, markdown)
        self._set_text(self.draft_text, markdown)
        self.organ_status.config(text=f"Synopsis skeleton generated: {path.relative_to(ROOT)}")
        self._report(f"Generated synopsis skeleton: {path.relative_to(ROOT)}")

    def diagnose_draft(self) -> None:
        text = self.draft_text.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("No draft", "Paste or generate draft text before diagnosis.")
            return
        diagnosis = draft_diagnosis.diagnose_draft(text)
        self._set_text(self.diagnosis_output, json.dumps(diagnosis, indent=2, ensure_ascii=False))

    def load_synopsis_into_diagnosis(self) -> None:
        self._set_text(self.draft_text, draft_intake.generate_synopsis_skeleton(self.organ_map))

    def use_captured_concepts(self) -> None:
        text = "\n".join(
            fragment.text
            for fragment in self.fragments
            if fragment.input_type in {"concept", "theory hunch", "research question", "problem fragment"}
        )
        self._set_text(self.concept_text, text)

    def analyse_concept_fit(self) -> None:
        data = project_state.ontology_status()
        rows = concept_fit.match_concepts(
            self.concept_text.get("1.0", "end"),
            self.fragments,
            data["design_nodes"],
            project_state.evidence_rows(limit=200),
            project_state.verification_queue(),
        )
        self._fill_tree(self.concept_tree, rows)
        self.concept_status.config(text="Concept fit generated. Design-map matches remain not verified.")

    def generate_literature_search_plan(self) -> None:
        self.refresh_organ_map()
        self.last_literature_plan = scholar_brief.literature_search_plan(self.fragments, self.organ_map)
        self._set_text(self.search_plan_output, json.dumps(self.last_literature_plan, indent=2, ensure_ascii=False))

    def export_literature_search_plan(self) -> None:
        if self.last_literature_plan is None:
            self.generate_literature_search_plan()
        if self.last_literature_plan is None:
            return
        markdown = "# Literature Search Plan\n\n```json\n"
        markdown += json.dumps(self.last_literature_plan, indent=2, ensure_ascii=False)
        markdown += "\n```\n"
        path = scholar_brief.write_markdown("literature-search-plan", markdown)
        self._report(f"Exported literature search plan: {path.relative_to(ROOT)}")

    def generate_supervisor_brief(self) -> None:
        self.refresh_organ_map()
        if self.last_literature_plan is None:
            self.last_literature_plan = scholar_brief.literature_search_plan(self.fragments, self.organ_map)
        markdown = scholar_brief.supervisor_brief(self.organ_map, self.last_literature_plan)
        self._set_text(self.supervisor_brief_output, markdown)

    def export_supervisor_brief(self) -> None:
        text = self.supervisor_brief_output.get("1.0", "end").strip()
        if not text:
            self.generate_supervisor_brief()
            text = self.supervisor_brief_output.get("1.0", "end").strip()
        path = scholar_brief.export_supervisor_brief(text)
        self._report(f"Exported supervisor brief: {path.relative_to(ROOT)}")

    def load_scholar_input_json(self) -> None:
        path = filedialog.askopenfilename(
            title="Load Scholar Input JSON",
            initialdir=str(ROOT / "outputs" / "gui_reports" / "scholar_inputs"),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            self.current_scholar_input = scholar_input_schema.load_json(Path(path))
        except Exception as exc:  # pragma: no cover - UI safety branch
            messagebox.showerror("Scholar input load failed", str(exc))
            return
        self.current_scholar_validation = scholar_input_schema.validate_record(self.current_scholar_input)
        self.scholar_selected_import_path = Path(path)
        self.scholar_dry_run_report = None
        self.scholar_commit_button.config(state="disabled")
        self.current_scholar_seed_preview = None
        self._render_scholar_input()
        self.scholar_input_status.config(text=f"Loaded scholar input JSON: {Path(path).name}")
        self.refresh_scholar_inbox(update_status=False)

    def refresh_scholar_inbox(self, update_status: bool = True) -> None:
        self.scholar_inbox_records = scholar_input_schema.discover_inbox_records()
        self.scholar_persistent_records = scholar_input_backend.persistent_rows()
        self._update_scholar_status_values()
        self._render_scholar_inbox_list()
        if update_status:
            self.scholar_input_status.config(
                text=(f"Refreshed Scholar Input Inbox: {len(self.scholar_inbox_records)} local JSON record(s), "
                      f"{len(self.scholar_persistent_records)} persistent record(s).")
            )

    def _scholar_source_view_changed(self) -> None:
        self._update_scholar_status_values()
        self._render_scholar_inbox_list()
        self.scholar_input_status.config(
            text=f"Source view: {self.scholar_source_view.get()}. Scholar input is not evidence."
        )
        if self.scholar_source_view.get() != "Persistent Database":
            self.selected_persistent_scholar = None
            self._set_scholar_transition_controls(None)

    def _update_scholar_status_values(self) -> None:
        if not hasattr(self, "scholar_status_combo"):
            return
        values = (["All", *scholar_input_backend.taxonomy_statuses()]
                  if self.scholar_source_view.get() == "Persistent Database"
                  else scholar_input_schema.STATUS_FILTER_VALUES)
        self.scholar_status_combo.config(values=values)
        if self.scholar_status_filter.get() not in values:
            self.scholar_status_filter.set("All")

    def run_scholar_import_dry_run(self) -> None:
        if self.scholar_selected_import_path is None or self.current_scholar_input is None:
            messagebox.showinfo("Select local JSON", "Select and locally validate a scholar-input JSON file first.")
            return
        self.current_scholar_validation = scholar_input_schema.validate_record(self.current_scholar_input)
        if not scholar_input_schema.is_valid(self.current_scholar_validation):
            self.scholar_commit_button.config(state="disabled")
            messagebox.showerror("Local validation failed", "Fix the displayed local validation errors before dry run.")
            return
        report = scholar_input_backend.run_importer(self.scholar_selected_import_path)
        self.scholar_dry_run_report = report
        self._set_text(self.scholar_import_report, scholar_input_backend.readable_report(report))
        self.scholar_commit_button.config(state="normal" if report.can_commit else "disabled")
        self.scholar_input_status.config(
            text="Backend dry run complete. Commit is enabled only for an eligible, zero-invalid batch."
        )

    def commit_scholar_import(self) -> None:
        report = self.scholar_dry_run_report
        if self.scholar_selected_import_path is None or report is None or not report.can_commit:
            self.scholar_commit_button.config(state="disabled")
            messagebox.showinfo("Dry run required", "A successful backend dry run is required before commit.")
            return
        if not messagebox.askyesno(
            "Confirm scholar-input commit",
            "Commit the eligible records reported by the dry run? Scholar input is not evidence.",
        ):
            self.scholar_input_status.config(text="Commit cancelled by user. No database changes made.")
            return
        commit_report = scholar_input_backend.run_importer(self.scholar_selected_import_path, commit=True)
        self._set_text(self.scholar_import_report, scholar_input_backend.readable_report(commit_report))
        self.scholar_commit_button.config(state="disabled")
        self.scholar_dry_run_report = None
        if commit_report.exit_code != 0 or commit_report.transaction_outcome != "COMMITTED":
            messagebox.showerror("Scholar-input commit failed", scholar_input_backend.readable_report(commit_report))
            return
        self.scholar_source_view.set("Persistent Database")
        self.refresh_scholar_inbox(update_status=False)
        validation = scholar_input_backend.run_consistency_validator()
        validation_text = (validation.stdout + "\n" + validation.stderr).strip()
        self._set_text(
            self.scholar_import_report,
            scholar_input_backend.readable_report(commit_report) + "\n\nConsistency validation\n" + validation_text,
        )
        self.scholar_input_status.config(
            text=f"Commit complete; persistent Inbox refreshed; consistency validator exit code {validation.returncode}."
        )

    def start_scholar_review(self) -> None:
        self._run_scholar_transition("start-review")

    def open_scholar_review_window(self) -> None:
        if self.selected_persistent_scholar is None:
            messagebox.showinfo("Persistent record required", "Select a persistent scholar-input row first.")
            return
        window = Toplevel(self.root)
        window.title(f"Governed Scholar-Input Review — {self.selected_persistent_scholar['scholar_id']}")
        window.geometry("1100x650")
        window.minsize(900, 560)
        self.scholar_review_window = window
        frame = ttk.Frame(window, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="SCHOLAR INPUT — NOT EVIDENCE", foreground="#8a3d00",
                  font=("TkDefaultFont", 12, "bold")).grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(frame, text="Decision actor (required)").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(frame, textvariable=self.scholar_review_actor).grid(row=2, column=0, sticky="ew", padx=(0, 8))
        ttk.Label(frame, text="Approved seed type").grid(row=1, column=1, sticky="w", pady=(8, 0))
        ttk.Combobox(frame, textvariable=self.scholar_review_lens_type,
                     values=["research_question", "retrieval_lens"], state="readonly").grid(
            row=2, column=1, sticky="ew", padx=(0, 8))
        actions = ttk.Frame(frame); actions.grid(row=2, column=2, sticky="ew")
        self.scholar_start_review_button = ttk.Button(actions, text="Start Review", command=self.start_scholar_review)
        self.scholar_start_review_button.pack(side="left", padx=(0, 6))
        self.scholar_approve_button = ttk.Button(actions, text="Approve to Question", command=self.approve_scholar_to_question)
        self.scholar_approve_button.pack(side="left", padx=(0, 6))
        self.scholar_reject_button = ttk.Button(actions, text="Reject and Archive", command=self.reject_scholar_input)
        self.scholar_reject_button.pack(side="left")
        ttk.Label(frame, text="Final approved question/lens text (original idea remains unchanged)").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))
        ttk.Label(frame, text="Rejection reason").grid(row=3, column=2, sticky="w", pady=(10, 0))
        self.scholar_final_question = ScrolledText(frame, height=5, wrap="word")
        self.scholar_final_question.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=(0, 8))
        self.scholar_rejection_reason = ScrolledText(frame, height=5, wrap="word")
        self.scholar_rejection_reason.grid(row=4, column=2, sticky="nsew")
        ttk.Label(frame, text="Read-only source record").grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))
        ttk.Label(frame, text="Read-only linked destination").grid(row=5, column=2, sticky="w", pady=(10, 0))
        self.scholar_review_detail = ScrolledText(frame, height=14, wrap="word")
        self.scholar_review_detail.grid(row=6, column=0, columnspan=2, sticky="nsew", padx=(0, 8))
        self.scholar_linked_question = ScrolledText(frame, height=14, wrap="word")
        self.scholar_linked_question.grid(row=6, column=2, sticky="nsew")
        self.scholar_transition_report = ScrolledText(frame, height=5, wrap="word")
        self.scholar_transition_report.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        for col in range(3): frame.columnconfigure(col, weight=1)
        frame.rowconfigure(6, weight=1)
        self._select_persistent_scholar(self.selected_persistent_scholar)
        self._set_text(self.scholar_transition_report, "Dry-run transition preview will appear here before confirmation.")

    def approve_scholar_to_question(self) -> None:
        self._run_scholar_transition("approve-to-question")

    def reject_scholar_input(self) -> None:
        self._run_scholar_transition("reject")

    def _run_scholar_transition(self, action: str) -> None:
        record = self.selected_persistent_scholar
        if record is None:
            messagebox.showinfo("Persistent record required", "Select a persistent scholar-input row first.")
            return
        actor = self.scholar_review_actor.get().strip()
        if not actor:
            messagebox.showerror("Decision actor required", "Enter the explicit decision actor before previewing a transition.")
            return
        question_text = self.scholar_final_question.get("1.0", "end").strip()
        rejection_reason = self.scholar_rejection_reason.get("1.0", "end").strip()
        if action == "approve-to-question" and not question_text:
            messagebox.showerror("Final text required", "Enter the final approved question or retrieval-lens text.")
            return
        if action == "reject" and not rejection_reason:
            messagebox.showerror("Rejection reason required", "Enter a non-empty rejection reason.")
            return
        kwargs = dict(
            scholar_id=record["scholar_id"], action=action, decided_by=actor,
            question_text=question_text, lens_type=self.scholar_review_lens_type.get(),
            rejection_reason=rejection_reason,
        )
        preview = scholar_input_backend.run_transition(**kwargs)
        self._set_text(self.scholar_import_report, scholar_input_backend.readable_transition_result(preview))
        if hasattr(self, "scholar_transition_report") and self.scholar_transition_report.winfo_exists():
            self._set_text(self.scholar_transition_report, scholar_input_backend.readable_transition_result(preview))
        self.root.update_idletasks()
        if not preview.accepted:
            messagebox.showinfo("Transition refused", scholar_input_backend.readable_transition_result(preview))
            return
        if not messagebox.askyesno(
            "Confirm governed transition",
            f"Commit {action} for {record['scholar_id']} after the displayed dry-run preview?",
        ):
            self.scholar_input_status.config(text="Transition cancelled by user. No database changes made.")
            return
        result = scholar_input_backend.run_transition(**kwargs, commit=True)
        self._set_text(self.scholar_import_report, scholar_input_backend.readable_transition_result(result))
        if hasattr(self, "scholar_transition_report") and self.scholar_transition_report.winfo_exists():
            self._set_text(self.scholar_transition_report, scholar_input_backend.readable_transition_result(result))
        if not result.accepted or not result.data.get("committed"):
            messagebox.showinfo("Transition not committed", scholar_input_backend.readable_transition_result(result))
            return
        scholar_id = record["scholar_id"]
        self.refresh_scholar_inbox(update_status=False)
        refreshed = next((row for row in self.scholar_persistent_records if row["scholar_id"] == scholar_id), None)
        self._select_persistent_scholar(refreshed)
        validation = scholar_input_backend.run_consistency_validator()
        self.scholar_input_status.config(
            text=f"Governed transition committed; row refreshed; consistency validator exit code {validation.returncode}."
        )

    def _select_persistent_scholar(self, record: dict | None) -> None:
        self.selected_persistent_scholar = record
        self._set_scholar_transition_controls(record.get("status") if record else None)
        if not record:
            self._set_text(self.scholar_review_detail, "No persistent scholar-input selected.")
            self._set_text(self.scholar_linked_question, "No linked research-question record.")
            return
        fields = [
            "scholar_id", "status", "source", "captured_ts", "imported_ts", "draft_organ",
            "idea", "raw_notes", "tags", "confidence", "project_title", "course_or_context",
            "became_question", "decided_by", "decided_ts", "rejection_reason",
        ]
        self._set_text(self.scholar_review_detail, "\n".join(f"{field}: {record.get(field) or ''}" for field in fields))
        linked = scholar_input_backend.research_question(record.get("became_question") or "")
        if linked:
            self._set_text(self.scholar_linked_question, "Linked research-question destination\n" + "\n".join(
                f"{field}: {linked.get(field) or ''}" for field in
                ["question_id", "lens_type", "question_text", "status", "origin_scholar_id", "created_ts", "created_by"]
            ))
        else:
            self._set_text(self.scholar_linked_question, "No linked research-question record.")

    def _set_scholar_transition_controls(self, status: str | None) -> None:
        if not hasattr(self, "scholar_start_review_button"):
            return
        self.scholar_start_review_button.config(state="normal" if status == "imported_not_evidence" else "disabled")
        terminal_ready = status == "under_review"
        self.scholar_approve_button.config(state="normal" if terminal_ready else "disabled")
        self.scholar_reject_button.config(state="normal" if terminal_ready else "disabled")

    def reset_scholar_inbox_filters(self) -> None:
        self.scholar_status_filter.set("All")
        self.scholar_source_filter.set("All")
        self.scholar_organ_filter.set("All")
        self._render_scholar_inbox_list()
        self.scholar_input_status.config(text="Scholar Input Inbox filters reset.")

    def clear_scholar_inbox_search(self) -> None:
        self.scholar_search_query.set("")
        self._render_scholar_inbox_list()
        self.scholar_input_status.config(text="Scholar Input Inbox search cleared.")

    def load_selected_scholar_record(self) -> None:
        item = self._selected_scholar_inbox_record()
        if item is None:
            messagebox.showinfo("No record selected", "Select a scholar-input row first.")
            return
        if item.record is None:
            self.current_scholar_input = None
            self.current_scholar_validation = item.validation_items
            self.current_scholar_seed_preview = None
            self._fill_tree(self.scholar_validation_tree, scholar_input_schema.validation_rows(item.validation_items))
            self._set_text(self.scholar_card, f"Could not load {item.filename}: {item.load_error}")
            self._set_text(self.scholar_seed_preview, "No preview available for invalid JSON.")
            self.scholar_input_status.config(text=f"Selected record is invalid JSON: {item.filename}")
            return
        self.current_scholar_input = item.record
        self.current_scholar_validation = item.validation_items
        self.current_scholar_seed_preview = None
        self.scholar_selected_import_path = item.path
        self.scholar_dry_run_report = None
        self.scholar_commit_button.config(state="disabled")
        self._render_scholar_input()
        self.scholar_input_status.config(
            text=f"Loaded selected scholar input: {item.filename}. Read-only; no backend state changed."
        )

    def validate_selected_scholar_input(self) -> None:
        item = self._selected_scholar_inbox_record()
        if item is not None:
            self.load_selected_scholar_record()
            if item.record is None:
                self.scholar_input_status.config(text=f"Validation result: invalid JSON in {item.filename}.")
                return
        self.validate_scholar_input()

    def export_selected_scholar_summary(self) -> None:
        item = self._selected_scholar_inbox_record()
        if item is not None and item.record is None:
            messagebox.showinfo("Invalid record", "Invalid JSON cannot be exported as a scholar-input summary.")
            return
        if item is not None and item.record is not self.current_scholar_input:
            self.load_selected_scholar_record()
        self.export_scholar_input_summary()

    def open_scholar_reports_folder(self) -> None:
        scholar_input_schema.REPORT_DIR.mkdir(parents=True, exist_ok=True)
        opened = webbrowser.open(scholar_input_schema.REPORT_DIR.as_uri())
        if opened:
            self.scholar_input_status.config(text="Opened local scholar-input reports folder.")
        else:
            self.scholar_input_status.config(text="Could not open reports folder from this environment.")

    def validate_scholar_input(self) -> None:
        if self.current_scholar_input is None:
            messagebox.showinfo("No scholar input", "Load a v0.2 scholar input JSON file first.")
            return
        self.current_scholar_validation = scholar_input_schema.validate_record(self.current_scholar_input)
        self._fill_tree(
            self.scholar_validation_tree,
            scholar_input_schema.validation_rows(self.current_scholar_validation),
        )
        verdict = "valid" if scholar_input_schema.is_valid(self.current_scholar_validation) else "invalid"
        self.scholar_input_status.config(text=f"Schema validation result: {verdict}. No backend state changed.")

    def preview_scholar_question_seed(self) -> None:
        if self.current_scholar_input is None:
            messagebox.showinfo("No scholar input", "Load a v0.2 scholar input JSON file first.")
            return
        self.current_scholar_seed_preview = scholar_input_schema.question_seed_preview(self.current_scholar_input)
        self._set_text(
            self.scholar_seed_preview,
            json.dumps(self.current_scholar_seed_preview, indent=2, ensure_ascii=False),
        )
        self.scholar_input_status.config(
            text="Research-question seed preview generated. This is non-mutating and not evidence."
        )

    def export_scholar_input_summary(self) -> None:
        if self.current_scholar_input is None:
            messagebox.showinfo("No scholar input", "Load a v0.2 scholar input JSON file first.")
            return
        if not self.current_scholar_validation:
            self.current_scholar_validation = scholar_input_schema.validate_record(self.current_scholar_input)
        if self.current_scholar_seed_preview is None:
            self.current_scholar_seed_preview = scholar_input_schema.question_seed_preview(self.current_scholar_input)
        paths = scholar_input_reports.export_report_bundle(
            self.current_scholar_input,
            self.current_scholar_validation,
            self.current_scholar_seed_preview,
        )
        rel_paths = ", ".join(str(path.relative_to(ROOT)) for path in paths)
        self.scholar_input_status.config(text=f"Exported scholar input reports: {rel_paths}")
        self._report(f"Exported scholar input reports: {rel_paths}")

    def copy_scholar_supervisor_note(self) -> None:
        if self.current_scholar_input is None:
            messagebox.showinfo("No scholar input", "Load a v0.2 scholar input JSON file first.")
            return
        note = scholar_input_reports.supervisor_note(
            self.current_scholar_input,
            self.current_scholar_seed_preview,
        )
        self.root.clipboard_clear()
        self.root.clipboard_append(note)
        self.scholar_input_status.config(text="Supervisor note copied. It includes SCHOLAR INPUT — NOT EVIDENCE.")

    def _render_scholar_input(self) -> None:
        if self.current_scholar_input is None:
            return
        self._set_text(self.scholar_card, scholar_input_schema.display_card(self.current_scholar_input))
        self._fill_tree(
            self.scholar_validation_tree,
            scholar_input_schema.validation_rows(self.current_scholar_validation),
        )
        self._set_text(self.scholar_seed_preview, "Preview not generated yet. Use Preview Research Question Seed.")

    def _render_scholar_inbox_list(self) -> None:
        if not hasattr(self, "scholar_inbox_tree"):
            return
        if self.scholar_source_view.get() == "Persistent Database":
            filtered = scholar_input_backend.filter_persistent_rows(
                self.scholar_persistent_records,
                status=self.scholar_status_filter.get(),
                source=self.scholar_source_filter.get(),
                organ=self.scholar_organ_filter.get(),
                search=self.scholar_search_query.get(),
            )
            rows = [self._persistent_scholar_row(row) for row in filtered]
            total = len(self.scholar_persistent_records)
            source_label = "persistent database"
        else:
            filtered = self._filtered_scholar_inbox_records()
            rows = [self._local_scholar_row(item) for item in filtered]
            total = len(self.scholar_inbox_records)
            source_label = "local JSON"
        self._fill_tree(self.scholar_inbox_tree, rows)
        if hasattr(self, "scholar_inbox_count"):
            self.scholar_inbox_count.config(
                text=f"Showing {len(filtered)} of {total} {source_label} scholar-input records"
            )

    @staticmethod
    def _local_scholar_row(item: scholar_input_schema.InboxRecord) -> dict[str, str]:
        record = item.record or {}
        return {
            "view": "Local JSON", "filename": item.filename,
            "scholar_id": str(record.get("scholar_id") or ""),
            "captured_ts": str(record.get("captured_ts") or ""),
            "imported_ts": str(record.get("imported_ts") or ""),
            "source": str(record.get("source") or ""),
            "draft_organ": str(record.get("draft_organ") or ""),
            "status": str(record.get("status") or ""), "idea": str(record.get("idea") or ""),
            "tags": str(record.get("tags") or ""), "confidence": str(record.get("confidence") or ""),
            "project_title": str(record.get("project_title") or ""),
            "course_or_context": str(record.get("course_or_context") or ""),
            "content_sha256": str(record.get("content_sha256") or "")[:12],
            "validation_status": item.validation_status,
        }

    @staticmethod
    def _persistent_scholar_row(record: dict) -> dict[str, str]:
        return {
            "view": "Persistent Database", "filename": "", **record,
            "idea": str(record.get("idea") or ""),
            "content_sha256": str(record.get("content_sha256") or "")[:12],
            "validation_status": "persistent read-only",
        }

    def _filtered_scholar_inbox_records(self) -> list[scholar_input_schema.InboxRecord]:
        return scholar_input_schema.filter_inbox_records(
            self.scholar_inbox_records,
            status_filter=self.scholar_status_filter.get(),
            source_filter=self.scholar_source_filter.get(),
            organ_filter=self.scholar_organ_filter.get(),
            search_query=self.scholar_search_query.get(),
        )

    def _selected_scholar_inbox_record(self) -> scholar_input_schema.InboxRecord | None:
        if self.scholar_source_view.get() != "Local JSON":
            return None
        selected = self.scholar_inbox_tree.selection() if hasattr(self, "scholar_inbox_tree") else ()
        if not selected:
            return None
        values = self.scholar_inbox_tree.item(selected[0], "values")
        if not values:
            return None
        filename = str(values[1])
        return next((record for record in self.scholar_inbox_records if record.filename == filename), None)

    def _preview_selected_scholar_record(self, _: object = None) -> None:
        if self.scholar_source_view.get() == "Persistent Database":
            selected = self.scholar_inbox_tree.selection()
            if not selected:
                return
            values = self.scholar_inbox_tree.item(selected[0], "values")
            scholar_id = str(values[2]) if values else ""
            record = next((row for row in self.scholar_persistent_records if row["scholar_id"] == scholar_id), None)
            if record:
                self._select_persistent_scholar(record)
                self._set_text(self.scholar_card, scholar_input_schema.display_card(record))
                self._fill_tree(self.scholar_validation_tree, [])
                self._set_text(self.scholar_seed_preview, "Persistent record is read-only; transitions use the governed backend CLI.")
                self.scholar_input_status.config(text=f"Selected persistent scholar input: {scholar_id}. Read-only.")
            return
        item = self._selected_scholar_inbox_record()
        if item is None:
            return
        if item.record is None:
            self._set_text(self.scholar_card, f"{item.filename}\n\nInvalid JSON: {item.load_error}")
            self._fill_tree(self.scholar_validation_tree, scholar_input_schema.validation_rows(item.validation_items))
            self._set_text(self.scholar_seed_preview, "No preview available for invalid JSON.")
            return
        self.current_scholar_input = item.record
        self.current_scholar_validation = item.validation_items
        self.current_scholar_seed_preview = None
        self._render_scholar_input()
        self.scholar_input_status.config(text=f"Selected local scholar input: {item.filename}")

    def _scholar_input_disabled_factory(self, action: str):
        def notice() -> None:
            explanations = {
                "Seed Research Question": (
                    "Disabled in v0.3 UI. Approval to question is a governed backend state transition; "
                    "this interface only previews the seed."
                ),
                "Reject and Archive": (
                    "Disabled in v0.3 UI. Rejection/archive requires backend storage and audit handling."
                ),
                "Run Retrieval": (
                    "Disabled in v0.3 UI. Retrieval must run only after an approved research question or lens."
                ),
                "Send to Verification Queue": (
                    "Not allowed. Scholar input cannot directly enter verification_queue; only real retrieved documents can."
                ),
            }
            message = explanations.get(action, "Disabled in v0.3 UI.")
            messagebox.showinfo(f"{action} disabled", message)
            self.scholar_input_status.config(text=message)
        return notice

    def current_research_input(self) -> query_lens.ResearchInput:
        values = {key: widget.get("1.0", "end").strip() for key, widget in self.research_fields.items()}
        return query_lens.ResearchInput(
            research_question=values["research_question"],
            topic_domain=values["topic_domain"],
            region=values["region"],
            time_period=values["time_period"],
            key_concepts=values["key_concepts"],
            required_corpus_scope=values["required_corpus_scope"],
            exclusion_terms=values["exclusion_terms"],
            scholar_notes=values["scholar_notes"],
            output_type=self.output_type.get(),
        )

    def save_research_input(self) -> None:
        self.current_input = self.current_research_input()
        path = report_writer.write_research_input(self.current_input.__dict__, self.report_format.get())
        self.input_status.config(text=f"Draft saved locally: {path.relative_to(ROOT)}")
        self._report(f"Saved draft research input: {path}")

    def generate_query_lens(self) -> None:
        self.current_input = self.current_research_input()
        lens = query_lens.build_lens(self.current_input)
        if self.layer_choice.get():
            lens.layer_hypothesis = self.layer_choice.get()
        self.current_lens = lens
        self.query_preview.delete("1.0", "end")
        self.query_preview.insert("1.0", json.dumps(query_lens.to_dict(lens), indent=2, ensure_ascii=False))
        self.query_status.config(text="Query lens preview generated. Planning stage only; no retrieval ran.")
        self.notebook.select(self.tabs["Query Lens"])

    def export_query_lens(self) -> None:
        if self.current_lens is None:
            self.generate_query_lens()
        if self.current_lens is None:
            return
        path = report_writer.write_query_lens(query_lens.to_dict(self.current_lens), self.report_format.get())
        self._report(f"Exported query lens: {path}")

    def export_project_state(self) -> None:
        state = project_state.load_project_state()
        path = report_writer.write_project_state(state.__dict__, self.report_format.get())
        self._report(f"Exported project state: {path}")

    def export_queue(self) -> None:
        payload = {"verification_queue": project_state.verification_queue()}
        path = report_writer.write_project_state(payload, self.report_format.get())
        self._report(f"Exported verification queue snapshot: {path}")

    def export_ontology_status(self) -> None:
        payload = project_state.ontology_status()
        path = report_writer.write_project_state(payload, self.report_format.get())
        self._report(f"Exported ontology status: {path}")

    def clear_research_input(self) -> None:
        for widget in self.research_fields.values():
            widget.delete("1.0", "end")
        self.input_status.config(text="Draft cleared. No project state changed.")

    def refresh_project_state(self) -> None:
        state = project_state.load_project_state()
        lines = [
            "Knowledge Prism Research Exoskeleton - Project State",
            "",
            f"Ledger blocks: {state.ledger_blocks}",
            f"Latest block: {state.latest_block_no} - {state.latest_block_title}",
            f"Chain verification: {'OK' if state.chain_ok else 'BROKEN'}",
            f"Action log: {'OK' if state.action_log_ok else 'BROKEN'}",
            f"Current stage: {state.current_stage}",
            "",
            f"Master corpus rows: {state.master_corpus_rows:,}",
            f"Pilot rows: {state.pilot_rows}",
            f"Sample-supported candidates: {state.sample_supported_rows}",
            f"Verification queue rows: {state.verification_queue_rows}",
            f"Boundary proposals: {state.boundary_proposal_rows}",
            f"Concept-verified count: {state.concept_verified_rows}",
            f"Ontology-core count: {state.ontology_core_rows}",
            f"Design map: {state.design_nodes} nodes / {state.design_edges} edges",
            f"Functional interpretations: {state.functional_role_rows}",
            "",
            "Warnings:",
            "- Design ontology is not verified ontology.",
            "- Trenin or any anchor candidate is queued only unless sampled.",
            "- Boundary proposals are not adopted doctrine.",
        ]
        self.state_box.delete("1.0", "end")
        self.state_box.insert("1.0", "\n".join(lines))

    def refresh_queue(self) -> None:
        self._fill_tree(self.queue_tree, project_state.verification_queue())

    def refresh_ontology(self) -> None:
        data = project_state.ontology_status()
        self._fill_tree(self.design_tree, data["design_nodes"])
        self.verified_box.delete("1.0", "end")
        self.verified_box.insert(
            "1.0",
            "Verified ontology-core entries: 0\n\n"
            "The design map remains a design_hypothesis scaffold. "
            "No design node becomes verified ontology without the full evidence process.",
        )

    def _show_queue_detail(self, _: object = None) -> None:
        selected = self.queue_tree.selection()
        if not selected:
            return
        values = self.queue_tree.item(selected[0], "values")
        columns = self.queue_tree["columns"]
        summary = dict(zip(columns, values))
        rows = project_state.verification_queue()
        detail = next((row for row in rows if row.get("queue_id") == summary.get("queue_id")), summary)
        self.queue_detail.delete("1.0", "end")
        self.queue_detail.insert("1.0", json.dumps(detail, indent=2, ensure_ascii=False))

    def _show_fragment_detail(self, _: object = None) -> None:
        fragment = self._selected_fragment()
        if fragment is not None:
            self._show_fragment(fragment)

    def _show_fragment(self, fragment: draft_intake.ResearchFragment) -> None:
        detail = {
            "fragment_id": fragment.fragment_id,
            "label": fragment.label,
            "input_type": fragment.input_type,
            "source_note": fragment.source_note,
            "confidence": fragment.confidence,
            "tags": fragment.tags,
            "assigned_organs": fragment.assigned_organs,
            "classification_reason": fragment.classification_reason,
            "text": fragment.text,
        }
        self._set_text(self.fragment_detail, json.dumps(detail, indent=2, ensure_ascii=False))

    def _show_organ_detail(self, _: object = None) -> None:
        organ = self._selected_organ()
        if organ is not None:
            self._show_organ(organ)

    def _show_organ(self, organ: str) -> None:
        entry = self.organ_map.get(organ)
        if not entry:
            return
        lines = [
            f"Organ: {organ}",
            f"Status: {entry['status']}",
            f"Confidence: {entry['confidence']}",
            f"Suggested next action: {entry['suggested_next_action']}",
            "",
            f"Safety: all assigned fragments remain {draft_intake.FRAGMENT_LABEL}.",
            "",
        ]
        for fragment in entry["fragments"]:
            lines.extend([
                f"- {fragment.fragment_id} ({fragment.input_type}, {fragment.confidence})",
                f"  {fragment.text}",
                "",
            ])
        self._set_text(self.organ_detail, "\n".join(lines).strip())

    def _selected_fragment(self) -> draft_intake.ResearchFragment | None:
        if not self.fragments:
            return None
        if not hasattr(self, "fragment_tree"):
            return self.fragments[-1]
        selected = self.fragment_tree.selection()
        if selected:
            values = self.fragment_tree.item(selected[0], "values")
            if values:
                fragment_id = str(values[0])
                found = next((fragment for fragment in self.fragments if fragment.fragment_id == fragment_id), None)
                if found is not None:
                    return found
        return self.fragments[-1]

    def _selected_organ(self) -> str | None:
        if not hasattr(self, "organ_tree"):
            return None
        selected = self.organ_tree.selection()
        if selected:
            values = self.organ_tree.item(selected[0], "values")
            if values:
                return str(values[0])
        children = self.organ_tree.get_children()
        if children:
            return str(self.organ_tree.item(children[0], "values")[0])
        return None

    def _read_import_path(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            return path.read_text(encoding="utf-8")
        if suffix == ".docx":
            with ZipFile(path) as docx:
                xml = docx.read("word/document.xml")
            root = ET.fromstring(xml)
            namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            paragraphs = []
            for paragraph in root.findall(".//w:p", namespace):
                text = "".join(node.text or "" for node in paragraph.findall(".//w:t", namespace))
                if text.strip():
                    paragraphs.append(text.strip())
            return "\n\n".join(paragraphs)
        raise ValueError("Unsupported import type. Use .txt, .md, or .docx.")

    def _toggle_write_mode(self) -> None:
        if self.write_mode.get():
            ok = messagebox.askokcancel("Enable governed write mode?", safety.WRITE_MODE_WARNING)
            if not ok:
                self.write_mode.set(False)
                return
            self.mode_label.config(text=safety.WRITE_MODE_WARNING, foreground="#9a681e")
        else:
            self.mode_label.config(text=safety.READ_ONLY_WARNING, foreground="#176b56")

    def _disabled_notice_factory(self, action: str):
        def notice() -> None:
            message = safety.disabled_reason(action)
            messagebox.showinfo(f"{action} disabled in v0.3", message)
            self._report(f"{action}: {message}")
        return notice

    def _disabled_panel(self, tab: ttk.Frame, title: str, text: str, buttons: list[str]) -> None:
        ttk.Label(tab, text=title, font=("TkDefaultFont", 14, "bold")).grid(row=0, column=0, sticky="w")
        box = ScrolledText(tab, height=14, wrap="word")
        box.grid(row=1, column=0, sticky="nsew", pady=8)
        box.insert("1.0", text)
        box.config(state="disabled")
        controls = ttk.Frame(tab)
        controls.grid(row=2, column=0, sticky="ew")
        for label in buttons:
            ttk.Button(controls, text=label, command=self._disabled_notice_factory(label)).pack(side="left", padx=(0, 8))
        tab.rowconfigure(1, weight=1)
        tab.columnconfigure(0, weight=1)

    def _labeled_text(self, parent: ttk.Frame, label: str, row: int, col: int) -> ScrolledText:
        container = ttk.Frame(parent)
        container.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 8 if col == 0 else 0), pady=6)
        ttk.Label(container, text=label).pack(anchor="w")
        box = ScrolledText(container, height=5, wrap="word")
        box.pack(fill="both", expand=True)
        parent.rowconfigure(row, weight=1)
        return box

    def _tree(self, parent: ttk.Frame, columns: list[str], row: int = 0, pack: bool = False) -> ttk.Treeview:
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=14)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, minwidth=90, stretch=True)
        yscroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        if pack:
            tree.pack(fill="both", expand=True)
            xscroll.pack(fill="x")
            yscroll.pack(side="right", fill="y")
        else:
            tree.grid(row=row, column=0, sticky="nsew")
            yscroll.grid(row=row, column=1, sticky="ns")
            xscroll.grid(row=row + 1, column=0, sticky="ew")
        return tree

    def _fill_tree(self, tree: ttk.Treeview, rows: list[dict]) -> None:
        for item in tree.get_children():
            tree.delete(item)
        columns = list(tree["columns"])
        for row in rows:
            tree.insert("", "end", values=[self._short(row.get(col, "")) for col in columns])

    def _short(self, value: object, limit: int = 120) -> str:
        text = "" if value is None else str(value)
        return text if len(text) <= limit else text[: limit - 3] + "..."

    def _set_text(self, widget: ScrolledText, text: str) -> None:
        widget.delete("1.0", "end")
        widget.insert("1.0", text)

    def _report(self, message: str) -> None:
        if hasattr(self, "report_status"):
            self.report_status.insert("end", message + "\n")
            self.report_status.see("end")


def main() -> None:
    root = Tk()
    KnowledgePrismApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
