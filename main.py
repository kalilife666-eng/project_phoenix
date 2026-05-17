
# Copyright project_phoenix
"""
Disclosure Analysis Tool
Simple report analyzer for disclosure/report issues.
"""

import os
import re
import threading
import tkinter as tk
import webbrowser
import urllib.parse
from datetime import datetime
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk

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
from privacy_scrubber import scrub_party_identifiers
from report_generator import ReportGenerator

# ─── Color Scheme ──────────────────────────────────────────────────────────────
COLORS = {
    "bg_dark": "#111111",
    "bg_medium": "#151515",
    "bg_light": "#1d1d1d",
    "accent": "#5f5f5f",
    "accent2": "#3f3f3f",
    "text_primary": "#efefef",
    "text_secondary": "#9a9a9a",
    "text_highlight": "#ffffff",
    "success": "#707070",
    "warning": "#6a6a6a",
    "danger": "#555555",
    "info": "#8a8a8a",
    "panel_bg": "#121212",
    "card_bg": "#171717",
    "input_bg": "#1b1b1b",
    "green_light": "#8a8a8a",
    "orange_light": "#7a7a7a",
    "red_light": "#6a6a6a",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAST_DOCUMENT_STATE_PATH = os.path.join(os.getcwd(), ".last_document_state.json")
LOGO_ICON_PATH = os.path.join(BASE_DIR, "assets", "project_phoenix_logo_icon.png")
LOGO_BG_PATH = os.path.join(BASE_DIR, "assets", "project_phoenix_logo.png")
BUILD_TAG = datetime.utcnow().strftime("%Y%m%d-%H%M%S")


def _about_dialog():
    messagebox.showinfo("About",
        f"Disclosure Analysis Tool\n"
        f"Version {APP_VERSION}\n\n"
        f"Simple disclosure analysis tool.\n\n"
        f"This tool checks report text against dictionary definitions\n"
        f"and highlights potential issues in plain language.\n\n"
        f"It is not legal advice."
    )


def _normalize_legal_term(term_key, term_data):
    return {
        "definition": term_data.get("definition") or term_data.get("legal_definition", ""),
        "preferred_form": term_data.get("preferred_form") or term_key.replace("_", " "),
        "category": term_data.get("category", "general"),
        "source": term_data.get("source") or term_data.get("legal_source", "Legal Dictionary"),
        "aliases": term_data.get("aliases", []),
        "misuses": term_data.get("misuses", []),
    }


class LegalAnalyzerApp:
    """Main application class for the project_phoenix GUI."""

    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} v{APP_VERSION} [{BUILD_TAG}]")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(1200, 750)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Core objects
        self.doc_processor = DocumentProcessor()
        self.charter_analyzer = CharterAnalyzer()
        self.report_generator = ReportGenerator()
        self.ai = AIIntegration()

        # State
        self.document_text = ""
        self.document_metadata = {}
        self.analysis_results = {}
        self.display_results = {}
        self.terminology_issues = []
        self.deflection_issues = []
        self.ai_results = {}
        self.breach_animation_after_id = None
        self.breach_animation_running = False
        self.breach_animation_frame = 0
        self.logo_bg_image = None
        self.logo_bg_source = None
        self.logo_bg_render = None
        self.logo_banner_render = None
        self.bg_canvas = None
        self.bg_canvas_image_id = None
        self.ui_root = None
        self.ui_window_id = None

        self._load_brand_assets()
        self._build_background()

        # Disclaimer Label
        parent = self.ui_root if self.ui_root is not None else self.root
        disclaimer_frame = tk.Frame(parent, bg="#101010")
        disclaimer_frame.pack(side="top", fill="x")
        tk.Label(disclaimer_frame, text="RESEARCH AND STATISTICS TOOL ONLY — NOT LEGAL ADVICE — VERIFY ALL RESULTS", 
                 bg="#101010", fg="#d8d8d8", font=("Helvetica", 10, "bold"), pady=5).pack()

        # Build UI tabs
        self.notebook = ttk.Notebook(self.root)
        self._build_styles()
        self._build_ui()
        self.root.after(50, self._restore_last_document_state)

    def _load_brand_assets(self):
        if os.path.exists(LOGO_BG_PATH):
            self.logo_bg_source = Image.open(LOGO_BG_PATH)
        # Intentionally do not set a custom window icon.

    def _build_background(self):
        if self.logo_bg_source is None:
            return
        self.bg_canvas = tk.Canvas(self.root, bd=0, highlightthickness=0)
        self.bg_canvas.pack(fill=tk.BOTH, expand=True)
        self.bg_canvas_image_id = self.bg_canvas.create_image(0, 0, anchor=tk.NW)
        self.ui_root = tk.Frame(self.bg_canvas, bg="")
        self.ui_window_id = self.bg_canvas.create_window(0, 0, anchor=tk.NW, window=self.ui_root)
        self.root.bind("<Configure>", self._refresh_background_image, add="+")
        self._refresh_background_image()

    def _refresh_background_image(self, event=None):
        if self.logo_bg_source is None or self.bg_canvas is None:
            return
        width = max(self.root.winfo_width(), 1)
        height = max(self.root.winfo_height(), 1)
        resized = self.logo_bg_source.resize((width, height), Image.LANCZOS)
        self.logo_bg_render = ImageTk.PhotoImage(resized)
        self.bg_canvas.config(width=width, height=height)
        self.bg_canvas.itemconfigure(self.bg_canvas_image_id, image=self.logo_bg_render)
        self.bg_canvas.coords(self.bg_canvas_image_id, 0, 0)
        if self.ui_window_id is not None:
            self.bg_canvas.itemconfigure(self.ui_window_id, width=width, height=height)
            self.bg_canvas.coords(self.ui_window_id, 0, 0)

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
        self.style.configure(
            "SidebarTab.TButton",
            background=COLORS["card_bg"],
            foreground=COLORS["text_primary"],
            font=("Segoe UI", 10, "bold"),
            padding=(12, 10),
            anchor="w",
        )
        self.style.map(
            "SidebarTab.TButton",
            background=[("active", COLORS["bg_medium"]), ("pressed", COLORS["bg_light"])],
            foreground=[("active", "white")],
        )
        self.style.configure(
            "SidebarTabActive.TButton",
            background=COLORS["accent"],
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 10),
            anchor="w",
        )

        # Notebook tabs
        self.style.configure("TNotebook", background=COLORS["bg_dark"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=COLORS["bg_medium"],
                              foreground=COLORS["text_primary"], padding=[16, 8],
                              font=("Segoe UI", 10, "bold"))
        self.style.map("TNotebook.Tab",
                        background=[("selected", COLORS["accent"])],
                        foreground=[("selected", "white")])
        # Force-hide notebook tab strips globally and for this tabless style.
        self.style.layout("TNotebook.Tab", [])
        self.style.layout("Tabless.TNotebook", [("Notebook.client", {"sticky": "nswe"})])
        self.style.layout("Tabless.TNotebook.Tab", [])

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
                              foreground=COLORS["text_primary"])
        self.style.configure("Info.TLabel", foreground=COLORS["info"])
        self.style.configure("Success.TLabel", foreground=COLORS["success"])
        self.style.configure("Warning.TLabel", foreground=COLORS["warning"])
        self.style.configure("Danger.TLabel", foreground=COLORS["danger"])

        # Labelframe
        self.style.configure("TLabelframe", background=COLORS["bg_dark"],
                              foreground=COLORS["text_secondary"])
        self.style.configure("TLabelframe.Label", background=COLORS["bg_dark"],
                              foreground=COLORS["text_secondary"], font=("Segoe UI", 10, "bold"))

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
        container = self.ui_root if self.ui_root is not None else self.root
        main_pane = ttk.PanedWindow(container, orient=tk.HORIZONTAL)
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
        status_bar = ttk.Label(container, textvariable=self.status_var, relief=tk.SUNKEN,
                                anchor=tk.W, font=("Segoe UI", 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=2, pady=2)

    def _build_left_panel(self, parent):
        # ── Logo / Title ──
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, padx=8, pady=(8, 4))
        ttk.Label(title_frame, text="Disclosure Analysis Tool", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(
            title_frame,
            text=f"Disclosure Analysis Tool v{APP_VERSION}",
            foreground=COLORS["text_secondary"],
        ).pack(anchor=tk.W)

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
        ttk.Button(analysis_frame, text="📖 Dictionary & Terminology",
                    command=self._run_terminology).pack(fill=tk.X, pady=2)
        ttk.Button(analysis_frame, text="🚫 Deflection / Ambiguity",
                    command=self._run_deflection).pack(fill=tk.X, pady=2)
        ttk.Button(analysis_frame, text="🧪 Disclosure Integrity Scan",
                    command=self._run_disclosure_integrity_scan, style="Warning.TButton").pack(fill=tk.X, pady=2)
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
        if self.logo_bg_source is not None:
            banner = self.logo_bg_source.resize((1200, 420), Image.LANCZOS)
            self.logo_banner_render = ImageTk.PhotoImage(banner)
            tk.Label(
                parent,
                image=self.logo_banner_render,
                bg=COLORS["bg_dark"],
                bd=0,
                highlightthickness=0,
            ).pack(fill=tk.X, pady=(0, 8))

        shell = ttk.Frame(parent)
        shell.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        nav_frame = ttk.Frame(shell, width=220)
        nav_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        content_frame = ttk.Frame(shell)
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.view_nav_frame = nav_frame
        self.view_buttons = {}
        self.view_order = []

        self.notebook = ttk.Notebook(content_frame, style="Tabless.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Document View
        self.doc_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.doc_tab, text="  📄 Document  ")
        self.view_order.append(("📄 Document", self.doc_tab))
        self._build_document_tab(self.doc_tab)

        # Tab 2: Charter Analysis
        self.charter_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.charter_tab, text="  ⚖️ Charter Analysis  ")
        self.view_order.append(("⚖️ Charter Analysis", self.charter_tab))
        self._build_charter_tab(self.charter_tab)

        # Tab 3: Terminology
        self.term_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.term_tab, text="  📖 Terminology  ")
        self.view_order.append(("📖 Terminology", self.term_tab))
        self._build_terminology_tab(self.term_tab)

        # Tab 4: Deflection / Ambiguity
        self.deflection_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.deflection_tab, text="  🚫 Deflection  ")
        self.view_order.append(("🚫 Deflection", self.deflection_tab))
        self._build_deflection_tab(self.deflection_tab)

        # Tab 5: Interactions & Specific Flags
        self.interaction_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.interaction_tab, text="  🔗 Interactions  ")
        self.view_order.append(("🔗 Interactions", self.interaction_tab))
        self._build_interaction_tab(self.interaction_tab)

        # Tab 6: Official Conduct
        self.police_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.police_tab, text="  👮 Official Conduct  ")
        self.view_order.append(("👮 Official Conduct", self.police_tab))
        self._build_police_tab(self.police_tab)

        # Tab 7: Prosecution Review
        self.prosecution_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.prosecution_tab, text="  ⚖️ Prosecution Review  ")
        self.view_order.append(("⚖️ Prosecution Review", self.prosecution_tab))
        self._build_prosecution_tab(self.prosecution_tab)

        # Tab 8: Cross-References
        self.xref_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.xref_tab, text="  📚 Cross-References  ")
        self.view_order.append(("📚 Cross-References", self.xref_tab))
        self._build_xref_tab(self.xref_tab)

        # Tab 9: Human Rights
        self.human_rights_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.human_rights_tab, text="  🧭 Human Rights  ")
        self.view_order.append(("🧭 Human Rights", self.human_rights_tab))
        self._build_human_rights_tab(self.human_rights_tab)

        # Tab 10: Disclosure Integrity
        self.disclosure_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.disclosure_tab, text="  🧪 Disclosure Integrity  ")
        self.view_order.append(("🧪 Disclosure Integrity", self.disclosure_tab))
        self._build_disclosure_integrity_tab(self.disclosure_tab)

        # Tab 11: AI Analysis
        self.ai_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.ai_tab, text="  🤖 AI Analysis  ")
        self.view_order.append(("🤖 AI Analysis", self.ai_tab))
        self._build_ai_tab(self.ai_tab)

        # Tab 12: Dictionary
        self.dict_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.dict_tab, text="  📕 Dictionary  ")
        self.view_order.append(("📕 Dictionary", self.dict_tab))
        self._build_dictionary_tab(self.dict_tab)

        self._build_view_nav()
        self.notebook.bind("<<NotebookTabChanged>>", self._sync_view_nav)
        self._sync_view_nav()

    def _build_view_nav(self):
        ttk.Label(self.view_nav_frame, text="Analysis Views", style="Subheader.TLabel").pack(
            anchor=tk.W, padx=4, pady=(4, 8)
        )
        for label, tab in self.view_order:
            btn = ttk.Button(
                self.view_nav_frame,
                text=label,
                style="SidebarTab.TButton",
                command=lambda t=tab: self._select_view(t),
            )
            btn.pack(fill=tk.X, pady=2)
            self.view_buttons[str(tab)] = btn

    def _select_view(self, tab):
        self.notebook.select(tab)
        self._sync_view_nav()

    def _sync_view_nav(self, event=None):
        current = str(self.notebook.select())
        for key, btn in self.view_buttons.items():
            btn.configure(style="SidebarTabActive.TButton" if key == current else "SidebarTab.TButton")

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

        animation_frame = ttk.LabelFrame(parent, text="Breach Visualization", padding=6)
        animation_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
        self.breach_canvas = tk.Canvas(
            animation_frame,
            height=150,
            bg="#120b11",
            highlightthickness=0,
            relief=tk.FLAT,
        )
        self.breach_canvas.pack(fill=tk.X, expand=True)
        self._draw_breach_scene(progress=0.0, explosion=0.0, active=False)

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
        detail_frame = ttk.LabelFrame(parent, text="Breach Detail & Legal Tests", padding=6)
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

    # ── Interactions & State Conduct Tab ──────────────────────────────────────

    def _build_interaction_tab(self, parent):
        ttk.Label(parent, text="Charter Breach Interactions & State Conduct", style="Subheader.TLabel").pack(
            anchor=tk.W, padx=8, pady=(8, 4))

        conduct_frame = ttk.LabelFrame(parent, text="State Conduct Assessment", padding=8)
        conduct_frame.pack(fill=tk.X, padx=8, pady=4)

        self.conduct_text = scrolledtext.ScrolledText(
            conduct_frame, wrap=tk.WORD, font=("Segoe UI", 10),
            bg=COLORS["panel_bg"], fg=COLORS["text_primary"],
            relief=tk.FLAT, height=10
        )
        self.conduct_text.pack(fill=tk.X, expand=True)

        # Breach Interactions
        interactions_frame = ttk.LabelFrame(parent, text="Systemic Interactions", padding=6)
        interactions_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.interaction_tree = ttk.Treeview(interactions_frame, columns=("sections", "severity", "description"), show="headings", height=8)
        self.interaction_tree.heading("sections", text="Sections")
        self.interaction_tree.heading("severity", text="Severity")
        self.interaction_tree.heading("description", text="Contextual Description")
        self.interaction_tree.column("sections", width=100)
        self.interaction_tree.column("severity", width=80)
        self.interaction_tree.column("description", width=800, anchor=tk.W)
        self.interaction_tree.bind("<<TreeviewSelect>>", self._on_interaction_select)
        self.interaction_tree.pack(fill=tk.BOTH, expand=True)

        # Specific Flags
        flags_frame = ttk.LabelFrame(parent, text="Specific User-Defined Flags", padding=6)
        flags_frame.pack(fill=tk.X, padx=8, pady=4)

        self.flag_tree = ttk.Treeview(flags_frame, columns=("label", "description", "matches"), show="headings", height=4)
        self.flag_tree.heading("label", text="Flag Label")
        self.flag_tree.heading("description", text="Significance")
        self.flag_tree.heading("matches", text="Found Instances")
        self.flag_tree.column("label", width=250)
        self.flag_tree.column("description", width=400)
        self.flag_tree.column("matches", width=300)
        self.flag_tree.pack(fill=tk.X, expand=True)

    def _build_police_tab(self, parent):
        ttk.Label(parent, text="Official Conduct Indicators", style="Subheader.TLabel").pack(
            anchor=tk.W, padx=8, pady=(8, 4))

        frame = ttk.LabelFrame(parent, text="Indicators", padding=6)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        cols = ("indicator", "severity", "source")
        self.police_tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        self.police_tree.heading("indicator", text="Indicator")
        self.police_tree.heading("severity", text="Severity")
        self.police_tree.heading("source", text="Source")
        self.police_tree.column("indicator", width=360)
        self.police_tree.column("severity", width=120, anchor=tk.CENTER)
        self.police_tree.column("source", width=260)
        self.police_tree.pack(fill=tk.BOTH, expand=True)
        self.police_tree.bind("<<TreeviewSelect>>", self._on_police_indicator_select)
        self.police_tree.bind("<Double-1>", lambda e: self._open_selected_indicator_url("police"))

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
        ttk.Button(btn_frame, text="Open Reference URL", command=lambda: self._open_selected_indicator_url("police")).pack(side=tk.RIGHT)

        self.police_detail_text = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, font=("Consolas", 10),
            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
            relief=tk.FLAT, height=10
        )
        self.police_detail_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

    def _build_prosecution_tab(self, parent):
        ttk.Label(parent, text="Prosecution Review Indicators", style="Subheader.TLabel").pack(
            anchor=tk.W, padx=8, pady=(8, 4))

        frame = ttk.LabelFrame(parent, text="Indicators", padding=6)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        cols = ("indicator", "severity", "source")
        self.prosecution_tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        self.prosecution_tree.heading("indicator", text="Indicator")
        self.prosecution_tree.heading("severity", text="Severity")
        self.prosecution_tree.heading("source", text="Source")
        self.prosecution_tree.column("indicator", width=360)
        self.prosecution_tree.column("severity", width=140, anchor=tk.CENTER)
        self.prosecution_tree.column("source", width=260)
        self.prosecution_tree.pack(fill=tk.BOTH, expand=True)
        self.prosecution_tree.bind("<<TreeviewSelect>>", self._on_prosecution_indicator_select)
        self.prosecution_tree.bind("<Double-1>", lambda e: self._open_selected_indicator_url("prosecution"))

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
        ttk.Button(btn_frame, text="Open Reference URL", command=lambda: self._open_selected_indicator_url("prosecution")).pack(side=tk.RIGHT)

        self.prosecution_detail_text = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, font=("Consolas", 10),
            bg=COLORS["input_bg"], fg=COLORS["text_primary"],
            relief=tk.FLAT, height=10
        )
        self.prosecution_detail_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

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

    def _build_human_rights_tab(self, parent):
        ttk.Label(parent, text="UN / National / Provincial Human Rights Assessment", style="Subheader.TLabel").pack(
            anchor=tk.W, padx=8, pady=(8, 4))

        summary_frame = ttk.LabelFrame(parent, text="Assessment Summary", padding=6)
        summary_frame.pack(fill=tk.X, padx=8, pady=4)
        self.hr_summary_text = scrolledtext.ScrolledText(
            summary_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg=COLORS["input_bg"], fg=COLORS["text_primary"], relief=tk.FLAT, height=8
        )
        self.hr_summary_text.pack(fill=tk.X, expand=True)

        cases_frame = ttk.LabelFrame(parent, text="Relevant Human Rights Criteria / Cases", padding=6)
        cases_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        cols = ("criterion", "cases")
        self.hr_tree = ttk.Treeview(cases_frame, columns=cols, show="headings", height=10)
        self.hr_tree.heading("criterion", text="Criterion")
        self.hr_tree.heading("cases", text="Case Law")
        self.hr_tree.column("criterion", width=280)
        self.hr_tree.column("cases", width=520)
        self.hr_tree.pack(fill=tk.BOTH, expand=True)
        self.hr_tree.bind("<<TreeviewSelect>>", self._on_hr_select)
        self.hr_tree.bind("<Double-1>", lambda e: self._open_hr_reference())

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
        ttk.Button(btn_frame, text="Open Framework Source", command=self._open_hr_source).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Open Linked Case", command=self._open_hr_reference).pack(side=tk.RIGHT)

        self.hr_detail_text = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, font=("Consolas", 10),
            bg=COLORS["input_bg"], fg=COLORS["text_primary"], relief=tk.FLAT, height=10
        )
        self.hr_detail_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

    def _build_disclosure_integrity_tab(self, parent):
        ttk.Label(
            parent,
            text="Disclosure Integrity Scan (Abuse of Process / Charter / Prosecution / Human Rights)",
            style="Subheader.TLabel",
        ).pack(anchor=tk.W, padx=8, pady=(8, 4))

        ctrl = ttk.Frame(parent)
        ctrl.pack(fill=tk.X, padx=8, pady=(0, 4))
        ttk.Button(
            ctrl,
            text="Run Disclosure Integrity Scan",
            command=self._run_disclosure_integrity_scan,
            style="Warning.TButton",
        ).pack(side=tk.LEFT)

        self.disclosure_summary_label = ttk.Label(
            ctrl,
            text="Run the scan to generate consolidated integrity findings.",
            foreground=COLORS["text_secondary"],
        )
        self.disclosure_summary_label.pack(side=tk.RIGHT)

        frame = ttk.LabelFrame(parent, text="Priority Findings", padding=6)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        cols = ("area", "severity", "signal")
        self.disclosure_tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        self.disclosure_tree.heading("area", text="Area")
        self.disclosure_tree.heading("severity", text="Severity")
        self.disclosure_tree.heading("signal", text="Signal")
        self.disclosure_tree.column("area", width=220)
        self.disclosure_tree.column("severity", width=120, anchor=tk.CENTER)
        self.disclosure_tree.column("signal", width=780)
        self.disclosure_tree.pack(fill=tk.BOTH, expand=True)
        self.disclosure_tree.bind("<<TreeviewSelect>>", self._on_disclosure_signal_select)

        self.disclosure_detail_text = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, font=("Consolas", 10),
            bg=COLORS["input_bg"], fg=COLORS["text_primary"], relief=tk.FLAT, height=10
        )
        self.disclosure_detail_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.disclosure_rows = []

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
        categories = sorted({
            _normalize_legal_term(term_key, term_data)["category"]
            for term_key, term_data in LEGAL_DICTIONARY.items()
        })
        cat_combo = ttk.Combobox(search_frame, textvariable=self.dict_cat_var, width=18,
                                  values=["All"] + categories,
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
        home_dir = os.path.expanduser("~")
        downloads_dir = os.path.join(home_dir, "Downloads")
        initial_dir = downloads_dir if os.path.isdir(downloads_dir) else home_dir
        filetypes = [
            ("All Files", "*"),
            ("All Supported", ("*.pdf", "*.docx", "*.txt", "*.md", "*.rtf")),
            ("PDF Files", "*.pdf"),
            ("Word Documents", "*.docx"),
            ("Text Files", ("*.txt", "*.md", "*.rtf")),
        ]
        path = filedialog.askopenfilename(
            title="Open Legal Document",
            filetypes=filetypes,
            initialdir=initial_dir,
        )
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
            self._save_last_document_state()
            self.root.after(50, self._autorun_full_analysis)
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
            self._save_last_document_state()
            dlg.destroy()
            self.root.after(50, self._autorun_full_analysis)

        ttk.Button(dlg, text="Load Document", command=_confirm, style="Success.TButton").pack(pady=8)

    # ══════════════════════════════════════════════════════════════════════════
    # ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════

    def _check_document_loaded(self):
        if not self.document_text.strip():
            messagebox.showwarning("No Document", "Please load a document first (File → Open or Paste Text).")
            return False
        return True

    def _save_last_document_state(self):
        # Do not persist raw disclosure content or metadata to disk.
        try:
            if os.path.exists(LAST_DOCUMENT_STATE_PATH):
                os.remove(LAST_DOCUMENT_STATE_PATH)
        except OSError:
            pass

    def _restore_last_document_state(self):
        # Legacy state files are removed on startup rather than restored.
        self._save_last_document_state()

    def _on_close(self):
        self._save_last_document_state()
        self.root.destroy()

    def _results_for_display(self):
        return self.display_results or self.analysis_results

    def _autorun_full_analysis(self):
        try:
            self._run_full_analysis(notify=False)
        except Exception as e:
            self.status_var.set("Autorun analysis failed")
            messagebox.showerror("Analysis Error", f"Automatic analysis failed:\n{e}")

    def _run_full_analysis(self, notify=True):
        if not self._check_document_loaded():
            return

        self.status_var.set("Running full analysis...")
        self.progress["value"] = 0
        self.root.update_idletasks()

        # Charter analysis
        self.progress["value"] = 15
        self.analysis_results = self.charter_analyzer.analyze_document(self.document_text)
        self.display_results = scrub_party_identifiers(self.analysis_results)
        self._populate_charter_tab()
        self._populate_interaction_tab()
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
        self._populate_misconduct_tabs()
        self._populate_xref_tab()
        self._populate_human_rights_tab()
        self._populate_disclosure_integrity_tab()
        self.root.update_idletasks()

        # Highlight document
        self._highlight_document()
        self._save_last_document_state()

        self.progress["value"] = 100
        self.status_var.set("Full analysis complete.")
        if notify:
            messagebox.showinfo("Analysis Complete", "Full document analysis is complete.\nReview all tabs for results.")

    def _run_charter_only(self):
        if not self._check_document_loaded():
            return
        self.status_var.set("Running Charter breach analysis...")
        self.progress["value"] = 0
        self.root.update_idletasks()

        self.analysis_results = self.charter_analyzer.analyze_document(self.document_text)
        self.display_results = scrub_party_identifiers(self.analysis_results)
        self._populate_charter_tab()
        self._populate_interaction_tab()
        self._populate_misconduct_tabs()
        self._populate_xref_tab()
        self._populate_human_rights_tab()
        self._populate_disclosure_integrity_tab()
        self._highlight_document()
        self._save_last_document_state()

        self.progress["value"] = 100
        self.status_var.set("Charter analysis complete.")

    def _run_terminology(self):
        if not self._check_document_loaded():
            return
        self._do_terminology_analysis()
        self._highlight_document()
        self.status_var.set("Terminology analysis complete.")

    def _run_deflection(self):
        if not self._check_document_loaded():
            return
        self._do_deflection_analysis()
        self._highlight_document()
        self.status_var.set("Deflection analysis complete.")

    def _run_disclosure_integrity_scan(self):
        if not self._check_document_loaded():
            return
        self.status_var.set("Running disclosure integrity scan...")
        self.progress["value"] = 0
        self.root.update_idletasks()

        self.analysis_results = self.charter_analyzer.analyze_document(self.document_text)
        self.display_results = scrub_party_identifiers(self.analysis_results)
        self.progress["value"] = 65
        self._populate_charter_tab()
        self._populate_interaction_tab()
        self._populate_misconduct_tabs()
        self._populate_human_rights_tab()
        self._populate_disclosure_integrity_tab()
        self._highlight_document()
        self._save_last_document_state()

        self.progress["value"] = 100
        self.status_var.set("Disclosure integrity scan complete.")
        self.notebook.select(self.disclosure_tab)

    def _clean_flag_phrase(self, phrase):
        """Remove rule annotations so scanning uses the actual text to match."""
        return re.sub(r"\s*\([^)]*\)", "", phrase).strip()

    def _is_context_only_phrase(self, phrase):
        """Skip entries that are guidance notes rather than literal search terms."""
        lowered = phrase.lower()
        markers = [
            "when ", "unless ", "mid-sentence", "sentence context", "abbreviating",
            "strictly,", "strictly ", "in preference to",
        ]
        return any(marker in lowered for marker in markers)

    def _find_phrase_matches(self, text, phrase):
        """Find case-insensitive phrase matches with word boundaries."""
        cleaned = self._clean_flag_phrase(phrase)
        if not cleaned or self._is_context_only_phrase(phrase):
            return []

        pattern = r"\s+".join(re.escape(part) for part in cleaned.split())
        if re.search(r"\w", cleaned):
            pattern = rf"(?<!\w){pattern}(?!\w)"
        return list(re.finditer(pattern, text, re.IGNORECASE))

    def _collect_issue_snippets(self, text, matches, limit=5):
        snippets = []
        for match in matches[:limit]:
            snippet = text[max(0, match.start() - 25):min(len(text), match.end() + 25)].strip()
            if snippet:
                snippets.append(snippet.replace("\n", " "))
        return snippets

    def _add_issue(self, bucket, key, payload, matches):
        if not matches:
            return

        spans = [(match.start(), match.end()) for match in matches]
        existing = bucket.get(key)
        if existing:
            existing["count"] += len(matches)
            existing["spans"].extend(spans)
            existing["matches"].extend(self._collect_issue_snippets(self.document_text, matches))
            existing["matches"] = existing["matches"][:5]
            return

        payload["count"] = len(matches)
        payload["spans"] = spans
        payload["matches"] = self._collect_issue_snippets(self.document_text, matches)
        bucket[key] = payload

    def _do_terminology_analysis(self):
        """Run terminology and consistency analysis."""
        issue_map = {}
        text = self.document_text

        # Check dictionary misuses
        for term_key, term_data in LEGAL_DICTIONARY.items():
            normalized = _normalize_legal_term(term_key, term_data)
            canonical_term = term_key.replace("_", " ").lower()
            preferred_form = normalized["preferred_form"]
            for misuse in normalized["misuses"]:
                cleaned_misuse = self._clean_flag_phrase(misuse)
                if not cleaned_misuse:
                    continue
                if cleaned_misuse.lower() in {canonical_term, preferred_form.lower()}:
                    continue
                matches = self._find_phrase_matches(text, misuse)
                self._add_issue(issue_map, (cleaned_misuse.lower(), "misuse"), {
                        "term": misuse,
                        "type": "misuse",
                        "issue": f"'{misuse}' is not the correct Canadian legal term",
                        "correct_form": preferred_form,
                        "source": normalized["source"],
                        "definition": normalized["definition"],
                        "category": normalized["category"],
                    }, matches)

        # Check terminology rules
        for rule_key, rule_data in TERMINOLOGY_RULES.items():
            for incorrect in rule_data.get("incorrect", []):
                cleaned_incorrect = self._clean_flag_phrase(incorrect)
                if not cleaned_incorrect:
                    continue
                if cleaned_incorrect.lower() == rule_data["correct"].lower():
                    continue
                matches = self._find_phrase_matches(text, incorrect)
                self._add_issue(issue_map, (cleaned_incorrect.lower(), "spelling/format"), {
                        "term": cleaned_incorrect,
                        "type": "spelling/format",
                        "issue": f"Incorrect form — {rule_data.get('note', '')}",
                        "correct_form": rule_data["correct"],
                        "source": "Terminology Standards",
                        "definition": rule_data.get("note", ""),
                        "category": "consistency",
                    }, matches)

        # Check for American vs Canadian terms
        american_to_canadian = {
            "probable cause": "reasonable grounds",
            "due process": "duty of fairness / principles of fundamental justice",
            "defense": "defence",
            "offense": "offence",
            "suppression of evidence": "exclusion of evidence",
            "miranda rights": "right to counsel (s.10(b) Charter)",
            "prosecutor": "the prosecution",
            "district attorney": "prosecution counsel",
            "grand jury": "preliminary inquiry",
            "beyond shadow of a doubt": "beyond a reasonable doubt",
            "fruit of the poisonous tree": "derivative evidence",
        }
        for american, canadian in american_to_canadian.items():
            matches = self._find_phrase_matches(text, american)
            self._add_issue(issue_map, (american.lower(), "americanism"), {
                    "term": american,
                    "type": "americanism",
                    "issue": f"American legal term — use Canadian equivalent",
                    "correct_form": canadian,
                    "source": "Canadian Legal Usage",
                    "definition": f"The Canadian equivalent is '{canadian}'.",
                    "category": "consistency",
                }, matches)

        self.terminology_issues = sorted(
            issue_map.values(),
            key=lambda issue: (-issue["count"], issue["term"].lower())
        )
        # Populate tree
        self._populate_term_tree()

    def _do_deflection_analysis(self):
        """Run deflection and ambiguity pattern analysis."""
        self.deflection_issues = []
        text = self.document_text

        for pattern_name, pattern_data in DEFLECTION_PATTERNS.items():
            total_count = 0
            matches_detail = []
            spans = []
            for pat in pattern_data["patterns"]:
                matches = list(re.finditer(pat, text, re.IGNORECASE))
                count = len(matches)
                total_count += count
                for m in matches:
                    matches_detail.append(m.group(0).strip())
                    spans.append((m.start(), m.end()))

            if total_count > 0:
                self.deflection_issues.append({
                    "pattern_type": pattern_name.replace("_", " ").title(),
                    "severity": pattern_data["severity"],
                    "count": total_count,
                    "description": pattern_data["description"],
                    "suggestion": pattern_data["suggestion"],
                    "matches": list(dict.fromkeys(matches_detail))[:10],
                    "spans": spans,
                })

        self.deflection_issues.sort(key=lambda issue: (-issue["count"], issue["pattern_type"]))
        self._populate_defl_tree()

    # ── Populate UI Components ────────────────────────────────────────────────

    def _populate_charter_tab(self):
        self._stop_breach_animation()
        results = self._results_for_display()

        # Clear
        for item in self.breach_tree.get_children():
            self.breach_tree.delete(item)
        self.breach_detail_text.delete("1.0", tk.END)
        self.oakes_text.delete("1.0", tk.END)

        breaches = results.get("potential_breaches", [])
        breaches_sorted = sorted(
            breaches,
            key=lambda b: (
                -self._confidence_weight(b.get("confidence_level")),
                -float(b.get("confidence", 0)),
                -len(b.get("breach_indicators", [])),
                -len(b.get("matched_keywords", [])),
                str(b.get("section", "")),
            ),
        )

        if not breaches:
            self.charter_summary_label.config(text="No Charter breaches detected.", foreground=COLORS["success"])
            self._draw_breach_scene(progress=0.0, explosion=0.0, active=False)
            return

        high = sum(1 for b in breaches if b["confidence_level"] == "HIGH")
        med = sum(1 for b in breaches if b["confidence_level"] == "MEDIUM")
        low = sum(1 for b in breaches if b["confidence_level"] == "LOW")
        self.charter_summary_label.config(
            text=f"{len(breaches)} breaches: {high} high, {med} medium, {low} low",
            foreground=COLORS["danger"] if high > 0 else COLORS["warning"]
        )
        self._start_breach_animation()

        for breach in breaches_sorted:
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
        oakes = results.get("oakes_analysis")
        if oakes:
            self.oakes_text.insert(tk.END, f"OAKES TEST ANALYSIS\n{'='*50}\n\n")
            self.oakes_text.insert(tk.END, f"Summary: {oakes.get('analysis_summary', 'N/A')}\n\n")
            self.oakes_text.insert(tk.END, f"Justification Likely: {oakes.get('justification_likely', 'N/A')}\n\n")
            self.oakes_text.insert(tk.END, f"Applicable on this record: {oakes.get('applicable', 'N/A')}\n\n")
            for step_id, step in oakes.get("steps", {}).items():
                self.oakes_text.insert(tk.END, f"Step: {step['question']}\n")
                self.oakes_text.insert(tk.END, f"  Analysis: {step.get('analysis', '')}\n\n")

    def _confidence_weight(self, level):
        return {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get((level or "").upper(), 0)

    def _severity_weight(self, level):
        normalized = (level or "").upper()
        return {
            "HIGH": 3,
            "HIGH CONCERN": 3,
            "MEDIUM": 2,
            "REVIEW REQUIRED": 2,
            "LOW": 1,
            "NO EXPRESS BAD-FAITH INDICATOR": 0,
        }.get(normalized, 0)

    def _start_breach_animation(self):
        self.breach_animation_running = True
        self.breach_animation_frame = 0
        self._animate_breach_scene()

    def _stop_breach_animation(self):
        self.breach_animation_running = False
        if self.breach_animation_after_id is not None:
            self.root.after_cancel(self.breach_animation_after_id)
            self.breach_animation_after_id = None

    def _animate_breach_scene(self):
        if not self.breach_animation_running:
            return

        total_frames = 60
        travel_frames = 28
        linger_frames = 16
        frame = self.breach_animation_frame % total_frames
        progress = min(frame / max(travel_frames, 1), 1.0)
        explosion = 0.0
        if frame >= travel_frames:
            explosion = min((frame - travel_frames) / 10.0, 1.0)
        if frame >= travel_frames + linger_frames:
            explosion = max(0.0, 1.0 - ((frame - travel_frames - linger_frames) / 6.0))

        self._draw_breach_scene(progress=progress, explosion=explosion, active=True)

        self.breach_animation_frame += 1
        self.breach_animation_after_id = self.root.after(70, self._animate_breach_scene)

    def _draw_breach_scene(self, progress, explosion, active):
        canvas = self.breach_canvas
        width = max(canvas.winfo_width(), 760)
        height = max(canvas.winfo_height(), 150)
        canvas.delete("all")

        sky = "#120b11" if active else "#151823"
        canvas.create_rectangle(0, 0, width, height, fill=sky, outline="")
        canvas.create_rectangle(0, height * 0.72, width, height, fill="#23181c", outline="")

        # Penitentiary
        prison_x0 = width - 250
        prison_y0 = 38
        prison_x1 = width - 38
        prison_y1 = height - 20
        canvas.create_rectangle(prison_x0, prison_y0, prison_x1, prison_y1, fill="#4c535f", outline="#87909d", width=2)
        tower_w = 34
        for tx in (prison_x0 + 18, prison_x1 - 18 - tower_w):
            canvas.create_rectangle(tx, 18, tx + tower_w, prison_y1, fill="#59616e", outline="#98a2b0", width=2)
            canvas.create_polygon(tx - 4, 18, tx + tower_w / 2, 2, tx + tower_w + 4, 18, fill="#6b7382", outline="#98a2b0")
        for bx in range(int(prison_x0 + 22), int(prison_x1 - 20), 28):
            canvas.create_line(bx, prison_y0 + 18, bx, prison_y1 - 16, fill="#9fa8b5", width=1)
        for wy in range(int(prison_y0 + 22), int(prison_y1 - 14), 24):
            canvas.create_line(prison_x0 + 14, wy, prison_x1 - 14, wy, fill="#707987", width=1)
        for fx in range(int(prison_x0 - 28), int(prison_x1 + 18), 12):
            canvas.create_line(fx, prison_y1, fx + 8, prison_y1 - 18, fill="#9ca5b3", width=2)
        canvas.create_line(prison_x0 - 30, prison_y1, prison_x1 + 25, prison_y1, fill="#808996", width=2)

        # Reaper based on supplied front-facing hooded reference
        reaper_x = 124
        reaper_y = height - 10
        robe_fill = "#111216"
        robe_edge = "#373b45"
        skull_fill = "#f0ede5"
        shadow_fill = "#0a0b0e"

        # outer hood and shoulders
        canvas.create_polygon(
            reaper_x - 52, reaper_y - 10,
            reaper_x - 42, reaper_y - 56,
            reaper_x - 24, reaper_y - 112,
            reaper_x + 2, reaper_y - 136,
            reaper_x + 30, reaper_y - 128,
            reaper_x + 52, reaper_y - 102,
            reaper_x + 68, reaper_y - 54,
            reaper_x + 82, reaper_y - 8,
            reaper_x + 48, reaper_y + 18,
            reaper_x - 10, reaper_y + 18,
            fill=robe_fill, outline=robe_edge, width=2, smooth=True
        )
        # hood cavity
        canvas.create_polygon(
            reaper_x - 18, reaper_y - 108,
            reaper_x + 6, reaper_y - 126,
            reaper_x + 28, reaper_y - 108,
            reaper_x + 18, reaper_y - 60,
            reaper_x - 10, reaper_y - 60,
            fill=shadow_fill, outline=""
        )
        # skull
        canvas.create_oval(reaper_x - 4, reaper_y - 102, reaper_x + 24, reaper_y - 62, fill=skull_fill, outline="")
        canvas.create_polygon(
            reaper_x + 8, reaper_y - 58,
            reaper_x - 2, reaper_y - 40,
            reaper_x + 18, reaper_y - 40,
            fill=skull_fill, outline=""
        )
        canvas.create_arc(reaper_x - 2, reaper_y - 100, reaper_x + 12, reaper_y - 72, start=180, extent=180, fill=shadow_fill, outline="")
        canvas.create_arc(reaper_x + 10, reaper_y - 100, reaper_x + 24, reaper_y - 72, start=180, extent=180, fill=shadow_fill, outline="")
        canvas.create_polygon(
            reaper_x + 10, reaper_y - 74,
            reaper_x + 6, reaper_y - 64,
            reaper_x + 14, reaper_y - 64,
            fill=shadow_fill, outline=""
        )
        for tooth_x in range(-2, 19, 5):
            canvas.create_line(reaper_x + tooth_x, reaper_y - 50, reaper_x + tooth_x, reaper_y - 42, fill=shadow_fill, width=1)
        canvas.create_line(reaper_x + 1, reaper_y - 50, reaper_x + 18, reaper_y - 50, fill=shadow_fill, width=2)

        # shoulder folds
        canvas.create_arc(reaper_x - 44, reaper_y - 64, reaper_x + 8, reaper_y - 18, start=190, extent=95, style=tk.ARC, outline="#d9dbe1", width=2)
        canvas.create_arc(reaper_x - 20, reaper_y - 62, reaper_x + 40, reaper_y - 16, start=195, extent=90, style=tk.ARC, outline="#d9dbe1", width=2)
        canvas.create_arc(reaper_x + 6, reaper_y - 64, reaper_x + 58, reaper_y - 18, start=200, extent=85, style=tk.ARC, outline="#d9dbe1", width=2)

        # dripping body
        body_points = [
            reaper_x - 34, reaper_y - 18,
            reaper_x - 28, reaper_y + 6,
            reaper_x - 24, reaper_y - 2,
            reaper_x - 18, reaper_y + 30,
            reaper_x - 12, reaper_y - 8,
            reaper_x - 4, reaper_y + 40,
            reaper_x + 4, reaper_y - 6,
            reaper_x + 10, reaper_y + 52,
            reaper_x + 18, reaper_y - 8,
            reaper_x + 26, reaper_y + 24,
            reaper_x + 34, reaper_y - 2,
            reaper_x + 40, reaper_y + 16,
            reaper_x + 44, reaper_y - 18,
        ]
        canvas.create_polygon(*body_points, fill=robe_fill, outline=robe_edge, width=2, smooth=True)

        # left dripping sleeve / throwing arm
        arm_tip_x = reaper_x + 58
        arm_tip_y = reaper_y - 54
        canvas.create_polygon(
            reaper_x + 28, reaper_y - 26,
            reaper_x + 62, reaper_y - 34,
            reaper_x + 78, reaper_y - 58,
            reaper_x + 64, reaper_y - 6,
            reaper_x + 38, reaper_y + 8,
            fill=robe_fill, outline=robe_edge, width=2, smooth=True
        )
        canvas.create_line(reaper_x + 44, reaper_y - 10, arm_tip_x, arm_tip_y, fill="#d9dbe1", width=3)

        # right hanging sleeve
        canvas.create_polygon(
            reaper_x - 40, reaper_y - 24,
            reaper_x - 72, reaper_y - 8,
            reaper_x - 86, reaper_y + 28,
            reaper_x - 66, reaper_y + 8,
            reaper_x - 54, reaper_y + 24,
            reaper_x - 32, reaper_y + 2,
            fill=robe_fill, outline=robe_edge, width=2, smooth=True
        )
        canvas.create_text(reaper_x + 2, 18, text="REAPER", fill="#8d95a3", font=("Segoe UI", 9, "bold"))

        # Molotov path
        start_x = arm_tip_x
        start_y = arm_tip_y
        target_x = prison_x0 + 72
        target_y = prison_y0 + 26
        arc_height = 85
        molotov_x = start_x + (target_x - start_x) * progress
        molotov_y = start_y + (target_y - start_y) * progress - arc_height * (4 * progress * (1 - progress))
        trail_color = "#ff8f3a" if active else "#5e6472"
        if active:
            canvas.create_line(start_x, start_y, molotov_x, molotov_y, fill=trail_color, width=2, smooth=True)
        # bottle body
        canvas.create_polygon(
            molotov_x - 8, molotov_y + 6,
            molotov_x - 5, molotov_y - 8,
            molotov_x + 5, molotov_y - 8,
            molotov_x + 8, molotov_y + 6,
            fill="#4fae76", outline="#e4e8d0", width=1
        )
        canvas.create_rectangle(molotov_x - 2, molotov_y - 14, molotov_x + 2, molotov_y - 8, fill="#d7c6a7", outline="")
        canvas.create_polygon(
            molotov_x + 1, molotov_y - 18,
            molotov_x + 11, molotov_y - 12,
            molotov_x + 4, molotov_y - 6,
            fill="#e6ddd0", outline=""
        )
        canvas.create_polygon(
            molotov_x + 8, molotov_y - 24,
            molotov_x + 20, molotov_y - 14,
            molotov_x + 10, molotov_y - 6,
            fill="#ffd05a", outline=""
        )
        canvas.create_polygon(
            molotov_x + 11, molotov_y - 30,
            molotov_x + 26, molotov_y - 16,
            molotov_x + 13, molotov_y - 8,
            fill="#ff5a24", outline=""
        )
        canvas.create_text(molotov_x + 10, molotov_y + 18, text="MOLOTOV", fill="#f0b35d", font=("Segoe UI", 7, "bold"))

        if explosion > 0:
            impact_x = target_x + 20
            impact_y = target_y + 18
            radius = 18 + 36 * explosion
            canvas.create_oval(impact_x - radius, impact_y - radius * 0.8, impact_x + radius, impact_y + radius * 0.8,
                               fill="#ffb23d", outline="")
            inner = radius * 0.55
            canvas.create_oval(impact_x - inner, impact_y - inner * 0.8, impact_x + inner, impact_y + inner * 0.8,
                               fill="#ff5a1f", outline="")
            flame_base = prison_y1 - 8
            for idx, fx in enumerate((prison_x0 + 42, prison_x0 + 72, prison_x0 + 104, prison_x0 + 138)):
                flame_h = 18 + (idx % 2) * 10 + int(16 * explosion)
                canvas.create_polygon(
                    fx, flame_base,
                    fx + 10, flame_base - flame_h,
                    fx + 22, flame_base,
                    fill="#ff7128", outline=""
                )
                canvas.create_polygon(
                    fx + 4, flame_base,
                    fx + 10, flame_base - flame_h * 0.6,
                    fx + 16, flame_base,
                    fill="#ffd257", outline=""
                )
            smoke_r = 14 + 22 * explosion
            for sx, sy in ((impact_x + 20, impact_y - 26), (impact_x + 46, impact_y - 12), (impact_x + 12, impact_y - 54)):
                canvas.create_oval(sx - smoke_r, sy - smoke_r, sx + smoke_r, sy + smoke_r, fill="#47424f", outline="")

    def _on_breach_select(self, event):
        results = self._results_for_display()
        sel = self.breach_tree.selection()
        if not sel:
            return

        vals = self.breach_tree.item(sel[0], "values")
        section = vals[0]

        # Find breach data
        breach = None
        for b in results.get("potential_breaches", []):
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
        self.breach_detail_text.insert(tk.END, self._plain_language_breach_explanation(breach))
        self.breach_detail_text.insert(tk.END, "\n")

        legal_articulation = breach.get("legal_articulation")
        if legal_articulation:
            self.breach_detail_text.insert(tk.END, "GOVERNING TEST:\n")
            self.breach_detail_text.insert(tk.END, f"  {legal_articulation.get('governing_test', '')}\n\n")
            self.breach_detail_text.insert(tk.END, "EXPRESS FINDING:\n")
            self.breach_detail_text.insert(tk.END, f"  {legal_articulation.get('conclusion', '')}\n\n")
            authorities = legal_articulation.get("authorities", [])
            if authorities:
                self.breach_detail_text.insert(tk.END, "LEADING AUTHORITIES:\n")
                for authority in authorities:
                    self.breach_detail_text.insert(tk.END, f"  • {authority}\n")
                self.breach_detail_text.insert(tk.END, "\n")

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
            if test.get("analysis"):
                self.breach_detail_text.insert(tk.END, f"   Analysis: {test['analysis']}\n")
            if test.get("authorities"):
                self.breach_detail_text.insert(tk.END, f"   Authorities: {'; '.join(test['authorities'])}\n")

        # Remedies
        self.breach_detail_text.insert(tk.END, "\n\nREMEDIES:\n")
        for r in results.get("remedies", []):
            self.breach_detail_text.insert(tk.END, f"\n  💊 {r['description']}\n")
            if r.get("options"):
                for opt in r["options"]:
                    self.breach_detail_text.insert(tk.END, f"    — {opt}\n")

        self.breach_detail_text.insert(tk.END, "\n\nSTATE-CONDUCT REVIEW:\n")
        officer = results.get("officer_conduct_assessment")
        bad_faith = results.get("bad_faith_assessment")
        police_indicators = results.get("police_misconduct_indicators", [])

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
            results.get("cross_references", {})
            .get("canlii", {})
            .get(section, {})
        )
        if canlii_for_section.get("search_urls"):
            for label, url in canlii_for_section["search_urls"].items():
                self.breach_detail_text.insert(tk.END, f"  • CanLII {label.title()}: {url}\n")

        cln_for_section = (
            results.get("cross_references", {})
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

    def _plain_language_breach_explanation(self, breach):
        intro_by_section = {
            "7": "Section 7 asks whether the state took away liberty, security, or bodily autonomy in a way that violates basic fairness.",
            "8": "Section 8 asks whether the state searched or seized something without lawful and reasonable justification.",
            "9": "Section 9 asks whether the detention or arrest was arbitrary instead of grounded in objective facts.",
            "10(a)": "Section 10(a) asks whether the person was promptly told why they were being arrested or detained.",
            "10(b)": "Section 10(b) asks whether the person was given a real chance to contact a lawyer without delay.",
            "15(1)": "Section 15(1) asks whether state action imposed unequal treatment tied to a protected personal ground such as disability, race, or sex.",
            "24": "Section 24 asks what remedy the court could give if a Charter breach is proven.",
        }
        lines = ["PLAIN-LANGUAGE GUIDE", "-" * 60]
        lines.append(intro_by_section.get(breach.get("section"), "This section asks whether the factual record satisfies the legal test for a Charter breach."))

        tests = list((breach.get("applicable_tests") or {}).values())
        if tests:
            lines.append("")
            lines.append("What the analyzer is checking:")
            for test in tests:
                status = (test.get("status") or "").replace("_", " ")
                if test.get("status") == "potential_issue":
                    verdict = "The current text contains facts that may support this part of the test."
                else:
                    verdict = "The current text does not clearly support this part of the test yet."
                lines.append(f"  • {test.get('question', 'Unnamed legal test')}")
                lines.append(f"    Result: {verdict}")
                if test.get("identified_issues"):
                    lines.append(f"    Key facts noticed: {', '.join(test['identified_issues'])}")
                if status:
                    lines.append(f"    Technical status: {status.title()}")

        legal_articulation = breach.get("legal_articulation") or {}
        if legal_articulation.get("conclusion"):
            lines.append("")
            lines.append("Bottom line:")
            lines.append(f"  {legal_articulation['conclusion']}")

        return "\n".join(lines) + "\n"


    def _on_interaction_select(self, event):
        sel = self.interaction_tree.selection()
        if not sel: return
        vals = self.interaction_tree.item(sel[0], "values")
        messagebox.showinfo("Interaction Detail", f"Sections: {vals[0]}\nSeverity: {vals[1]}\n\n{vals[2]}")

    def _populate_interaction_tab(self):
        results = self._results_for_display()
        # Clear
        for item in self.interaction_tree.get_children():
            self.interaction_tree.delete(item)
        for item in self.flag_tree.get_children():
            self.flag_tree.delete(item)
        self.conduct_text.config(state=tk.NORMAL)
        self.conduct_text.delete("1.0", tk.END)

        breaches = results.get("potential_breaches", [])
        breach_map = {
            b.get("section"): b
            for b in sorted(
                breaches,
                key=lambda b: (-self._confidence_weight(b.get("confidence_level")), -float(b.get("confidence", 0))),
            )
        }

        self.conduct_text.insert(tk.END, "HOW THIS TIES TOGETHER (FOR FACT-CHECK)\n")
        self.conduct_text.insert(tk.END, f"{'='*72}\n")
        self.conduct_text.insert(tk.END, "1) Start with Charter breach findings ranked by confidence.\n")
        self.conduct_text.insert(tk.END, "2) Link each breach to conduct signals (official bad faith / prosecution review).\n")
        self.conduct_text.insert(tk.END, "3) Verify each claim using the listed CanLII and Criminal Law Notebook references.\n")
        self.conduct_text.insert(tk.END, "4) Confirm the document text itself contains the matched indicators quoted in each section detail.\n\n")
        self.conduct_text.insert(tk.END, "RELEVANCE ORDER (CHARTER -> MISCONDUCT NEXUS)\n")
        for section, breach in breach_map.items():
            self.conduct_text.insert(
                tk.END,
                f"  • Section {section} ({breach.get('confidence_level', 'N/A')}, "
                f"{int(float(breach.get('confidence', 0)) * 100)}%): {breach.get('title', '')}\n",
            )
        self.conduct_text.insert(tk.END, "\n")

        # Interactions (sorted by severity)
        interactions_sorted = sorted(
            results.get("breach_interactions", []),
            key=lambda it: (-self._severity_weight(it.get("severity")), ", ".join(it.get("sections", []))),
        )
        for interaction in interactions_sorted:
            sections = ", ".join(interaction["sections"])
            self.interaction_tree.insert("", tk.END, values=(sections, interaction["severity"], interaction["description"]))
            self.interaction_tree.see(self.interaction_tree.get_children()[-1])

        # Specific Flags
        for flag in results.get("specific_flags", []):
            matches = ", ".join(flag["matches"])
            self.flag_tree.insert("", tk.END, values=(flag["label"], flag["description"], matches))

        # State Conduct
        conduct = results.get("officer_conduct_assessment")
        bad_faith = results.get("bad_faith_assessment")
        crown_conduct = results.get("crown_conduct_assessment")
        if conduct:
            self.conduct_text.insert(tk.END, f"SERIOUSNESS: {conduct['seriousness']}\n")
            self.conduct_text.insert(tk.END, f"LEGAL BASIS: {conduct['legal_basis']}\n")
            self.conduct_text.insert(tk.END, f"\nASSESSMENT:\n{conduct['assessment']}\n")
            self.conduct_text.insert(tk.END, "\n")
        elif not bad_faith and not crown_conduct:
            self.conduct_text.insert(tk.END, "No specific state-conduct patterns identified based on current criteria.")

        if bad_faith:
            self.conduct_text.insert(tk.END, f"BAD FAITH LEVEL: {bad_faith['level']} (score {bad_faith['score']})\n")
            self.conduct_text.insert(tk.END, f"LEGAL BASIS: {bad_faith['legal_basis']}\n")
            self.conduct_text.insert(tk.END, f"\nBAD FAITH ASSESSMENT:\n{bad_faith['assessment']}\n")
            self.conduct_text.insert(tk.END, "\nBAD FAITH FINDINGS:\n")
            for finding in bad_faith.get("findings", []):
                self.conduct_text.insert(tk.END, f"  • {finding['label']}: {finding['rationale']}\n")
                if finding.get("matches"):
                    self.conduct_text.insert(tk.END, f"    Matches: {', '.join(finding['matches'])}\n")
            self.conduct_text.insert(tk.END, "\nCHARTER SOURCES:\n")
            for source in bad_faith.get("charter_sources", []):
                self.conduct_text.insert(tk.END, f"  • {source}\n")
            self.conduct_text.insert(tk.END, "\nPOLICING LEGISLATION SOURCES:\n")
            for source in bad_faith.get("policing_sources", []):
                self.conduct_text.insert(tk.END, f"  • {source}\n")

        if crown_conduct:
            self.conduct_text.insert(tk.END, "\nPROSECUTION REVIEW ASSESSMENT:\n")
            self.conduct_text.insert(tk.END, f"LEVEL: {crown_conduct['level']} (score {crown_conduct['score']})\n")
            self.conduct_text.insert(tk.END, f"LEGAL BASIS: {crown_conduct['legal_basis']}\n")
            self.conduct_text.insert(tk.END, f"\nASSESSMENT:\n{crown_conduct['assessment']}\n")
            if crown_conduct.get("findings"):
                self.conduct_text.insert(tk.END, "\nPROSECUTION FINDINGS:\n")
                for finding in crown_conduct["findings"]:
                    self.conduct_text.insert(tk.END, f"  • {finding['label']}: {finding['rationale']}\n")
                    if finding.get("matches"):
                        self.conduct_text.insert(tk.END, f"    Matches: {', '.join(finding['matches'])}\n")
            self.conduct_text.insert(tk.END, "\nPROSECUTION SOURCES:\n")
            for source in crown_conduct.get("sources", []):
                self.conduct_text.insert(tk.END, f"  • {source}\n")

        if (
            (conduct and conduct['seriousness'] == "HIGH")
            or (bad_faith and bad_faith["level"] == "HIGH")
            or (crown_conduct and crown_conduct["level"] == "HIGH CONCERN")
        ):
            self.conduct_text.config(fg=COLORS["danger"])
        else:
            self.conduct_text.config(fg=COLORS["text_primary"])

    def _populate_misconduct_tabs(self):
        results = self._results_for_display()
        self._populate_indicator_tree(
            self.police_tree,
            results.get("police_misconduct_indicators", []),
        )
        self.police_detail_text.delete("1.0", tk.END)
        self.police_detail_text.insert(tk.END, "Select an official-conduct indicator to inspect it or open its reference URL.")

        self._populate_indicator_tree(
            self.prosecution_tree,
            results.get("prosecutorial_misconduct_indicators", []),
        )
        self.prosecution_detail_text.delete("1.0", tk.END)
        self.prosecution_detail_text.insert(tk.END, "Select a prosecution-review indicator to inspect it or open its reference URL.")

    def _populate_indicator_tree(self, tree, indicators):
        for item in tree.get_children():
            tree.delete(item)
        indicators_sorted = sorted(
            indicators,
            key=lambda item: (
                -self._severity_weight(item.get("severity")),
                item.get("indicator", ""),
            ),
        )
        for indicator in indicators_sorted:
            tree.insert("", tk.END, values=(
                indicator.get("indicator", ""),
                indicator.get("severity", ""),
                indicator.get("source", ""),
            ))

    def _find_indicator(self, category, indicator_name, source_name):
        results = self._results_for_display()
        key = "police_misconduct_indicators" if category == "police" else "prosecutorial_misconduct_indicators"
        for indicator in results.get(key, []):
            if indicator.get("indicator") == indicator_name and indicator.get("source") == source_name:
                return indicator
        return None

    def _on_police_indicator_select(self, event):
        self._display_indicator_detail("police", self.police_tree, self.police_detail_text)

    def _on_prosecution_indicator_select(self, event):
        self._display_indicator_detail("prosecution", self.prosecution_tree, self.prosecution_detail_text)

    def _display_indicator_detail(self, category, tree, text_widget):
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0], "values")
        indicator = self._find_indicator(category, vals[0], vals[2])
        text_widget.delete("1.0", tk.END)
        if not indicator:
            return
        text_widget.insert(tk.END, f"INDICATOR: {indicator.get('indicator', '')}\n")
        text_widget.insert(tk.END, f"SEVERITY: {indicator.get('severity', '')}\n")
        text_widget.insert(tk.END, f"SOURCE: {indicator.get('source', '')}\n")
        text_widget.insert(tk.END, f"URL: {indicator.get('url', '')}\n\n")
        text_widget.insert(tk.END, indicator.get("summary", ""))

    def _open_selected_indicator_url(self, category):
        tree = self.police_tree if category == "police" else self.prosecution_tree
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0], "values")
        indicator = self._find_indicator(category, vals[0], vals[2])
        if indicator and indicator.get("url"):
            webbrowser.open(indicator["url"])

    def _populate_human_rights_tab(self):
        assessment = self._results_for_display().get("human_rights_assessment", {})
        self.hr_summary_text.delete("1.0", tk.END)
        self.hr_detail_text.delete("1.0", tk.END)
        for item in self.hr_tree.get_children():
            self.hr_tree.delete(item)

        if not assessment:
            self.hr_summary_text.insert(tk.END, "Run analysis to generate a UN / national / provincial human-rights assessment.")
            return

        grounds = ", ".join(assessment.get("protected_grounds", [])) or "None detected"
        criteria = ", ".join(assessment.get("criteria", [])) or "No Code criteria strongly triggered"
        source_lines = "\n".join(
            f"{src.get('layer', 'Source')}: {src.get('title', '')} — {src.get('url', '')}"
            for src in assessment.get("sources", [])
        )
        self.hr_summary_text.insert(
            tk.END,
            f"LEVEL: {assessment.get('level', 'N/A')} (score {assessment.get('score', 0)})\n"
            f"PROTECTED GROUNDS: {grounds}\n"
            f"CRITERIA: {criteria}\n\n"
            f"{assessment.get('assessment', '')}\n\n"
            f"FRAMEWORK SOURCES:\n{source_lines}\n"
        )

        findings_sorted = sorted(
            assessment.get("findings", []),
            key=lambda f: (-len(f.get("cases", [])), -len(f.get("layers", [])), f.get("criterion", "")),
        )
        for finding in findings_sorted:
            case_titles = "; ".join(case["title"] for case in finding.get("cases", []))
            self.hr_tree.insert("", tk.END, values=(finding.get("criterion", ""), case_titles))

        self.hr_detail_text.insert(tk.END, "Select a Human Rights Code criterion to inspect the articulation and linked case law.")

    def _get_selected_hr_finding(self):
        results = self._results_for_display()
        sel = self.hr_tree.selection()
        if not sel:
            return None
        vals = self.hr_tree.item(sel[0], "values")
        for finding in results.get("human_rights_assessment", {}).get("findings", []):
            if finding.get("criterion") == vals[0]:
                return finding
        return None

    def _on_hr_select(self, event):
        finding = self._get_selected_hr_finding()
        self.hr_detail_text.delete("1.0", tk.END)
        if not finding:
            return
        self.hr_detail_text.insert(tk.END, f"CRITERION: {finding.get('criterion', '')}\n\n")
        self.hr_detail_text.insert(tk.END, f"{finding.get('summary', '')}\n\n")
        if finding.get("layers"):
            self.hr_detail_text.insert(tk.END, "LAYERS:\n")
            for layer in finding["layers"]:
                self.hr_detail_text.insert(tk.END, f"  • {layer}\n")
            self.hr_detail_text.insert(tk.END, "\n")
        self.hr_detail_text.insert(tk.END, "CASES:\n")
        for case in finding.get("cases", []):
            self.hr_detail_text.insert(tk.END, f"  • {case['title']} — {case['citation']}\n")
            self.hr_detail_text.insert(tk.END, f"    {case['url']}\n")

    def _open_hr_source(self):
        assessment = self._results_for_display().get("human_rights_assessment", {})
        sources = assessment.get("sources", [])
        if sources:
            webbrowser.open(sources[0]["url"])

    def _open_hr_reference(self):
        finding = self._get_selected_hr_finding()
        if finding and finding.get("cases"):
            webbrowser.open(finding["cases"][0]["url"])

    def _populate_disclosure_integrity_tab(self):
        results = self._results_for_display()
        for item in self.disclosure_tree.get_children():
            self.disclosure_tree.delete(item)
        self.disclosure_detail_text.delete("1.0", tk.END)
        self.disclosure_rows = []

        if not results:
            self.disclosure_summary_label.config(
                text="Run analysis to populate disclosure-integrity findings.",
                foreground=COLORS["text_secondary"],
            )
            self.disclosure_detail_text.insert(
                tk.END,
                "No analysis results loaded. Run Full Analysis or Disclosure Integrity Scan first.",
            )
            return

        breaches = results.get("potential_breaches", [])
        high_breaches = [b for b in breaches if b.get("confidence_level") == "HIGH"]
        key_sections = {"7", "8", "9", "10(a)", "10(b)", "15(1)", "24"}
        key_breaches = [
            b for b in breaches if str(b.get("section", "")) in key_sections
        ]

        bad_faith = results.get("bad_faith_assessment", {}) or {}
        crown = results.get("crown_conduct_assessment", {}) or {}
        hr = results.get("human_rights_assessment", {}) or {}

        abuse_level = bad_faith.get("level", "N/A")
        crown_level = crown.get("level", "N/A")
        hr_level = hr.get("level", "N/A")
        risk_color = COLORS["danger"] if (
            abuse_level == "HIGH" or crown_level == "HIGH CONCERN" or hr_level == "HIGH" or len(high_breaches) >= 2
        ) else COLORS["warning"] if high_breaches else COLORS["success"]
        self.disclosure_summary_label.config(
            text=(
                f"Breaches: {len(breaches)} ({len(high_breaches)} high) | "
                f"Abuse: {abuse_level} | Prosecution: {crown_level} | Human Rights: {hr_level}"
            ),
            foreground=risk_color,
        )

        rows = []
        if bad_faith:
            rows.append({
                "area": "Abuse of Process / Official Bad Faith",
                "severity": bad_faith.get("level", "N/A"),
                "signal": bad_faith.get("assessment", "No assessment."),
                "detail": "\n".join(
                    [bad_faith.get("assessment", "")]
                    + [
                        f"- {f.get('label', '')}: {f.get('rationale', '')}"
                        for f in bad_faith.get("findings", [])
                    ]
                ).strip(),
            })

        if crown:
            rows.append({
                "area": "Prosecution Review",
                "severity": crown.get("level", "N/A"),
                "signal": crown.get("assessment", "No assessment."),
                "detail": "\n".join(
                    [crown.get("assessment", "")]
                    + [
                        f"- {f.get('label', '')}: {f.get('rationale', '')}"
                        for f in crown.get("findings", [])
                    ]
                ).strip(),
            })

        if hr:
            rows.append({
                "area": "Human Rights Issues",
                "severity": hr.get("level", "N/A"),
                "signal": f"Score {hr.get('score', 0)} | {hr.get('assessment', '')}",
                "detail": "\n".join(
                    [f"Protected grounds: {', '.join(hr.get('protected_grounds', [])) or 'None'}"]
                    + [f"- {f.get('criterion', '')}: {f.get('summary', '')}" for f in hr.get("findings", [])]
                ).strip(),
            })

        for breach in sorted(
            key_breaches,
            key=lambda b: (-self._confidence_weight(b.get("confidence_level")), str(b.get("section", ""))),
        ):
            rows.append({
                "area": f"Charter Section {breach.get('section', '')}",
                "severity": breach.get("confidence_level", "N/A"),
                "signal": breach.get("title", ""),
                "detail": (
                    f"{breach.get('title', '')}\n\n"
                    f"{breach.get('description', '')}\n\n"
                    f"Matched keywords: {', '.join(k.get('keyword', '') for k in breach.get('matched_keywords', [])[:8])}\n"
                    f"Breach indicators: {', '.join(i.get('type', '') for i in breach.get('breach_indicators', [])[:8])}"
                ),
            })

        if not rows:
            rows.append({
                "area": "Disclosure Integrity",
                "severity": "LOW",
                "signal": "No major abuse / prosecution / human-rights patterns identified on current text.",
                "detail": "Run additional analysis with fuller disclosure and supporting materials for stronger confidence.",
            })

        self.disclosure_rows = rows
        for idx, row in enumerate(rows):
            self.disclosure_tree.insert("", tk.END, iid=str(idx), values=(
                row["area"], row["severity"], row["signal"][:180]
            ))

        self.disclosure_detail_text.insert(
            tk.END,
            "Select a priority finding above to inspect supporting details and pattern signals.",
        )

    def _on_disclosure_signal_select(self, event):
        sel = self.disclosure_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(self.disclosure_rows):
            return
        row = self.disclosure_rows[idx]
        self.disclosure_detail_text.delete("1.0", tk.END)
        self.disclosure_detail_text.insert(tk.END, f"AREA: {row['area']}\n")
        self.disclosure_detail_text.insert(tk.END, f"SEVERITY: {row['severity']}\n\n")
        self.disclosure_detail_text.insert(tk.END, row["detail"])

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
        cross_refs = self._results_for_display().get("cross_references", {})
        canlii_refs = cross_refs.get("canlii", {})

        if canlii_refs:
            for section, refs in sorted(canlii_refs.items(), key=lambda item: str(item[0])):
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
            for section, refs in sorted(cln_refs.items(), key=lambda item: str(item[0])):
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
            for start_idx, end_idx in issue.get("spans", []):
                start = f"1.0+{start_idx}c"
                end = f"1.0+{end_idx}c"
                text_widget.tag_add("deflection", start, end)

        # Highlight term issues
        for issue in self.terminology_issues:
            for start_idx, end_idx in issue.get("spans", []):
                start = f"1.0+{start_idx}c"
                end = f"1.0+{end_idx}c"
                text_widget.tag_add("term_issue", start, end)

    # ══════════════════════════════════════════════════════════════════════════
    # AI INTEGRATION
    # ══════════════════════════════════════════════════════════════════════════

    def _update_ai_status(self):
        """Update AI connection status indicator."""
        if self.ai.is_configured():
            provider_name = "GPT-4" if self.ai.provider == "openai" else "Gemini"
            self.ai_status_label.config(text=f"AI: ✅ Connected ({provider_name})", foreground=COLORS["success"])
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
            normalized = _normalize_legal_term(term_key, term_data)
            if filter_text and filter_text.lower() not in term_key.lower() and filter_text.lower() not in normalized["preferred_form"].lower():
                continue
            if category != "All" and normalized["category"] != category:
                continue

            self.dict_tree.insert("", tk.END, iid=term_key, values=(
                term_key.replace("_", " ").title(),
                normalized["category"],
                normalized["preferred_form"],
                normalized["source"][:50],
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
        normalized = _normalize_legal_term(term_key, term_data)

        self.dict_def_text.insert(tk.END, f"TERM: {term_key.replace('_', ' ').title()}\n")
        self.dict_def_text.insert(tk.END, f"{'═'*60}\n\n")
        self.dict_def_text.insert(tk.END, f"DEFINITION:\n{normalized['definition']}\n\n")
        self.dict_def_text.insert(tk.END, f"PREFERRED FORM: {normalized['preferred_form']}\n")
        self.dict_def_text.insert(tk.END, f"CATEGORY: {normalized['category']}\n")
        self.dict_def_text.insert(tk.END, f"SOURCE: {normalized['source']}\n\n")

        if normalized["aliases"]:
            self.dict_def_text.insert(tk.END, f"ALIASES: {', '.join(normalized['aliases'])}\n")
        if normalized["misuses"]:
            self.dict_def_text.insert(tk.END, f"\n⚠️ MISUSES TO AVOID:\n")
            for m in normalized["misuses"]:
                self.dict_def_text.insert(tk.END, f"  ✗ '{m}'\n")

    def _quick_dict_lookup(self):
        query = self.dict_entry_var.get().strip().lower()
        if not query:
            self.dict_result_label.config(text="Enter a term to look up.")
            return

        # Search dictionary
        for term_key, term_data in LEGAL_DICTIONARY.items():
            normalized = _normalize_legal_term(term_key, term_data)
            if query == term_key.lower() or query in [a.lower() for a in normalized["aliases"]]:
                self.dict_result_label.config(
                    text=f"✓ {normalized['preferred_form']}\n{normalized['definition'][:200]}..."
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

        # AI Provider Selection
        provider_frame = ttk.LabelFrame(dlg, text="AI Provider", padding=10)
        provider_frame.pack(fill=tk.X, padx=10, pady=5)
        
        provider_var = tk.StringVar(value=self.ai.provider)
        ttk.Radiobutton(provider_frame, text="OpenAI (GPT-4)", variable=provider_var, value="openai").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(provider_frame, text="Google (Gemini)", variable=provider_var, value="gemini").pack(side=tk.LEFT, padx=10)

        # OpenAI Frame
        openai_frame = ttk.LabelFrame(dlg, text="OpenAI Configuration", padding=10)
        
        # Gemini Frame
        gemini_frame = ttk.LabelFrame(dlg, text="Gemini Configuration", padding=10)

        def _toggle_provider_frames(*args):
            if provider_var.get() == "openai":
                gemini_frame.pack_forget()
                openai_frame.pack(fill=tk.X, padx=10, pady=5)
            else:
                openai_frame.pack_forget()
                gemini_frame.pack(fill=tk.X, padx=10, pady=5)
        
        provider_var.trace_add("write", _toggle_provider_frames)

        # OpenAI Content
        ttk.Label(openai_frame, text="OpenAI API Key:").pack(anchor=tk.W)
        openai_var = tk.StringVar(value=os.environ.get("OPENAI_API_KEY", "") if self.ai.provider == "openai" else "")
        ttk.Entry(openai_frame, textvariable=openai_var, width=60, show="*").pack(fill=tk.X, pady=2)

        # Gemini Content
        ttk.Label(gemini_frame, text="Gemini API Key:").pack(anchor=tk.W)
        gemini_var = tk.StringVar(value=os.environ.get("GEMINI_API_KEY", "") if self.ai.provider == "gemini" else "")
        ttk.Entry(gemini_frame, textvariable=gemini_var, width=60, show="*").pack(fill=tk.X, pady=2)
        ttk.Label(gemini_frame, text="Get a key at: https://aistudio.google.com/", foreground=COLORS["info"]).pack(anchor=tk.W)

        # Model
        model_frame = ttk.LabelFrame(dlg, text="AI Model", padding=10)
        model_frame.pack(fill=tk.X, padx=10, pady=5)
        
        model_var = tk.StringVar(value=self.ai.model)
        model_dropdown = ttk.Combobox(model_frame, textvariable=model_var, width=30, state="readonly")
        model_dropdown.pack(anchor=tk.W)

        def _update_models(*args):
            if provider_var.get() == "openai":
                model_dropdown['values'] = ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
                if model_var.get() not in model_dropdown['values']:
                    model_var.set("gpt-4o")
            else:
                model_dropdown['values'] = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"]
                if model_var.get() not in model_dropdown['values']:
                    model_var.set("gemini-1.5-pro")

        provider_var.trace_add("write", _update_models)
        _toggle_provider_frames()
        _update_models()

        def _save():
            # Update CanLII
            self.charter_analyzer.canlii.api_key = canlii_var.get().strip()

            # Update AI
            self.ai.provider = provider_var.get()
            self.ai.model = model_var.get()
            
            if self.ai.provider == "openai":
                self.ai.api_key = openai_var.get().strip()
                if self.ai.api_key:
                    self.ai.session.headers.update({"Authorization": f"Bearer {self.ai.api_key}"})
                    os.environ["OPENAI_API_KEY"] = self.ai.api_key
            else:
                self.ai.api_key = gemini_var.get().strip()
                if self.ai.api_key:
                    os.environ["GEMINI_API_KEY"] = self.ai.api_key
                    if hasattr(self.ai, 'GEMINI_AVAILABLE') and self.ai.GEMINI_AVAILABLE:
                        import google.generativeai as genai
                        genai.configure(api_key=self.ai.api_key)

            self._update_ai_status()
            dlg.destroy()
            messagebox.showinfo("Settings Saved", f"AI configured to use {self.ai.provider.upper()} ({self.ai.model}).")

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
                self._results_for_display(), self.document_metadata, path
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
                self._results_for_display(), self.document_metadata, path
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
