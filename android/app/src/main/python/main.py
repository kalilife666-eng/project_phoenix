# Copyright project_phoenix
"""
project_phoenix
Authoritative Canadian Charter Analysis Engine
"""

import os
import threading
import tkinter as tk
import webbrowser
import urllib.parse
from datetime import datetime
from tkinter import ttk, filedialog, messagebox, scrolledtext

from ai_integration import AIIntegration
from canlii_client import CanLIIClient, CriminalLawNotebookClient
from charter_analyzer import CharterAnalyzer
# Local modules
from config import (
    OAKS_TEST, CANLII_API_KEY, APP_TITLE,
    APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT
)
from document_processor import DocumentProcessor
from legal_dictionary import (
    LEGAL_DICTIONARY, TERMINOLOGY_RULES, DEFLECTION_PATTERNS
)
from report_generator import ReportGenerator

# ─── Color Scheme ──────────────────────────────────────────────────────────────
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_medium": "#16213e",
    "bg_light": "#0f3460",
    "accent": "#e94560",
    "accent2": "#533483",
    "text_primary": "#eaeaea",
    "text_secondary": "#a0a0b0",
    "text_highlight": "#ffd700",
    "success": "#00c853",
    "warning": "#ff9800",
    "danger": "#e53935",
    "info": "#2196f3",
    "panel_bg": "#1e1e3a",
    "card_bg": "#252547",
    "input_bg": "#2a2a4a",
    "green_light": "#4caf50",
    "orange_light": "#ff9800",
    "red_light": "#ef5350",
}


def _about_dialog():
    messagebox.showinfo("About",
        f"🛡️ project_phoenix\n"
        f"Version {APP_VERSION}\n\n"
        f"RESEARCH AND STATISTICS TOOL ONLY\n\n"
        f"project_phoenix is designed for legal research and statistical\n"
        f"identification of potential Charter\n"
        f"indicators. It does NOT constitute legal advice.\n\n"
        f"All results must be verified by a qualified professional."
    )


class LegalAnalyzerApp:
    """Main application class for the project_phoenix GUI."""

    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} v{APP_VERSION}")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(1200, 750)

        # Core objects
        self.doc_processor = DocumentProcessor()
        self.charter_analyzer = CharterAnalyzer()
        self.report_generator = ReportGenerator()
        self.ai = AIIntegration()

        # State
        self.document_text = ""
        self.document_metadata = {}
        self.analysis_results = {}
        self.terminology_issues = []
        self.deflection_issues = []
        self.ai_results = {}

        # Disclaimer Label
        disclaimer_frame = tk.Frame(self.root, bg=COLORS["danger"])
        disclaimer_frame.pack(side="top", fill="x")
        tk.Label(disclaimer_frame, text="RESEARCH AND STATISTICS TOOL ONLY — NOT LEGAL ADVICE — VERIFY ALL RESULTS", 
                 bg=COLORS["danger"], fg="white", font=("Helvetica", 10, "bold"), pady=5).pack()

        # Build UI tabs
        self.notebook = ttk.Notebook(self.root)

    def _build_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # General
        self.style.configure(".", background=COLORS["bg_dark"], foreground=COLORS["text_primary"],
                              fieldbackground=COLORS["input_bg"], borderwidth=0)
        self.style.configure("TFrame", background=COLORS["bg_dark"])
        self.style.configure("TLabel", background=COLORS["bg_dark"], foreground=COLORS["text_primary"],
                              font=("Segoe UI", 10))
        self.style.configure("TButton", background=COLORS["accent"], foreground="white",
                              font=("Segoe UI", 10, "bold"), padding=(12, 6))
        self.style.map("TButton",
                        background=[("active", COLORS["accent2"]), ("pressed", COLORS["bg_light"])])
        self.style.configure("Accent.TButton", background=COLORS["info"], foreground="white")
        self.style.configure("Success.TButton", background=COLORS["success"], foreground="white")
        self.style.configure("Danger.TButton", background=COLORS["danger"], foreground="white")
        self.style.configure("Warning.TButton", background=COLORS["warning"], foreground="black")

        # Notebook tabs
        self.style.configure("TNotebook", background=COLORS["bg_dark"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=COLORS["bg_medium"],
                              foreground=COLORS["text_primary"], padding=[16, 8],
                              font=("Segoe UI", 10, "bold"))
        self.style.map("TNotebook.Tab",
                        background=[("selected", COLORS["accent"])],
                        foreground=[("selected", "white")])

        # Treeview
        self.style.configure("Treeview", background=COLORS["card_bg"],
                              foreground=COLORS["text_primary"],
                              fieldbackground=COLORS["card_bg"],
                              font=("Segoe UI", 9), rowheight=28)
        self.style.configure("Treeview.Heading", background=COLORS["bg_medium"],
                              foreground=COLORS["text_highlight"],
                              font=("Segoe UI", 9, "bold"))
        self.style.map("Treeview", background=[("selected", COLORS["accent2"])])

        # Entry / combobox
        self.style.configure("TEntry", fieldbackground=COLORS["input_bg"],
                              foreground=COLORS["text_primary"])
        self.style.configure("TCombobox", fieldbackground=COLORS["input_bg"],
                              foreground=COLORS["text_primary"])

        # Labels
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"),
                              foreground=COLORS["text_highlight"])
        self.style.configure("Subheader.TLabel", font=("Segoe UI", 11, "bold"),
                              foreground=COLORS["accent"])
        self.style.configure("Info.TLabel", foreground=COLORS["info"])
        self.style.configure("Success.TLabel", foreground=COLORS["success"])
        self.style.configure("Warning.TLabel", foreground=COLORS["warning"])
        self.style.configure("Danger.TLabel", foreground=COLORS["danger"])

        # Labelframe
        self.style.configure("TLabelframe", background=COLORS["bg_dark"],
                              foreground=COLORS["accent"])
        self.style.configure("TLabelframe.Label", background=COLORS["bg_dark"],
                              foreground=COLORS["accent"], font=("Segoe UI", 10, "bold"))

        # Progress bar
        self.style.configure("TProgressbar", background=COLORS["accent"],
                              troughcolor=COLORS["input_bg"])

    # ─── UI Construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Menu Bar ──
        menubar = tk.Menu(self.root, bg=COLORS["bg_medium"], fg=COLORS["text_primary"],
                           activebackground=COLORS["accent"], activeforeground="white")
        file_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["card_bg"], fg=COLORS["text_primary"])
        file_menu.add_command(label="Open Document...", command=self._open_document)
        file_menu.add_command(label="Paste Text...", command=self._paste_text)
        file_menu.add_separator()
        file_menu.add_command(label="Export HTML Report...", command=self._export_html)
        file_menu.add_command(label="Export Text Report...", command=self._export_txt)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["card_bg"], fg=COLORS["text_primary"])
        tools_menu.add_command(label="CanLII Search...", command=self._canlii_search_dialog)
        tools_menu.add_command(label="Criminal Law Notebook...", command=self._cln_browse)
        tools_menu.add_command(label="Legal Dictionary Lookup...", command=self._dict_lookup_dialog)
        tools_menu.add_separator()
        tools_menu.add_command(label="AI Ask a Question...", command=self._ai_question_dialog)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        settings_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["card_bg"], fg=COLORS["text_primary"])
        settings_menu.add_command(label="API Keys...", command=self._settings_dialog)
        menubar.add_cascade(label="Settings", menu=settings_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["card_bg"], fg=COLORS["text_primary"])
        help_menu.add_command(label="About", command=_about_dialog)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

        # ── Main Paned Layout ──
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Left panel — navigation & controls
        left_frame = ttk.Frame(main_pane, width=280)
        main_pane.add(left_frame, weight=0)

        # Right panel — content tabs
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=1)

        self._build_left_panel(left_frame)
        self._build_right_panel(right_frame)

        # Status bar
        self.status_var = tk.StringVar(value="Ready — No document loaded")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN,
                                anchor=tk.W, font=("Segoe UI", 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=2, pady=2)

    def _build_left_panel(self, parent):
        # ── Logo / Title ──
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, padx=8, pady=(8, 4))
        ttk.Label(title_frame, text="⚖️ Legal Document", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(title_frame, text="   Analyzer", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(title_frame, text=f"   v{APP_VERSION}", foreground=COLORS["text_secondary"]).pack(anchor=tk.W)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=8, pady=6)

        # ── Document Load ──
        load_frame = ttk.LabelFrame(parent, text="📂 Document", padding=8)
        load_frame.pack(fill=tk.X, padx=8, pady=4)

        ttk.Button(load_frame, text="Open File", command=self._open_document).pack(fill=tk.X, pady=2)
        ttk.Button(load_frame, text="Paste Text", command=self._paste_text).pack(fill=tk.X, pady=2)

        self.doc_info_label = ttk.Label(load_frame, text="No document loaded", foreground=COLORS["text_secondary"])
        self.doc_info_label.pack(anchor=tk.W, pady=(6, 0))

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=8, pady=6)

        # ── Analysis Controls ──
        analysis_frame = ttk.LabelFrame(parent, text="🔍 Analysis", padding=8)
        analysis_frame.pack(fill=tk.X, padx=8, pady=4)

        ttk.Button(analysis_frame, text="▶ Run Full Analysis",
                    command=self._run_full_analysis, style="Success.TButton").pack(fill=tk.X, pady=2)
        ttk.Button(analysis_frame, text="⚖️ Charter Breach Only",
                    command=self._run_charter_only).pack(fill=tk.X, pady=2)
        ttk.Button(analysis_frame, text="🧭 Human Rights Only",
                    command=self._run_human_rights_only).pack(fill=tk.X, pady=2)
        ttk.Button(analysis_frame, text="📖 Dictionary & Terminology",
                    command=self._run_terminology).pack(fill=tk.X, pady=2)
        ttk.Button(analysis_frame, text="🚫 Deflection / Ambiguity",
                    command=self._run_deflection).pack(fill=tk.X, pady=2)
        ttk.Button(analysis_frame, text="🤖 AI Verify Analysis",
                    command=self._run_ai_verify, style="Accent.TButton").pack(fill=tk.X, pady=2)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=8, pady=6)

        # ── Cross-References ──
        xref_frame = ttk.LabelFrame(parent, text="📚 Cross-References", padding=8)
        xref_frame.pack(fill=tk.X, padx=8, pady=4)

        ttk.Button(xref_frame, text="🔍 CanLII Search",
                    command=self._canlii_search_dialog).pack(fill=tk.X, pady=2)
        ttk.Button(xref_frame, text="📕 Criminal Law Notebook",
                    command=self._cln_browse).pack(fill=tk.X, pady=2)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=8, pady=6)

        # ── Export ──
        export_frame = ttk.LabelFrame(parent, text="📄 Export", padding=8)
        export_frame.pack(fill=tk.X, padx=8, pady=4)

        ttk.Button(export_frame, text="📥 HTML Report",
                    command=self._export_html).pack(fill=tk.X, pady=2)
        ttk.Button(export_frame, text="📥 Text Report",
                    command=self._export_txt).pack(fill=tk.X, pady=2)

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=8, pady=6)

        # ── Quick Dictionary Lookup ──
        dict_frame = ttk.LabelFrame(parent, text="📖 Quick Lookup", padding=8)
        dict_frame.pack(fill=tk.X, padx=8, pady=4)

        self.dict_entry_var = tk.StringVar()
        dict_entry = ttk.Entry(dict_frame, textvariable=self.dict_entry_var)
        dict_entry.pack(fill=tk.X, pady=2)
        dict_entry.bind("<Return>", lambda e: self._quick_dict_lookup())

        ttk.Button(dict_frame, text="Look Up", command=self._quick_dict_lookup).pack(fill=tk.X, pady=2)

        self.dict_result_label = ttk.Label(dict_frame, text="", wraplength=240,
                                             foreground=COLORS["info"], font=("Segoe UI", 9))
        self.dict_result_label.pack(anchor=tk.W, pady=4)

        # ── Progress ──
        self.progress = ttk.Progressbar(parent, orient=tk.HORIZONTAL, mode="determinate", length=250)
        self.progress.pack(fill=tk.X, padx=8, pady=(8, 4))

    def _build_right_panel(self, parent):
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Tab 1: Document View
        self.doc_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.doc_tab, text="  📄 Document  ")
        self._build_document_tab(self.doc_tab)

        # Tab 2: Charter Analysis
        self.charter_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.charter_tab, text="  ⚖️ Charter Analysis  ")
        self._build_charter_tab(self.charter_tab)

        # Tab 3: Terminology
        self.human_rights_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.human_rights_tab, text="  🧭 Human Rights  ")
        self._build_human_rights_tab(self.human_rights_tab)

        # Tab 4: Terminology
        self.term_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.term_tab, text="  📖 Terminology  ")
        self._build_terminology_tab(self.term_tab)

        # Tab 5: Deflection / Ambiguity
        self.deflection_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.deflection_tab, text="  🚫 Deflection  ")
        self._build_deflection_tab(self.deflection_tab)

        # Tab 6: Cross-References
        self.xref_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.xref_tab, text="  📚 Cross-References  ")
        self._build_xref_tab(self.xref_tab)

        # Tab 7: AI Analysis
        self.ai_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.ai_tab, text="  🤖 AI Analysis  ")
        self._build_ai_tab(self.ai_tab)

        # Tab 8: Dictionary
        self.dict_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.dict_tab, text="  📕 Dictionary  ")
        self._build_dictionary_tab(self.dict_tab)

    # ── Document Tab ──────────────────────────────────────────────────────────

    def _build_document_tab(self, parent):
        # Document text viewer
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, padx=8, pady=(8, 0))
        ttk.Label(header, text="Document Viewer", style="Subheader.TLabel").pack(side=tk.LEFT)

        self.doc_text = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, font=("Consolas", 11),
            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
            insertbackground="white", selectbackground=COLORS["accent2"],
            relief=tk.FLAT, borderwidth=2
        )
        self.doc_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Highlight tags
        self.doc_text.tag_configure("charter_ref", foreground=COLORS["text_highlight"],
                                     background=COLORS["accent2"], font=("Consolas", 11, "bold"))
        self.doc_text.tag_configure("breach_indicator", foreground=COLORS["danger"],
                                     underline=True)
        self.doc_text.tag_configure("deflection", foreground=COLORS["warning"],
                                     background="#4a3000")
        self.doc_text.tag_configure("term_issue", foreground=COLORS["orange_light"],
                                     underline=True)

    # ── Charter Analysis Tab ──────────────────────────────────────────────────

    def _build_charter_tab(self, parent):
        # Top: Summary
        top = ttk.Frame(parent)
        top.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(top, text="Charter Breach Analysis", style="Subheader.TLabel").pack(side=tk.LEFT)

        self.charter_summary_label = ttk.Label(top, text="Run analysis to view results.",
                                                 foreground=COLORS["text_secondary"])
        self.charter_summary_label.pack(side=tk.RIGHT)

        # Breach list (Treeview)
        breach_frame = ttk.LabelFrame(parent, text="Potential Breaches", padding=6)
        breach_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        cols = ("section", "title", "confidence", "keywords", "indicators")
        self.breach_tree = ttk.Treeview(breach_frame, columns=cols, show="headings", height=6)
        self.breach_tree.heading("section", text="Section")
        self.breach_tree.heading("title", text="Title")
        self.breach_tree.heading("confidence", text="Confidence")
        self.breach_tree.heading("keywords", text="Keywords")
        self.breach_tree.heading("indicators", text="Indicators")
        self.breach_tree.column("section", width=70, anchor=tk.CENTER)
        self.breach_tree.column("title", width=200)
        self.breach_tree.column("confidence", width=80, anchor=tk.CENTER)
        self.breach_tree.column("keywords", width=200)
        self.breach_tree.column("indicators", width=200)
        self.breach_tree.pack(fill=tk.BOTH, expand=True)
        self.breach_tree.bind("<<TreeviewSelect>>", self._on_breach_select)

        # Detail pane
        detail_frame = ttk.LabelFrame(parent, text="Breath Detail & Legal Tests", padding=6)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.breach_detail_text = scrolledtext.ScrolledText(
            detail_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
            insertbackground="white", relief=tk.FLAT, height=12
        )
        self.breach_detail_text.pack(fill=tk.BOTH, expand=True)

        # Oakes section
        oakes_frame = ttk.LabelFrame(parent, text="Section 1 — Oakes Test", padding=6)
        oakes_frame.pack(fill=tk.X, padx=8, pady=(4, 8))

        self.oakes_text = scrolledtext.ScrolledText(
            oakes_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
            relief=tk.FLAT, height=8
        )
        self.oakes_text.pack(fill=tk.BOTH, expand=True)

    # ── Human Rights Tab ─────────────────────────────────────────────────────

    def _build_human_rights_tab(self, parent):
        top = ttk.Frame(parent)
        top.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(top, text="Human Rights Comparison (UN / Federal / Provincial)",
                  style="Subheader.TLabel").pack(side=tk.LEFT)
        self.human_rights_summary_label = ttk.Label(
            top, text="Run analysis to view results.", foreground=COLORS["text_secondary"]
        )
        self.human_rights_summary_label.pack(side=tk.RIGHT)

        findings_frame = ttk.LabelFrame(parent, text="Findings", padding=6)
        findings_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        cols = ("criterion", "summary", "layers", "cases")
        self.human_rights_tree = ttk.Treeview(findings_frame, columns=cols, show="headings", height=8)
        self.human_rights_tree.heading("criterion", text="Criterion")
        self.human_rights_tree.heading("summary", text="Summary")
        self.human_rights_tree.heading("layers", text="Framework Layers")
        self.human_rights_tree.heading("cases", text="Cases")
        self.human_rights_tree.column("criterion", width=230)
        self.human_rights_tree.column("summary", width=360)
        self.human_rights_tree.column("layers", width=300)
        self.human_rights_tree.column("cases", width=280)
        self.human_rights_tree.pack(fill=tk.BOTH, expand=True)
        self.human_rights_tree.bind("<<TreeviewSelect>>", self._on_human_rights_select)

        detail_frame = ttk.LabelFrame(parent, text="Assessment Detail", padding=6)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))

        self.human_rights_text = scrolledtext.ScrolledText(
            detail_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
            relief=tk.FLAT, height=10
        )
        self.human_rights_text.pack(fill=tk.BOTH, expand=True)

    # ── Terminology Tab ───────────────────────────────────────────────────────

    def _build_terminology_tab(self, parent):
        ttk.Label(parent, text="Terminology & Consistency Check", style="Subheader.TLabel").pack(
            anchor=tk.W, padx=8, pady=(8, 4))

        # Issues tree
        term_frame = ttk.LabelFrame(parent, text="Terminology Issues Found", padding=6)
        term_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        cols = ("term", "type", "issue", "correct_form", "source")
        self.term_tree = ttk.Treeview(term_frame, columns=cols, show="headings", height=12)
        self.term_tree.heading("term", text="Term / Phrase")
        self.term_tree.heading("type", text="Type")
        self.term_tree.heading("issue", text="Issue")
        self.term_tree.heading("correct_form", text="Correct Form")
        self.term_tree.heading("source", text="Source")
        self.term_tree.column("term", width=180)
        self.term_tree.column("type", width=100)
        self.term_tree.column("issue", width=250)
        self.term_tree.column("correct_form", width=180)
        self.term_tree.column("source", width=200)
        self.term_tree.pack(fill=tk.BOTH, expand=True)
        self.term_tree.bind("<<TreeviewSelect>>", self._on_term_select)

        # Detail
        self.term_detail_text = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, font=("Consolas", 10),
            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
            relief=tk.FLAT, height=8
        )
        self.term_detail_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

    # ── Deflection Tab ────────────────────────────────────────────────────────

    def _build_deflection_tab(self, parent):
        ttk.Label(parent, text="Deflection & Ambiguity Detection", style="Subheader.TLabel").pack(
            anchor=tk.W, padx=8, pady=(8, 4))

        defl_frame = ttk.LabelFrame(parent, text="Detected Issues", padding=6)
        defl_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        cols = ("pattern_type", "severity", "count", "description", "suggestion")
        self.defl_tree = ttk.Treeview(defl_frame, columns=cols, show="headings", height=10)
        self.defl_tree.heading("pattern_type", text="Pattern Type")
        self.defl_tree.heading("severity", text="Severity")
        self.defl_tree.heading("count", text="Count")
        self.defl_tree.heading("description", text="Description")
        self.defl_tree.heading("suggestion", text="Suggestion")
        self.defl_tree.column("pattern_type", width=150)
        self.defl_tree.column("severity", width=70, anchor=tk.CENTER)
        self.defl_tree.column("count", width=60, anchor=tk.CENTER)
        self.defl_tree.column("description", width=350)
        self.defl_tree.column("suggestion", width=300)
        self.defl_tree.pack(fill=tk.BOTH, expand=True)

        self.defl_detail_text = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, font=("Consolas", 10),
            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
            relief=tk.FLAT, height=8
        )
        self.defl_detail_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

    # ── Cross-References Tab ──────────────────────────────────────────────────

    def _build_xref_tab(self, parent):
        ttk.Label(parent, text="Cross-References (CanLII & Criminal Law Notebook)",
                   style="Subheader.TLabel").pack(anchor=tk.W, padx=8, pady=(8, 4))

        # CanLII section
        canlii_frame = ttk.LabelFrame(parent, text="CanLII — Case Law Search", padding=6)
        canlii_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.xref_canlii_text = scrolledtext.ScrolledText(
            canlii_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
            relief=tk.FLAT, height=10
        )
        self.xref_canlii_text.pack(fill=tk.BOTH, expand=True)

        # CLN section
        cln_frame = ttk.LabelFrame(parent, text="Criminal Law Notebook", padding=6)
        cln_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.xref_cln_text = scrolledtext.ScrolledText(
            cln_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
            relief=tk.FLAT, height=10
        )
        self.xref_cln_text.pack(fill=tk.BOTH, expand=True)

    # ── AI Tab ────────────────────────────────────────────────────────────────

    def _build_ai_tab(self, parent):
        ttk.Label(parent, text="AI-Powered Verification & Analysis", style="Subheader.TLabel").pack(
            anchor=tk.W, padx=8, pady=(8, 4))

        # AI status
        self.ai_status_label = ttk.Label(parent, text="AI: Not configured",
                                           foreground=COLORS["warning"])
        self.ai_status_label.pack(anchor=tk.W, padx=8, pady=2)

        # AI controls
        ai_ctrl = ttk.Frame(parent)
        ai_ctrl.pack(fill=tk.X, padx=8, pady=4)

        ttk.Button(ai_ctrl, text="Verify Charter Analysis",
                    command=lambda: self._ai_verify_specific("charter"),
                    style="Accent.TButton").pack(side=tk.LEFT, padx=4)
        ttk.Button(ai_ctrl, text="Verify Terminology",
                    command=lambda: self._ai_verify_specific("terms"),
                    style="Accent.TButton").pack(side=tk.LEFT, padx=4)
        ttk.Button(ai_ctrl, text="Detect Deflection",
                    command=lambda: self._ai_verify_specific("deflection"),
                    style="Accent.TButton").pack(side=tk.LEFT, padx=4)
        ttk.Button(ai_ctrl, text="Validate Cross-Refs",
                    command=lambda: self._ai_verify_specific("crossref"),
                    style="Accent.TButton").pack(side=tk.LEFT, padx=4)
        ttk.Button(ai_ctrl, text="Executive Summary",
                    command=lambda: self._ai_verify_specific("summary"),
                    style="Accent.TButton").pack(side=tk.LEFT, padx=4)

        # AI output
        self.ai_output = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, font=("Consolas", 10),
            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
            insertbackground="white", relief=tk.FLAT
        )
        self.ai_output.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Ask AI
        ask_frame = ttk.Frame(parent)
        ask_frame.pack(fill=tk.X, padx=8, pady=(4, 8))

        self.ai_ask_var = tk.StringVar()
        ai_entry = ttk.Entry(ask_frame, textvariable=self.ai_ask_var, font=("Segoe UI", 10))
        ai_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        ai_entry.bind("<Return>", lambda e: self._ai_ask())
        ttk.Button(ask_frame, text="Ask AI", command=self._ai_ask,
                    style="Accent.TButton").pack(side=tk.RIGHT)

    # ── Dictionary Tab ────────────────────────────────────────────────────────

    def _build_dictionary_tab(self, parent):
        ttk.Label(parent, text="Canadian Legal Dictionary", style="Subheader.TLabel").pack(
            anchor=tk.W, padx=8, pady=(8, 4))

        # Search bar
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.dict_search_var = tk.StringVar()
        dict_search = ttk.Entry(search_frame, textvariable=self.dict_search_var, width=40,
                                 font=("Segoe UI", 10))
        dict_search.pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        dict_search.bind("<Return>", lambda e: self._search_dictionary())

        ttk.Button(search_frame, text="Search", command=self._search_dictionary).pack(side=tk.LEFT, padx=4)

        # Category filter
        ttk.Label(search_frame, text="Category:").pack(side=tk.LEFT, padx=(8, 2))
        self.dict_cat_var = tk.StringVar(value="All")
        cat_combo = ttk.Combobox(search_frame, textvariable=self.dict_cat_var, width=18,
                                  values=["All"] + sorted(set(v["category"] for v in LEGAL_DICTIONARY.values())),
                                  state="readonly")
        cat_combo.pack(side=tk.LEFT, padx=4)

        # Dictionary list
        dict_list_frame = ttk.Frame(parent)
        dict_list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        cols = ("term", "category", "preferred_form", "source")
        self.dict_tree = ttk.Treeview(dict_list_frame, columns=cols, show="headings", height=10)
        self.dict_tree.heading("term", text="Term")
        self.dict_tree.heading("category", text="Category")
        self.dict_tree.heading("preferred_form", text="Preferred Form")
        self.dict_tree.heading("source", text="Source")
        self.dict_tree.column("term", width=200)
        self.dict_tree.column("category", width=130)
        self.dict_tree.column("preferred_form", width=200)
        self.dict_tree.column("source", width=250)
        self.dict_tree.pack(fill=tk.BOTH, expand=True)
        self.dict_tree.bind("<<TreeviewSelect>>", self._on_dict_select)

        # Definition display
        self.dict_def_text = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, font=("Consolas", 10),
            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
            relief=tk.FLAT, height=10
        )
        self.dict_def_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Initial populate
        self._populate_dictionary_tree()

    # ══════════════════════════════════════════════════════════════════════════
    # FILE OPERATIONS
    # ══════════════════════════════════════════════════════════════════════════

    def _open_document(self):
        filetypes = [
            ("All Supported", "*.pdf;*.docx;*.txt;*.md;*.rtf"),
            ("PDF Files", "*.pdf"),
            ("Word Documents", "*.docx"),
            ("Text Files", "*.txt;*.md;*.rtf"),
        ]
        path = filedialog.askopenfilename(title="Open Legal Document", filetypes=filetypes)
        if not path:
            return

        self.status_var.set(f"Loading document: {os.path.basename(path)}...")
        self.root.update_idletasks()

        try:
            result = self.doc_processor.load_document(path)
            self.document_text = result["text"]
            self.document_metadata = result["metadata"]
            self.doc_text.delete("1.0", tk.END)
            self.doc_text.insert("1.0", self.document_text)

            meta = self.document_metadata
            self.doc_info_label.config(
                text=f"📄 {meta['file_name']}\n   {meta['word_count']:,} words | {meta['paragraph_count']} paragraphs"
            )
            self.status_var.set(f"Loaded: {meta['file_name']} — {meta['word_count']:,} words")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load document:\n{e}")
            self.status_var.set("Error loading document")

    def _paste_text(self):
        """Open a dialog to paste text directly."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Paste Document Text")
        dlg.geometry("800x500")
        dlg.transient(self.root)
        dlg.grab_set()

        ttk.Label(dlg, text="Paste your legal document text below:", style="Subheader.TLabel").pack(
            padx=10, pady=8)

        text_area = scrolledtext.ScrolledText(dlg, wrap=tk.WORD, font=("Consolas", 11),
                                              bg=COLORS["input_bg"], fg=COLORS["text_primary"],
                                              insertbackground="white", relief=tk.FLAT)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        name_var = tk.StringVar(value="pasted_document")
        name_frame = ttk.Frame(dlg)
        name_frame.pack(fill=tk.X, padx=10, pady=4)
        ttk.Label(name_frame, text="Document name:").pack(side=tk.LEFT)
        ttk.Entry(name_frame, textvariable=name_var, width=40).pack(side=tk.LEFT, padx=4)

        def _confirm():
            content = text_area.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("Empty", "Please paste some text.", parent=dlg)
                return
            self.document_text = content
            self.document_metadata = {
                "file_name": name_var.get(),
                "format": ".txt",
                "char_count": len(content),
                "word_count": len(content.split()),
                "paragraph_count": len([p for p in content.split("\n\n") if p.strip()]),
                "sentence_count": 0,
            }
            self.doc_text.delete("1.0", tk.END)
            self.doc_text.insert("1.0", content)
            meta = self.document_metadata
            self.doc_info_label.config(
                text=f"📄 {meta['file_name']}\n   {meta['word_count']:,} words | {meta['paragraph_count']} paragraphs"
            )
            self.status_var.set(f"Loaded pasted document — {meta['word_count']:,} words")
            dlg.destroy()

        ttk.Button(dlg, text="Load Document", command=_confirm, style="Success.TButton").pack(pady=8)

    # ══════════════════════════════════════════════════════════════════════════
    # ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════

    def _check_document_loaded(self):
        if not self.document_text.strip():
            messagebox.showwarning("No Document", "Please load a document first (File → Open or Paste Text).")
            return False
        return True

    def _run_full_analysis(self):
        if not self._check_document_loaded():
            return

        self.status_var.set("Running full analysis...")
        self.progress["value"] = 0
        self.root.update_idletasks()

        # Charter analysis
        self.progress["value"] = 15
        self.analysis_results = self.charter_analyzer.analyze_document(self.document_text)
        self._populate_charter_tab()
        self._populate_human_rights_tab()
        self.root.update_idletasks()

        # Terminology
        self.progress["value"] = 40
        self._do_terminology_analysis()
        self.root.update_idletasks()

        # Deflection
        self.progress["value"] = 60
        self._do_deflection_analysis()
        self.root.update_idletasks()

        # Cross-references
        self.progress["value"] = 80
        self._populate_xref_tab()
        self.root.update_idletasks()

        # Highlight document
        self._highlight_document()

        self.progress["value"] = 100
        self.status_var.set("Full analysis complete.")
        messagebox.showinfo("Analysis Complete", "Full document analysis is complete.\nReview all tabs for results.")

    def _run_charter_only(self):
        if not self._check_document_loaded():
            return
        self.status_var.set("Running Charter breach analysis...")
        self.progress["value"] = 0
        self.root.update_idletasks()

        self.analysis_results = self.charter_analyzer.analyze_document(self.document_text)
        self._populate_charter_tab()
        self._populate_human_rights_tab()
        self._populate_xref_tab()

        self.progress["value"] = 100
        self.status_var.set("Charter analysis complete.")

    def _run_human_rights_only(self):
        if not self._check_document_loaded():
            return
        self.status_var.set("Running Human Rights analysis...")
        self.progress["value"] = 0
        self.root.update_idletasks()

        self.analysis_results = self.charter_analyzer.analyze_document(self.document_text)
        self._populate_human_rights_tab()

        self.progress["value"] = 100
        self.status_var.set("Human Rights analysis complete.")

    def _run_terminology(self):
        if not self._check_document_loaded():
            return
        self._do_terminology_analysis()
        self.status_var.set("Terminology analysis complete.")

    def _run_deflection(self):
        if not self._check_document_loaded():
            return
        self._do_deflection_analysis()
        self.status_var.set("Deflection analysis complete.")

    def _do_terminology_analysis(self):
        """Run terminology and consistency analysis."""
        self.terminology_issues = []
        text = self.document_text
        text_lower = text.lower()

        # Check dictionary misuses
        for term_key, term_data in LEGAL_DICTIONARY.items():
            for misuse in term_data.get("misuses", []):
                if misuse.lower() in text_lower:
                    self.terminology_issues.append({
                        "term": misuse,
                        "type": "misuse",
                        "issue": f"'{misuse}' is not the correct Canadian legal term",
                        "correct_form": term_data["preferred_form"],
                        "source": term_data.get("source", "Legal Dictionary"),
                        "definition": term_data["definition"],
                        "category": term_data["category"],
                    })

        # Check terminology rules
        for rule_key, rule_data in TERMINOLOGY_RULES.items():
            for incorrect in rule_data.get("incorrect", []):
                count = text_lower.count(incorrect.lower())
                if count > 0:
                    self.terminology_issues.append({
                        "term": incorrect,
                        "type": "spelling/format",
                        "issue": f"Incorrect form — {rule_data.get('note', '')}",
                        "correct_form": rule_data["correct"],
                        "source": "Terminology Standards",
                        "definition": rule_data.get("note", ""),
                        "category": "consistency",
                    })

        # Check for American vs Canadian terms
        american_to_canadian = {
            "probable cause": "reasonable grounds",
            "due process": "duty of fairness / principles of fundamental justice",
            "defense (noun)": "defence",
            "offense": "offence",
            "suppression of evidence": "exclusion of evidence",
            "miranda rights": "right to counsel (s.10(b) Charter)",
            "prosecutor (in preference to Crown)": "the Crown",
            "district attorney": "Crown counsel / Crown attorney",
            "grand jury": "preliminary inquiry",
            "beyond shadow of a doubt": "beyond a reasonable doubt",
            "fruit of the poisonous tree": "derivative evidence",
        }
        for american, canadian in american_to_canadian.items():
            if american.lower() in text_lower:
                self.terminology_issues.append({
                    "term": american,
                    "type": "americanism",
                    "issue": f"American legal term — use Canadian equivalent",
                    "correct_form": canadian,
                    "source": "Canadian Legal Usage",
                    "definition": f"The Canadian equivalent is '{canadian}'.",
                    "category": "consistency",
                })

        # Populate tree
        self._populate_term_tree()

    def _do_deflection_analysis(self):
        """Run deflection and ambiguity pattern analysis."""
        import re
        self.deflection_issues = []
        text = self.document_text

        for pattern_name, pattern_data in DEFLECTION_PATTERNS.items():
            total_count = 0
            matches_detail = []
            for pat in pattern_data["patterns"]:
                matches = list(re.finditer(pat, text, re.IGNORECASE))
                count = len(matches)
                total_count += count
                for m in matches:
                    matches_detail.append(m.group(0))

            if total_count > 0:
                self.deflection_issues.append({
                    "pattern_type": pattern_name.replace("_", " ").title(),
                    "severity": pattern_data["severity"],
                    "count": total_count,
                    "description": pattern_data["description"],
                    "suggestion": pattern_data["suggestion"],
                    "matches": matches_detail[:10],
                })

        self._populate_defl_tree()

    # ── Populate UI Components ────────────────────────────────────────────────

    def _populate_charter_tab(self):
        # Clear
        for item in self.breach_tree.get_children():
            self.breach_tree.delete(item)
        self.breach_detail_text.delete("1.0", tk.END)
        self.oakes_text.delete("1.0", tk.END)

        breaches = self.analysis_results.get("potential_breaches", [])

        if not breaches:
            self.charter_summary_label.config(text="No Charter breaches detected.", foreground=COLORS["success"])
            return

        high = sum(1 for b in breaches if b["confidence_level"] == "HIGH")
        med = sum(1 for b in breaches if b["confidence_level"] == "MEDIUM")
        low = sum(1 for b in breaches if b["confidence_level"] == "LOW")
        self.charter_summary_label.config(
            text=f"{len(breaches)} breaches: {high} high, {med} medium, {low} low",
            foreground=COLORS["danger"] if high > 0 else COLORS["warning"]
        )

        for breach in breaches:
            kw_str = ", ".join(k["keyword"] for k in breach.get("matched_keywords", [])[:4])
            ind_str = ", ".join(i["type"] for i in breach.get("breach_indicators", [])[:3])
            self.breach_tree.insert("", tk.END, values=(
                breach["section"],
                breach["title"],
                breach.get("confidence_level", "N/A"),
                kw_str,
                ind_str,
            ), tags=(breach.get("confidence_level", "").lower(),))

        self.breach_tree.tag_configure("high", foreground=COLORS["red_light"])
        self.breach_tree.tag_configure("medium", foreground=COLORS["orange_light"])
        self.breach_tree.tag_configure("low", foreground=COLORS["green_light"])

        # Oakes
        oakes = self.analysis_results.get("oakes_analysis")
        if oakes:
            self.oakes_text.insert(tk.END, f"OAKES TEST ANALYSIS\n{'='*50}\n\n")
            self.oakes_text.insert(tk.END, f"Summary: {oakes.get('analysis_summary', 'N/A')}\n\n")
            self.oakes_text.insert(tk.END, f"Justification Likely: {oakes.get('justification_likely', 'N/A')}\n\n")
            for step_id, step in oakes.get("steps", {}).items():
                self.oakes_text.insert(tk.END, f"Step: {step['question']}\n")
                self.oakes_text.insert(tk.END, f"  Analysis: {step.get('analysis', '')}\n\n")

    def _on_breach_select(self, event):
        sel = self.breach_tree.selection()
        if not sel:
            return

        vals = self.breach_tree.item(sel[0], "values")
        section = vals[0]

        # Find breach data
        breach = None
        for b in self.analysis_results.get("potential_breaches", []):
            if b["section"] == section:
                breach = b
                break

        self.breach_detail_text.delete("1.0", tk.END)
        if not breach:
            return

        self.breach_detail_text.insert(tk.END, f"SECTION {breach['section']} — {breach['title']}\n")
        self.breach_detail_text.insert(tk.END, f"{'='*60}\n\n")
        self.breach_detail_text.insert(tk.END, f"Description: {breach.get('description', '')}\n")
        self.breach_detail_text.insert(tk.END, f"Confidence: {breach.get('confidence_level', '')} ({int(breach.get('confidence',0)*100)}%)\n\n")

        self.breach_detail_text.insert(tk.END, "MATCHED KEYWORDS:\n")
        for kw in breach.get("matched_keywords", []):
            self.breach_detail_text.insert(tk.END, f"  • {kw['keyword']} ({kw['count']}x)\n")

        self.breach_detail_text.insert(tk.END, "\nBREACH INDICATORS:\n")
        for ind in breach.get("breach_indicators", []):
            self.breach_detail_text.insert(tk.END, f"  ⚠️ {ind['type']} ({ind['count']}x)\n")

        self.breach_detail_text.insert(tk.END, "\nLEGAL TESTS:\n")
        for test_id, test in breach.get("applicable_tests", {}).items():
            icon = "⚠️" if test["status"] == "potential_issue" else "✓"
            self.breach_detail_text.insert(tk.END, f"\n{icon} {test['question']}\n")
            self.breach_detail_text.insert(tk.END, f"   Status: {test['status'].replace('_',' ').title()}\n")
            if test.get("identified_issues"):
                self.breach_detail_text.insert(tk.END, f"   Issues: {', '.join(test['identified_issues'])}\n")

        # Remedies
        self.breach_detail_text.insert(tk.END, "\n\nREMEDIES:\n")
        for r in self.analysis_results.get("remedies", []):
            self.breach_detail_text.insert(tk.END, f"\n  💊 {r['description']}\n")
            if r.get("options"):
                for opt in r["options"]:
                    self.breach_detail_text.insert(tk.END, f"    — {opt}\n")

        self.breach_detail_text.insert(tk.END, "\n\nOFFICER MISCONDUCT (VERBATIM ASSESSMENT):\n")
        officer = self.analysis_results.get("officer_conduct_assessment")
        bad_faith = self.analysis_results.get("bad_faith_assessment")
        police_indicators = self.analysis_results.get("police_misconduct_indicators", [])

        if officer:
            self.breach_detail_text.insert(
                tk.END, f"\nSeriousness: {officer.get('seriousness', 'N/A')}\n"
            )
            self.breach_detail_text.insert(
                tk.END, f"Legal Basis: {officer.get('legal_basis', 'N/A')}\n"
            )
            self.breach_detail_text.insert(
                tk.END, f"Assessment: {officer.get('assessment', 'N/A')}\n"
            )
            findings = officer.get("findings", [])
            if findings:
                self.breach_detail_text.insert(tk.END, "Findings:\n")
                for finding in findings:
                    self.breach_detail_text.insert(tk.END, f"  • {finding}\n")

        if bad_faith:
            self.breach_detail_text.insert(
                tk.END, f"\nBad Faith Level: {bad_faith.get('level', 'N/A')} (Score {bad_faith.get('score', 0)})\n"
            )
            self.breach_detail_text.insert(
                tk.END, f"Bad Faith Legal Basis: {bad_faith.get('legal_basis', 'N/A')}\n"
            )
            self.breach_detail_text.insert(
                tk.END, f"Bad Faith Assessment: {bad_faith.get('assessment', 'N/A')}\n"
            )

        self.breach_detail_text.insert(tk.END, "\nCASE LAW / AUTHORITIES FOR THIS BREACH:\n")
        section = breach.get("section")

        canlii_for_section = (
            self.analysis_results.get("cross_references", {})
            .get("canlii", {})
            .get(section, {})
        )
        if canlii_for_section.get("search_urls"):
            for label, url in canlii_for_section["search_urls"].items():
                self.breach_detail_text.insert(tk.END, f"  • CanLII {label.title()}: {url}\n")

        cln_for_section = (
            self.analysis_results.get("cross_references", {})
            .get("criminallawnotebook", {})
            .get(section, {})
        )
        if cln_for_section.get("direct_reference"):
            self.breach_detail_text.insert(
                tk.END, f"  • Criminal Law Notebook: {cln_for_section['direct_reference']}\n"
            )

        matching_police_indicators = [
            p for p in police_indicators if f"Section {section}" in p.get("indicator", "")
        ]
        for indicator in matching_police_indicators:
            self.breach_detail_text.insert(
                tk.END,
                f"  • Misconduct Link ({indicator.get('severity', 'N/A')}): "
                f"{indicator.get('summary', '')}\n"
                f"    Source: {indicator.get('source', 'N/A')} | {indicator.get('url', '')}\n"
            )

    def _populate_term_tree(self):
        for item in self.term_tree.get_children():
            self.term_tree.delete(item)

        for issue in self.terminology_issues:
            tag = "danger" if issue["type"] == "americanism" else "warning" if issue["type"] == "misuse" else ""
            self.term_tree.insert("", tk.END, values=(
                issue["term"],
                issue["type"],
                issue["issue"][:60],
                issue["correct_form"],
                issue["source"][:40],
            ), tags=(tag,))

        self.term_tree.tag_configure("danger", foreground=COLORS["red_light"])
        self.term_tree.tag_configure("warning", foreground=COLORS["orange_light"])

    def _populate_human_rights_tab(self):
        for item in self.human_rights_tree.get_children():
            self.human_rights_tree.delete(item)
        self.human_rights_text.delete("1.0", tk.END)

        hr = self.analysis_results.get("human_rights_assessment", {})
        if not hr:
            self.human_rights_summary_label.config(
                text="No human-rights assessment available.",
                foreground=COLORS["text_secondary"]
            )
            return

        level = hr.get("level", "N/A")
        score = hr.get("score", 0)
        grounds = hr.get("protected_grounds", [])
        color = COLORS["danger"] if level == "HIGH" else COLORS["warning"] if level == "MEDIUM" else COLORS["success"]

        self.human_rights_summary_label.config(
            text=f"Risk {level} | Score {score} | Grounds: {len(grounds)}",
            foreground=color
        )

        findings = hr.get("findings", [])
        for finding in findings:
            self.human_rights_tree.insert("", tk.END, values=(
                finding.get("criterion", "N/A"),
                finding.get("summary", "")[:120],
                "; ".join(finding.get("layers", [])[:3]),
                "; ".join(finding.get("cases", [])[:2]),
            ))

        self.human_rights_text.insert(tk.END, "HUMAN RIGHTS ASSESSMENT\n")
        self.human_rights_text.insert(tk.END, f"{'='*60}\n\n")
        self.human_rights_text.insert(tk.END, f"Level: {level}\n")
        self.human_rights_text.insert(tk.END, f"Score: {score}\n")
        self.human_rights_text.insert(tk.END, f"Assessment: {hr.get('assessment', 'N/A')}\n\n")

        if grounds:
            self.human_rights_text.insert(tk.END, "Protected Grounds Detected:\n")
            for ground in grounds:
                self.human_rights_text.insert(tk.END, f"  • {ground}\n")
            self.human_rights_text.insert(tk.END, "\n")

        self.human_rights_text.insert(tk.END, "Framework Sources:\n")
        for source in hr.get("sources", []):
            self.human_rights_text.insert(
                tk.END, f"  • {source.get('layer', '')}: {source.get('title', '')}\n"
            )

    def _on_human_rights_select(self, event):
        sel = self.human_rights_tree.selection()
        if not sel:
            return

        criterion = self.human_rights_tree.item(sel[0], "values")[0]
        hr = self.analysis_results.get("human_rights_assessment", {})
        finding = None
        for entry in hr.get("findings", []):
            if entry.get("criterion") == criterion:
                finding = entry
                break
        if not finding:
            return

        self.human_rights_text.delete("1.0", tk.END)
        self.human_rights_text.insert(tk.END, f"{finding.get('criterion', 'Finding')}\n")
        self.human_rights_text.insert(tk.END, f"{'='*60}\n\n")
        self.human_rights_text.insert(tk.END, f"Summary:\n{finding.get('summary', '')}\n\n")
        self.human_rights_text.insert(tk.END, "Comparison Layers:\n")
        for layer in finding.get("layers", []):
            self.human_rights_text.insert(tk.END, f"  • {layer}\n")
        self.human_rights_text.insert(tk.END, "\nAuthorities / Cases:\n")
        for case in finding.get("cases", []):
            self.human_rights_text.insert(tk.END, f"  • {case}\n")

    def _on_term_select(self, event):
        sel = self.term_tree.selection()
        if not sel:
            return
        vals = self.term_tree.item(sel[0], "values")
        # Find matching issue
        for issue in self.terminology_issues:
            if issue["term"] == vals[0] and issue["type"] == vals[1]:
                self.term_detail_text.delete("1.0", tk.END)
                self.term_detail_text.insert(tk.END, f"TERM: {issue['term']}\n")
                self.term_detail_text.insert(tk.END, f"TYPE: {issue['type']}\n")
                self.term_detail_text.insert(tk.END, f"ISSUE: {issue['issue']}\n")
                self.term_detail_text.insert(tk.END, f"CORRECT FORM: {issue['correct_form']}\n")
                self.term_detail_text.insert(tk.END, f"\nDEFINITION:\n{issue.get('definition', 'N/A')}\n")
                self.term_detail_text.insert(tk.END, f"\nSOURCE: {issue.get('source', 'N/A')}\n")
                break

    def _populate_defl_tree(self):
        for item in self.defl_tree.get_children():
            self.defl_tree.delete(item)

        for issue in self.deflection_issues:
            sev_color = {"high": COLORS["red_light"], "medium": COLORS["orange_light"],
                         "low": COLORS["green_light"]}.get(issue["severity"], COLORS["text_primary"])
            self.defl_tree.insert("", tk.END, values=(
                issue["pattern_type"],
                issue["severity"].upper(),
                issue["count"],
                issue["description"][:60],
                issue["suggestion"][:50],
            ), tags=(issue["severity"],))

        self.defl_tree.tag_configure("high", foreground=COLORS["red_light"])
        self.defl_tree.tag_configure("medium", foreground=COLORS["orange_light"])
        self.defl_tree.tag_configure("low", foreground=COLORS["green_light"])

    def _populate_xref_tab(self):
        # CanLII
        self.xref_canlii_text.delete("1.0", tk.END)
        cross_refs = self.analysis_results.get("cross_references", {})
        canlii_refs = cross_refs.get("canlii", {})

        if canlii_refs:
            for section, refs in canlii_refs.items():
                self.xref_canlii_text.insert(tk.END, f"\nSection {section} — CanLII Search\n{'─'*40}\n")
                if refs.get("search_urls"):
                    for label, url in refs["search_urls"].items():
                        self.xref_canlii_text.insert(tk.END, f"  {label.title()}: {url}\n")
                if refs.get("message"):
                    self.xref_canlii_text.insert(tk.END, f"  Note: {refs['message']}\n")
                if not refs.get("api_configured", True):
                    self.xref_canlii_text.insert(tk.END, f"  ⚠️ API not configured — use URLs above\n")
        else:
            self.xref_canlii_text.insert(tk.END, "Run Charter analysis to generate CanLII cross-references.")

        # CLN
        self.xref_cln_text.delete("1.0", tk.END)
        cln_refs = cross_refs.get("criminallawnotebook", {})

        if cln_refs:
            for section, refs in cln_refs.items():
                self.xref_cln_text.insert(tk.END, f"\nSection {section} — Criminal Law Notebook\n{'─'*40}\n")
                if refs.get("direct_reference"):
                    self.xref_cln_text.insert(tk.END, f"  📕 Direct: {refs['direct_reference']}\n")
                if refs.get("related_topics"):
                    for t in refs["related_topics"]:
                        self.xref_cln_text.insert(tk.END, f"  📎 {t['name']}: {t['url']}\n")
                if refs.get("exclusion_reference"):
                    self.xref_cln_text.insert(tk.END, f"  📕 Exclusion: {refs['exclusion_reference']}\n")
        else:
            self.xref_cln_text.insert(tk.END, "Run Charter analysis to generate CLN cross-references.")

    def _highlight_document(self):
        """Highlight charter references, breach indicators, and terminology issues in the document."""
        import re
        text_widget = self.doc_text

        # Remove existing tags
        for tag in ["charter_ref", "breach_indicator", "deflection", "term_issue"]:
            text_widget.tag_remove(tag, "1.0", tk.END)

        content = text_widget.get("1.0", tk.END)
        content_lower = content.lower()

        # Highlight Charter section references
        charter_patterns = [
            r'(?:s\.?\s*\d+(?:\([a-z0-9]+\))?)\s+of\s+(?:the\s+)?(?:Charter|Canadian Charter)',
            r'(?:Charter|Canadian Charter)[,\s]+(?:s\.?\s*\d+(?:\([a-z0-9]+\))?)',
        ]
        for pat in charter_patterns:
            for m in re.finditer(pat, content, re.IGNORECASE):
                start = f"1.0+{m.start()}c"
                end = f"1.0+{m.end()}c"
                text_widget.tag_add("charter_ref", start, end)

        # Highlight breach indicators
        breach_words = ["violation", "infringement", "breach", "unreasonable", "arbitrary",
                        "unconstitutional", "unlawful", "without warrant", "without reasonable grounds",
                        "grossly disproportionate", "denied", "not informed", "failure to inform",
                        "excessive", "overbroad"]
        for word in breach_words:
            for m in re.finditer(re.escape(word), content, re.IGNORECASE):
                start = f"1.0+{m.start()}c"
                end = f"1.0+{m.end()}c"
                text_widget.tag_add("breach_indicator", start, end)

        # Highlight deflection patterns
        for issue in self.deflection_issues:
            for match_text in issue.get("matches", []):
                for m in re.finditer(re.escape(match_text), content, re.IGNORECASE):
                    start = f"1.0+{m.start()}c"
                    end = f"1.0+{m.end()}c"
                    text_widget.tag_add("deflection", start, end)

        # Highlight term issues
        for issue in self.terminology_issues:
            term = issue["term"]
            for m in re.finditer(re.escape(term), content, re.IGNORECASE):
                start = f"1.0+{m.start()}c"
                end = f"1.0+{m.end()}c"
                text_widget.tag_add("term_issue", start, end)

    # ══════════════════════════════════════════════════════════════════════════
    # AI INTEGRATION
    # ══════════════════════════════════════════════════════════════════════════

    def _update_ai_status(self):
        if self.ai.is_configured():
            self.ai_status_label.config(text="AI: ✅ Connected (GPT-4)", foreground=COLORS["success"])
        else:
            self.ai_status_label.config(text="AI: ❌ Not configured (Settings → API Keys)",
                                         foreground=COLORS["warning"])

    def _run_ai_verify(self):
        if not self._check_document_loaded():
            return
        self._ai_verify_specific("charter")

    def _ai_verify_specific(self, analysis_type):
        if not self.ai.is_configured():
            messagebox.showwarning("AI Not Configured",
                "OpenAI API key not configured.\n\n"
                "Go to Settings → API Keys to add your key, "
                "or set the OPENAI_API_KEY environment variable.")
            return

        if not self._check_document_loaded():
            return

        self.status_var.set(f"Running AI verification ({analysis_type})... Please wait.")
        self.root.update_idletasks()

        def _worker():
            try:
                if analysis_type == "charter":
                    result = self.ai.verify_charter_analysis(self.analysis_results, self.document_text)
                elif analysis_type == "terms":
                    result = self.ai.verify_legal_terms(self.document_text, self.terminology_issues)
                elif analysis_type == "deflection":
                    result = self.ai.detect_deflection(self.document_text, self.deflection_issues)
                elif analysis_type == "crossref":
                    result = self.ai.validate_cross_references(self.analysis_results, self.document_text)
                elif analysis_type == "summary":
                    result = self.ai.generate_summary(self.analysis_results)
                else:
                    result = {"error": "Unknown analysis type", "content": None}

                # Update UI from main thread
                self.root.after(0, self._display_ai_result, analysis_type, result)
            except Exception as e:
                self.root.after(0, self._display_ai_error, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _display_ai_result(self, analysis_type, result):
        if result.get("error") and not result.get("content"):
            self.ai_output.insert(tk.END, f"\n⚠️ ERROR: {result['error']}\n")
            self.status_var.set(f"AI error: {result['error'][:60]}")
            return

        content = result.get("content", "No response")
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.ai_output.insert(tk.END,
            f"\n{'═'*70}\n"
            f"🤖 AI VERIFICATION — {analysis_type.upper()} — {timestamp}\n"
            f"{'═'*70}\n\n"
            f"{content}\n\n"
        )
        self.ai_output.see(tk.END)

        usage = self.ai.get_usage_stats()
        self.status_var.set(
            f"AI analysis complete ({analysis_type}). Tokens: {usage['total_tokens']:,} | Cost: ~${usage['estimated_cost_usd']:.4f}"
        )

    def _display_ai_error(self, error):
        self.ai_output.insert(tk.END, f"\n❌ AI Error: {error}\n")
        self.status_var.set(f"AI error: {error[:60]}")

    def _ai_ask(self):
        question = self.ai_ask_var.get().strip()
        if not question:
            return
        if not self.ai.is_configured():
            messagebox.showwarning("AI Not Configured", "Configure API key in Settings first.")
            return

        self.status_var.set("Sending question to AI...")
        self.root.update_idletasks()

        def _worker():
            try:
                result = self.ai.ask_custom_question(question, self.document_text[:2000] if self.document_text else "")
                self.root.after(0, self._display_ai_result, "custom", result)
            except Exception as e:
                self.root.after(0, self._display_ai_error, str(e))

        threading.Thread(target=_worker, daemon=True).start()
        self.ai_ask_var.set("")

    # ══════════════════════════════════════════════════════════════════════════
    # CROSS-REFERENCE DIALOGS
    # ══════════════════════════════════════════════════════════════════════════

    def _canlii_search_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("CanLII Search")
        dlg.geometry("700x500")
        dlg.transient(self.root)
        dlg.grab_set()

        ttk.Label(dlg, text="Search CanLII for Canadian Case Law", style="Subheader.TLabel").pack(
            padx=10, pady=8)

        # Search input
        search_frame = ttk.Frame(dlg)
        search_frame.pack(fill=tk.X, padx=10, pady=4)

        ttk.Label(search_frame, text="Query:").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=50, font=("Segoe UI", 10))
        search_entry.pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        # Options
        opt_frame = ttk.Frame(dlg)
        opt_frame.pack(fill=tk.X, padx=10, pady=4)

        ttk.Label(opt_frame, text="Court:").pack(side=tk.LEFT)
        court_var = tk.StringVar(value="All")
        court_combo = ttk.Combobox(opt_frame, textvariable=court_var, width=20, state="readonly",
            values=["All", "csc-scc", "cf", "caf", "onsc", "onca", "bcsc", "bcca", "abqb", "abca", "qccs", "qcca"])
        court_combo.pack(side=tk.LEFT, padx=4)

        # Results
        result_text = scrolledtext.ScrolledText(dlg, wrap=tk.WORD, font=("Consolas", 10),
                                                  bg=COLORS["input_bg"], fg=COLORS["text_primary"],
                                                  relief=tk.FLAT)
        result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        def _search():
            query = search_var.get().strip()
            if not query:
                return
            client = CanLIIClient()
            results = client.search_cases(query, database_id=court_var.get() if court_var.get() != "All" else None)
            result_text.delete("1.0", tk.END)

            if results.get("error"):
                result_text.insert(tk.END, f"Error: {results['error']}\n\n")
                result_text.insert(tk.END, "Direct search URL:\n")
                eq = urllib.parse.quote(query, safe="")
                result_text.insert(tk.END, f"https://www.canlii.org/en/search/#search[0][query]={eq}\n")
            elif results.get("search_urls"):
                result_text.insert(tk.END, "CanLII API not configured. Use direct URLs:\n\n")
                for label, url in results["search_urls"].items():
                    result_text.insert(tk.END, f"{label.title()}:\n{url}\n\n")
            else:
                result_text.insert(tk.END, f"Results found.\n")
                for case in results.get("results", [])[:10]:
                    result_text.insert(tk.END, f"\n• {case.get('title', 'Unknown')}\n")
                    result_text.insert(tk.END, f"  Citation: {case.get('citation', 'N/A')}\n")

        ttk.Button(opt_frame, text="Search", command=_search, style="Accent.TButton").pack(side=tk.LEFT, padx=8)

    def _cln_browse(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Criminal Law Notebook")
        dlg.geometry("800x600")
        dlg.transient(self.root)
        dlg.grab_set()

        ttk.Label(dlg, text="Criminal Law Notebook — Topic Browser", style="Subheader.TLabel").pack(
            padx=10, pady=8)

        cln = CriminalLawNotebookClient()

        tree = ttk.Treeview(dlg, columns=("url",), show="tree headings", height=15)
        tree.heading("#0", text="Topic")
        tree.heading("url", text="URL")
        tree.column("url", width=450)

        for topic_id, topic in cln.TOPICS.items():
            topic_node = tree.insert("", tk.END, text=topic["name"], values=(topic["url"],), open=False)
            for sub_id, sub_url in topic.get("subtopics", {}).items():
                sub_name = sub_id.replace("_", " ").title()
                tree.insert(topic_node, tk.END, text=f"  {sub_name}", values=(sub_url,))

        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        def _open_url(event):
            sel = tree.selection()
            if sel:
                url = tree.item(sel[0], "values")[0]
                webbrowser.open(url)

        ttk.Button(dlg, text="Open Selected in Browser", command=lambda: _open_url(None),
                    style="Accent.TButton").pack(pady=8)

    # ══════════════════════════════════════════════════════════════════════════
    # DICTIONARY
    # ══════════════════════════════════════════════════════════════════════════

    def _populate_dictionary_tree(self, filter_text="", category="All"):
        for item in self.dict_tree.get_children():
            self.dict_tree.delete(item)

        for term_key, term_data in LEGAL_DICTIONARY.items():
            if filter_text and filter_text.lower() not in term_key.lower() and \
               filter_text.lower() not in term_data["preferred_form"].lower():
                continue
            if category != "All" and term_data["category"] != category:
                continue

            self.dict_tree.insert("", tk.END, iid=term_key, values=(
                term_key.replace("_", " ").title(),
                term_data["category"],
                term_data["preferred_form"],
                term_data.get("source", "")[:50],
            ))

    def _search_dictionary(self):
        query = self.dict_search_var.get().strip()
        category = self.dict_cat_var.get()
        self._populate_dictionary_tree(query, category)

    def _on_dict_select(self, event):
        sel = self.dict_tree.selection()
        if not sel:
            return
        term_key = sel[0]
        term_data = LEGAL_DICTIONARY.get(term_key)

        self.dict_def_text.delete("1.0", tk.END)
        if not term_data:
            return

        self.dict_def_text.insert(tk.END, f"TERM: {term_key.replace('_', ' ').title()}\n")
        self.dict_def_text.insert(tk.END, f"{'═'*60}\n\n")
        self.dict_def_text.insert(tk.END, f"DEFINITION:\n{term_data['definition']}\n\n")
        self.dict_def_text.insert(tk.END, f"PREFERRED FORM: {term_data['preferred_form']}\n")
        self.dict_def_text.insert(tk.END, f"CATEGORY: {term_data['category']}\n")
        self.dict_def_text.insert(tk.END, f"SOURCE: {term_data.get('source', 'N/A')}\n\n")

        if term_data.get("aliases"):
            self.dict_def_text.insert(tk.END, f"ALIASES: {', '.join(term_data['aliases'])}\n")
        if term_data.get("misuses"):
            self.dict_def_text.insert(tk.END, f"\n⚠️ MISUSES TO AVOID:\n")
            for m in term_data["misuses"]:
                self.dict_def_text.insert(tk.END, f"  ✗ '{m}'\n")

    def _quick_dict_lookup(self):
        query = self.dict_entry_var.get().strip().lower()
        if not query:
            self.dict_result_label.config(text="Enter a term to look up.")
            return

        # Search dictionary
        for term_key, term_data in LEGAL_DICTIONARY.items():
            if query == term_key.lower() or query in [a.lower() for a in term_data.get("aliases", [])]:
                self.dict_result_label.config(
                    text=f"✓ {term_data['preferred_form']}\n{term_data['definition'][:200]}..."
                )
                return

        self.dict_result_label.config(text=f"'{query}' not found in dictionary.\nTry the Dictionary tab for a full search.")

    def _dict_lookup_dialog(self):
        """Open a full dictionary lookup dialog."""
        self.notebook.select(self.dict_tab)

    # ══════════════════════════════════════════════════════════════════════════
    # SETTINGS & DIALOGS
    # ══════════════════════════════════════════════════════════════════════════

    def _settings_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("API Key Settings")
        dlg.geometry("600x350")
        dlg.transient(self.root)
        dlg.grab_set()

        ttk.Label(dlg, text="API Configuration", style="Subheader.TLabel").pack(padx=10, pady=8)
        ttk.Label(dlg, text="API keys are stored in memory only (not saved to disk).",
                   foreground=COLORS["text_secondary"]).pack(padx=10)

        # CanLII
        canlii_frame = ttk.LabelFrame(dlg, text="CanLII API", padding=10)
        canlii_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(canlii_frame, text="CanLII API Key:").pack(anchor=tk.W)
        canlii_var = tk.StringVar(value=CANLII_API_KEY or os.environ.get("CANLII_API_KEY", ""))
        ttk.Entry(canlii_frame, textvariable=canlii_var, width=60, show="*").pack(fill=tk.X, pady=2)
        ttk.Label(canlii_frame, text="Get a free key at: https://api.canlii.org/",
                   foreground=COLORS["info"]).pack(anchor=tk.W)

        # OpenAI
        openai_frame = ttk.LabelFrame(dlg, text="OpenAI API (GPT-4)", padding=10)
        openai_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(openai_frame, text="OpenAI API Key:").pack(anchor=tk.W)
        openai_var = tk.StringVar(value=os.environ.get("OPENAI_API_KEY", ""))
        ttk.Entry(openai_frame, textvariable=openai_var, width=60, show="*").pack(fill=tk.X, pady=2)
        ttk.Label(openai_frame, text="Set via environment variable OPENAI_API_KEY or enter above.",
                   foreground=COLORS["info"]).pack(anchor=tk.W)

        # Model
        model_frame = ttk.LabelFrame(dlg, text="AI Model", padding=10)
        model_frame.pack(fill=tk.X, padx=10, pady=8)
        model_var = tk.StringVar(value="gpt-4")
        ttk.Combobox(model_frame, textvariable=model_var, width=20, state="readonly",
                      values=["gpt-4", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]).pack(anchor=tk.W)

        def _save():
            # Update CanLII
            # We update the runtime objects
            self.charter_analyzer.canlii.api_key = canlii_var.get().strip()

            # Update OpenAI
            self.ai.api_key = openai_var.get().strip()
            self.ai.model = model_var.get()
            if self.ai.api_key:
                self.ai.session.headers.update({"Authorization": f"Bearer {self.ai.api_key}"})
                os.environ["OPENAI_API_KEY"] = self.ai.api_key

            self._update_ai_status()
            dlg.destroy()
            messagebox.showinfo("Settings Saved", "API keys configured for this session.")

        ttk.Button(dlg, text="Save Settings", command=_save, style="Success.TButton").pack(pady=10)

    def _ai_question_dialog(self):
        """Open AI question dialog."""
        self.notebook.select(self.ai_tab)
        self.ai_ask_var.set("")
        self.root.focus_set()

    # ══════════════════════════════════════════════════════════════════════════
    # EXPORT
    # ══════════════════════════════════════════════════════════════════════════

    def _export_html(self):
        if not self.analysis_results:
            messagebox.showwarning("No Results", "Run an analysis first.")
            return

        path = filedialog.asksaveasfilename(
            title="Export HTML Report",
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("All", "*.*")],
            initialfile=f"charter_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
        )
        if not path:
            return

        try:
            self.report_generator.generate_html_report(
                self.analysis_results, self.document_metadata, path
            )
            # Ask to open
            if messagebox.askyesno("Report Saved", f"Report saved to:\n{path}\n\nOpen in browser?"):
                webbrowser.open(f"file://{path}")
            self.status_var.set(f"HTML report exported: {path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _export_txt(self):
        if not self.analysis_results:
            messagebox.showwarning("No Results", "Run an analysis first.")
            return

        path = filedialog.asksaveasfilename(
            title="Export Text Report",
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All", "*.*")],
            initialfile=f"charter_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        )
        if not path:
            return

        try:
            self.report_generator.generate_text_report(
                self.analysis_results, self.document_metadata, path
            )
            messagebox.showinfo("Report Saved", f"Report saved to:\n{path}")
            self.status_var.set(f"Text report exported: {path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    root = tk.Tk()

    # Set DPI awareness on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = LegalAnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
