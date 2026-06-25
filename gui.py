"""
GUI module — premium professional Tkinter interface.
Updated: Grammar Conversion + Determinism Checker added.
"""
import tkinter as tk
from tkinter import messagebox
import os

from utils import COLORS, FONTS, show_error, show_info
from parser import CFGParser
from ambiguity_checker import AmbiguityChecker
from tree_generator import TreeGenerator
from grammar_converter import GrammarConverter
from determinism_checker import DeterminismChecker

try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
#  Tree Popup
# ══════════════════════════════════════════════════════════════════════

class TreePopup(tk.Toplevel):
    """Popup window for displaying rendered parse tree images."""

    def __init__(self, parent, image_paths, ascii_trees=None):
        super().__init__(parent)
        self.title("Parse Tree Visualization")
        self.configure(bg=COLORS['bg'])
        self.geometry("950x750")
        self.transient(parent)
        self.grab_set()

        header = tk.Frame(self, bg=COLORS['bg'])
        header.pack(fill=tk.X, padx=25, pady=(20, 10))
        tk.Label(header, text="Generated Parse Trees", font=FONTS['heading'],
                 bg=COLORS['bg'], fg=COLORS['accent']).pack(anchor='w')
        tk.Label(header, text="Graphical renderings of all valid parse trees.",
                 font=FONTS['body'], bg=COLORS['bg'], fg=COLORS['fg_muted']).pack(anchor='w', pady=(2, 0))

        container = tk.Frame(self, bg=COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=25, pady=10)

        canvas = tk.Canvas(container, bg=COLORS['bg'], highlightthickness=0)
        v_scrollbar = tk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        h_scrollbar = tk.Scrollbar(container, orient=tk.HORIZONTAL, command=canvas.xview)
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.img_frame = tk.Frame(canvas, bg=COLORS['bg'])
        canvas.create_window((0, 0), window=self.img_frame, anchor='nw')
        self.img_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )

        self.photos = []
        cols = 2
        for i, path in enumerate(image_paths):
            row = i // cols
            col = i % cols
            frame = tk.Frame(self.img_frame, bg=COLORS['card'], bd=0)
            frame.grid(row=row, column=col, sticky='nsew', padx=10, pady=15)
            self.img_frame.columnconfigure(col, weight=1)
            tk.Label(frame, text=f"Parse Tree {i + 1}", font=FONTS['heading'],
                     bg=COLORS['card'], fg=COLORS['accent']).pack(anchor='w', padx=15, pady=(15, 5))
            try:
                img = Image.open(path)
                max_w = 850
                w, h = img.size
                if w > max_w:
                    ratio = max_w / w
                    w, h = int(w * ratio), int(h * ratio)
                    img = img.resize((w, h), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.photos.append(photo)
                lbl = tk.Label(frame, image=photo, bg=COLORS['card'])
                lbl.pack(pady=5)
            except Exception as e:
                tk.Label(frame, text=f"Error loading image: {e}",
                         font=FONTS['body'], bg=COLORS['card'], fg=COLORS['danger']).pack(pady=10)

        if ascii_trees and not image_paths:
            ascii_frame = tk.Frame(self.img_frame, bg=COLORS['card'], bd=0)
            ascii_frame.pack(fill=tk.X, pady=15, padx=5)
            tk.Label(ascii_frame, text="Text-Based Tree Representation",
                     font=FONTS['heading'], bg=COLORS['card'], fg=COLORS['accent']).pack(anchor='w', padx=15, pady=(15, 5))
            for i, ascii_tree in enumerate(ascii_trees):
                tk.Label(ascii_frame, text=f"Tree {i+1}:", font=FONTS['body'],
                         bg=COLORS['card'], fg=COLORS['fg']).pack(anchor='w', padx=15, pady=(10, 0))
                txt = tk.Text(ascii_frame, wrap=tk.NONE, font=FONTS['mono'], height=10,
                              bg=COLORS['input'], fg=COLORS['fg'], relief=tk.FLAT, padx=10, pady=10)
                txt.pack(fill=tk.X, padx=15, pady=5)
                txt.insert(tk.END, ascii_tree)
                txt.config(state=tk.DISABLED)

        self.img_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        btn_frame = tk.Frame(self, bg=COLORS['bg'])
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="Close", command=self.destroy, font=FONTS['button'],
                  bg=COLORS['danger'], fg=COLORS['fg'], relief=tk.FLAT,
                  cursor='hand2', padx=20, pady=5).pack()


# ══════════════════════════════════════════════════════════════════════
#  Main Application
# ══════════════════════════════════════════════════════════════════════

class GrammarAmbiguityApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("Grammar Ambiguity Checker")
        self.geometry("1380x820")
        self.configure(bg=COLORS['bg'])
        self.minsize(1100, 750)

        self.current_result = None
        self.current_parser = None
        self.tab_labels = []
        self.tab_frames = []

        self._build_ui()
        self.load_example()
        self.update_status("Ready — default example loaded.", 'success')

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # ── Top Header ────────────────────────────────────────────────
        top = tk.Frame(self, bg=COLORS['bg'])
        top.pack(side=tk.TOP, fill=tk.X, padx=30, pady=(22, 12))

        title_frame = tk.Frame(top, bg=COLORS['bg'])
        title_frame.pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(title_frame, text="Grammar Ambiguity Checker",
                 font=FONTS['title'], bg=COLORS['bg'], fg=COLORS['accent']).pack(anchor='w')
        tk.Label(title_frame,
                 text="Compiler Construction  ·  Syntax Analysis  ·  Ambiguity & Determinism",
                 font=FONTS['subtitle'], bg=COLORS['bg'], fg=COLORS['fg_muted']).pack(anchor='w', pady=(3, 0))

        sep = tk.Frame(self, bg=COLORS['border'], height=2)
        sep.pack(fill=tk.X, padx=30, pady=(0, 12))

        # ── Main Paned Window ─────────────────────────────────────────
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=COLORS['bg'],
                               sashwidth=6, sashrelief=tk.FLAT, sashpad=3)
        paned.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        # ── Left Panel ────────────────────────────────────────────────
        left = tk.Frame(paned, bg=COLORS['card'], bd=0)
        paned.add(left, width=470)

        left_canvas = tk.Canvas(left, bg=COLORS['card'], highlightthickness=0)
        left_scroll = tk.Scrollbar(left, orient=tk.VERTICAL, command=left_canvas.yview,
                                   bg=COLORS['card'], troughcolor=COLORS['card'])
        left_canvas.configure(yscrollcommand=left_scroll.set)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.left_inner = tk.Frame(left_canvas, bg=COLORS['card'])
        left_canvas.create_window((0, 0), window=self.left_inner, anchor='nw')
        self.left_inner.bind(
            '<Configure>',
            lambda e: left_canvas.configure(scrollregion=left_canvas.bbox('all'))
        )

        # Grammar Input
        gh = tk.Frame(self.left_inner, bg=COLORS['card'])
        gh.pack(fill=tk.X, padx=20, pady=(20, 6))
        tk.Label(gh, text="Grammar Productions", font=FONTS['heading'],
                 bg=COLORS['card'], fg=COLORS['fg']).pack(anchor='w')
        tk.Label(gh, text="One production per line  ·  Use  ->  and  |  for alternatives",
                 font=('Segoe UI', 9), bg=COLORS['card'], fg=COLORS['fg_muted']).pack(anchor='w')

        grammar_box = tk.Frame(self.left_inner, bg=COLORS['card'])
        grammar_box.pack(fill=tk.X, padx=20, pady=4)
        self.grammar_text = tk.Text(grammar_box, height=9, width=38, font=FONTS['mono'],
                                    bg=COLORS['input'], fg=COLORS['fg'],
                                    insertbackground=COLORS['insert'], relief=tk.FLAT,
                                    padx=12, pady=12, wrap=tk.WORD,
                                    highlightthickness=1, highlightcolor=COLORS['accent'],
                                    highlightbackground=COLORS['input_border'])
        self.grammar_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        g_scroll = tk.Scrollbar(grammar_box, command=self.grammar_text.yview,
                                bg=COLORS['input'], troughcolor=COLORS['card'])
        g_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.grammar_text.config(yscrollcommand=g_scroll.set)

        # Input String
        ih = tk.Frame(self.left_inner, bg=COLORS['card'])
        ih.pack(fill=tk.X, padx=20, pady=(16, 6))
        tk.Label(ih, text="Input String", font=FONTS['heading'],
                 bg=COLORS['card'], fg=COLORS['fg']).pack(anchor='w')
        self.input_entry = tk.Entry(self.left_inner, font=FONTS['mono'], bg=COLORS['input'],
                                    fg=COLORS['fg'], insertbackground=COLORS['insert'],
                                    relief=tk.FLAT, highlightthickness=1,
                                    highlightcolor=COLORS['accent'],
                                    highlightbackground=COLORS['input_border'])
        self.input_entry.pack(fill=tk.X, padx=20, pady=4, ipady=8)

        # ── Button Grid (2-column) ─────────────────────────────────────
        btn_outer = tk.Frame(self.left_inner, bg=COLORS['card'])
        btn_outer.pack(fill=tk.X, padx=20, pady=(18, 8))

        tk.Label(btn_outer, text="Actions", font=('Segoe UI', 9, 'bold'),
                 bg=COLORS['card'], fg=COLORS['fg_muted']).pack(anchor='w', pady=(0, 6))

        grid_frame = tk.Frame(btn_outer, bg=COLORS['card'])
        grid_frame.pack(fill=tk.X)
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        grid_btns = [
            # (label, command, bg, hover_bg, row, col)
            ("▶  Run Check",        self.run_check,         COLORS['accent'],  COLORS['accent_hover'], 0, 0),
            ("⚡ Generate Tree",     self.generate_tree,     '#818cf8',         '#a5b4fc',              0, 1),
            ("🔄 Convert Grammar",  self.convert_grammar,   '#10b981',         '#34d399',              1, 0),
            ("🔍 Determinism",      self.check_determinism, '#8b5cf6',         '#a78bfa',              1, 1),
            ("⌫  Clear All",        self.clear_all,         COLORS['fg_muted'],'#cbd5e1',              2, 0),
            ("⎗  Load Example",     self.load_example,      COLORS['warning'], '#fbbf24',              2, 1),
        ]

        for text, cmd, color, hover, row, col in grid_btns:
            fg = COLORS['bg'] if color not in (COLORS['fg_muted'],) else COLORS['fg']
            btn = tk.Button(grid_frame, text=text, command=cmd, font=FONTS['button'],
                            bg=color, fg=fg, activebackground=hover,
                            relief=tk.FLAT, cursor='hand2', pady=9, bd=0)
            btn.grid(row=row, column=col, sticky='ew', padx=3, pady=3)
            btn.bind("<Enter>", lambda e, b=btn, c=hover: b.config(bg=c))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))

        exit_btn = tk.Button(btn_outer, text="✕  Exit", command=self.destroy,
                             font=FONTS['button'], bg=COLORS['danger'], fg=COLORS['bg'],
                             activebackground='#f87171', relief=tk.FLAT,
                             cursor='hand2', pady=9, bd=0)
        exit_btn.pack(fill=tk.X, padx=3, pady=(3, 0))
        exit_btn.bind("<Enter>", lambda e: exit_btn.config(bg='#f87171'))
        exit_btn.bind("<Leave>", lambda e: exit_btn.config(bg=COLORS['danger']))

        # ── Right Panel ───────────────────────────────────────────────
        right = tk.Frame(paned, bg=COLORS['bg'], bd=0)
        paned.add(right, width=870)

        # Tab Bar (7 tabs)
        tab_bar = tk.Frame(right, bg=COLORS['bg'])
        tab_bar.pack(fill=tk.X, pady=(0, 8))

        tab_names = [
            "Console",
            "Leftmost",
            "Rightmost",
            "Trees",
            "Result",
            "Convert",
            "Determinism",
        ]
        for i, name in enumerate(tab_names):
            lbl = tk.Label(tab_bar, text=name, font=FONTS['button'],
                           bg=COLORS['card'], fg=COLORS['fg_muted'],
                           padx=14, pady=11, cursor='hand2')
            lbl.pack(side=tk.LEFT, padx=(0, 3))
            lbl.bind("<Button-1>", lambda e, idx=i: self._switch_tab(idx))
            self.tab_labels.append(lbl)
            frame = tk.Frame(right, bg=COLORS['bg'])
            self.tab_frames.append(frame)

        # ── Tab 0: Output Console ─────────────────────────────────────
        self.output_text = tk.Text(self.tab_frames[0], wrap=tk.NONE, font=FONTS['mono'],
                                   bg=COLORS['input'], fg=COLORS['fg'], relief=tk.FLAT,
                                   padx=14, pady=14, state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self._add_scrollbar(self.tab_frames[0], self.output_text, include_horizontal=True)
        self._config_tags(self.output_text)

        # ── Tab 1: Leftmost Derivation ────────────────────────────────
        self.left_text = tk.Text(self.tab_frames[1], wrap=tk.NONE, font=FONTS['mono'],
                                 bg=COLORS['input'], fg=COLORS['fg'], relief=tk.FLAT,
                                 padx=14, pady=14, state=tk.DISABLED)
        self.left_text.pack(fill=tk.BOTH, expand=True)
        self._add_scrollbar(self.tab_frames[1], self.left_text, include_horizontal=True)
        self._config_tags(self.left_text)

        # ── Tab 2: Rightmost Derivation ───────────────────────────────
        self.right_text = tk.Text(self.tab_frames[2], wrap=tk.NONE, font=FONTS['mono'],
                                  bg=COLORS['input'], fg=COLORS['fg'], relief=tk.FLAT,
                                  padx=14, pady=14, state=tk.DISABLED)
        self.right_text.pack(fill=tk.BOTH, expand=True)
        self._add_scrollbar(self.tab_frames[2], self.right_text, include_horizontal=True)
        self._config_tags(self.right_text)

        # ── Tab 3: Parse Trees ────────────────────────────────────────
        self.tree_text = tk.Text(self.tab_frames[3], wrap=tk.NONE, font=FONTS['mono'],
                                 bg=COLORS['input'], fg=COLORS['fg'], relief=tk.FLAT,
                                 padx=14, pady=14, state=tk.DISABLED)
        self.tree_text.pack(fill=tk.BOTH, expand=True)
        self._add_scrollbar(self.tab_frames[3], self.tree_text, include_horizontal=True)
        self._config_tags(self.tree_text)

        # ── Tab 4: Result Banner ──────────────────────────────────────
        result_container = tk.Frame(self.tab_frames[4], bg=COLORS['bg'])
        result_container.pack(expand=True, fill=tk.BOTH)
        self.result_banner = tk.Frame(result_container, bg=COLORS['card'], bd=0)
        self.result_banner.pack(pady=35, padx=40, fill=tk.X)
        self.result_icon = tk.Label(self.result_banner, text="◆",
                                    font=('Segoe UI', 72),
                                    bg=COLORS['card'], fg=COLORS['border'])
        self.result_icon.pack(pady=(30, 10))
        self.result_label = tk.Label(self.result_banner, text="Ready to Analyze",
                                     font=FONTS['big'], bg=COLORS['card'], fg=COLORS['fg_muted'])
        self.result_label.pack(pady=10, padx=40)
        self.result_sub = tk.Label(self.result_banner,
                                   text="Enter a grammar and input string, then click 'Run Check'",
                                   font=FONTS['body'], bg=COLORS['card'], fg=COLORS['fg_muted'])
        self.result_sub.pack(pady=(0, 30), padx=40)
        self.result_detail = tk.Label(result_container, text="",
                                      font=FONTS['body'], bg=COLORS['bg'], fg=COLORS['fg_muted'])
        self.result_detail.pack()

        # ── Tab 5: Convert Grammar ────────────────────────────────────
        convert_outer = tk.Frame(self.tab_frames[5], bg=COLORS['bg'])
        convert_outer.pack(fill=tk.BOTH, expand=True)

        # Outer scrollable area for the Convert tab so result and report share one vertical scrollbar
        convert_canvas = tk.Canvas(convert_outer, bg=COLORS['bg'], highlightthickness=0)
        convert_vscroll = tk.Scrollbar(convert_outer, orient=tk.VERTICAL, command=convert_canvas.yview,
                                       bg=COLORS['bg'], troughcolor=COLORS['card'])
        convert_canvas.configure(yscrollcommand=convert_vscroll.set)
        convert_vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        convert_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        convert_inner = tk.Frame(convert_canvas, bg=COLORS['bg'])
        convert_canvas.create_window((0, 0), window=convert_inner, anchor='nw')
        convert_inner.bind(
            '<Configure>',
            lambda e: convert_canvas.configure(scrollregion=convert_canvas.bbox('all'))
        )

        # Banner
        self.convert_banner = tk.Frame(convert_inner, bg=COLORS['card'])
        self.convert_banner.pack(fill=tk.X, padx=8, pady=(8, 0))
        self.convert_icon = tk.Label(self.convert_banner, text="🔄",
                                     font=('Segoe UI', 28), bg=COLORS['card'])
        self.convert_icon.pack(side=tk.LEFT, padx=(16, 8), pady=12)
        banner_txt = tk.Frame(self.convert_banner, bg=COLORS['card'])
        banner_txt.pack(side=tk.LEFT, pady=12)
        self.convert_title = tk.Label(banner_txt, text="Convert Grammar",
                                      font=FONTS['medium'], bg=COLORS['card'],
                                      fg=COLORS['fg_muted'])
        self.convert_title.pack(anchor='w')
        self.convert_sub = tk.Label(banner_txt,
                                    text="Load a grammar and click '🔄 Convert Grammar'",
                                    font=FONTS['body'], bg=COLORS['card'],
                                    fg=COLORS['fg_muted'])
        self.convert_sub.pack(anchor='w')

        # ── Unambiguous Grammar Quick Copy Box ─────────────────────────
        result_box = tk.Frame(convert_inner, bg=COLORS['card'], bd=1, relief=tk.SOLID)
        result_box.pack(fill=tk.X, padx=8, pady=8)

        result_header = tk.Frame(result_box, bg=COLORS['card'])
        result_header.pack(fill=tk.X, padx=12, pady=(12, 6))
        tk.Label(result_header, text="📋 Unambiguous Grammar Result", font=FONTS['heading'],
                 bg=COLORS['card'], fg=COLORS['success']).pack(anchor='w', side=tk.LEFT)
        copy_btn = tk.Button(result_header, text="Copy All", command=self._copy_unambig_grammar,
                            font=FONTS['button'], bg=COLORS['accent'], fg=COLORS['bg'],
                            relief=tk.FLAT, cursor='hand2', padx=10, pady=4)
        copy_btn.pack(anchor='e', side=tk.RIGHT)

        grammar_box = tk.Frame(result_box, bg=COLORS['card'])
        grammar_box.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        self.unambig_text = tk.Text(grammar_box, height=6, width=50, font=FONTS['mono'],
                                    bg=COLORS['input'], fg=COLORS['success'],
                                    relief=tk.FLAT, padx=10, pady=10, state=tk.DISABLED,
                                    highlightthickness=0)
        self.unambig_text.pack(fill=tk.BOTH, expand=True)

        # Detail text
        self.convert_text = tk.Text(convert_inner, wrap=tk.NONE, font=FONTS['mono'],
                                    bg=COLORS['input'], fg=COLORS['fg'], relief=tk.FLAT,
                                    padx=14, pady=14, state=tk.DISABLED)
        self.convert_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self._add_scrollbar(convert_inner, self.convert_text, include_horizontal=True)
        self._config_tags(self.convert_text)

        # ── Tab 6: Determinism ────────────────────────────────────────
        det_outer = tk.Frame(self.tab_frames[6], bg=COLORS['bg'])
        det_outer.pack(fill=tk.BOTH, expand=True)

        # Banner
        self.det_banner = tk.Frame(det_outer, bg=COLORS['card'])
        self.det_banner.pack(fill=tk.X, padx=8, pady=(8, 0))
        self.det_icon = tk.Label(self.det_banner, text="🔍",
                                 font=('Segoe UI', 28), bg=COLORS['card'])
        self.det_icon.pack(side=tk.LEFT, padx=(16, 8), pady=12)
        det_banner_txt = tk.Frame(self.det_banner, bg=COLORS['card'])
        det_banner_txt.pack(side=tk.LEFT, pady=12)
        self.det_title = tk.Label(det_banner_txt, text="Determinism Checker",
                                  font=FONTS['medium'], bg=COLORS['card'],
                                  fg=COLORS['fg_muted'])
        self.det_title.pack(anchor='w')
        self.det_sub = tk.Label(det_banner_txt,
                                text="Load a grammar and click '🔍 Determinism'",
                                font=FONTS['body'], bg=COLORS['card'],
                                fg=COLORS['fg_muted'])
        self.det_sub.pack(anchor='w')

        # Detail text
        self.det_text = tk.Text(det_outer, wrap=tk.NONE, font=FONTS['mono'],
                                bg=COLORS['input'], fg=COLORS['fg'], relief=tk.FLAT,
                                padx=14, pady=14, state=tk.DISABLED)
        self.det_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._add_scrollbar(det_outer, self.det_text, include_horizontal=True)
        self._config_tags(self.det_text)

        self._switch_tab(0)

        # ── Status Bar ────────────────────────────────────────────────
        status_frame = tk.Frame(self, bg=COLORS['card'], height=38)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = tk.Label(status_frame, text="Ready",
                                     font=FONTS['status'], bg=COLORS['card'],
                                     fg=COLORS['fg_muted'], anchor='w')
        self.status_label.pack(side=tk.LEFT, padx=20, pady=8)

    # ------------------------------------------------------------------
    # UI Helpers
    # ------------------------------------------------------------------

    def _add_scrollbar(self, parent, text_widget, include_horizontal=False):
        sb = tk.Scrollbar(parent, command=text_widget.yview,
                          bg=COLORS['input'], troughcolor=COLORS['bg'])
        text_widget.pack_forget()
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        if include_horizontal:
            hsb = tk.Scrollbar(parent, orient=tk.HORIZONTAL,
                               command=text_widget.xview,
                               bg=COLORS['input'], troughcolor=COLORS['bg'])
            hsb.pack(side=tk.BOTTOM, fill=tk.X)
            text_widget.config(xscrollcommand=hsb.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_widget.config(yscrollcommand=sb.set)

    def _config_tags(self, w):
        w.tag_config('error',   foreground=COLORS['danger'])
        w.tag_config('success', foreground=COLORS['success'])
        w.tag_config('accent',  foreground=COLORS['accent'])
        w.tag_config('warning', foreground=COLORS['warning'])
        w.tag_config('bold',    font=FONTS['mono_bold'])
        w.tag_config('info',    foreground=COLORS['fg_muted'])
        w.tag_config('green',   foreground='#34d399')
        w.tag_config('purple',  foreground='#a78bfa')

    def _switch_tab(self, index):
        for i, lbl in enumerate(self.tab_labels):
            if i == index:
                lbl.config(bg=COLORS['accent'], fg=COLORS['bg'])
                self.tab_frames[i].pack(fill=tk.BOTH, expand=True)
            else:
                lbl.config(bg=COLORS['card'], fg=COLORS['fg_muted'])
                self.tab_frames[i].pack_forget()

    def _set_text(self, widget, text, tag=None):
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        if tag:
            widget.insert(tk.END, text, tag)
        else:
            widget.insert(tk.END, text)
        widget.config(state=tk.DISABLED)

    def _append_text(self, widget, text, tag=None):
        widget.config(state=tk.NORMAL)
        if tag:
            widget.insert(tk.END, text + "\n", tag)
        else:
            widget.insert(tk.END, text + "\n")
        widget.config(state=tk.DISABLED)
        widget.see(tk.END)

    def _append_block(self, widget, text, tag=None):
        """Append multi-line text block without adding extra newlines."""
        widget.config(state=tk.NORMAL)
        if not text.endswith('\n'):
            text = text + '\n'
        if tag:
            widget.insert(tk.END, text, tag)
        else:
            widget.insert(tk.END, text)
        widget.config(state=tk.DISABLED)
        widget.see(tk.END)

    def _copy_unambig_grammar(self):
        """Copy unambiguous grammar to the clipboard."""
        if not getattr(self, 'current_unambig_grammar', '').strip():
            show_info(self, "No Grammar", "No unambiguous grammar available to copy.")
            return
        self.clipboard_clear()
        self.clipboard_append(self.current_unambig_grammar)
        self.update()
        show_info(self, "Copied", "Unambiguous grammar copied to clipboard!\n\nPaste it into 'Grammar Productions' and click 'Run Check' to verify.")

    def update_status(self, msg, color_key='fg_muted'):
        self.status_label.config(text=msg, fg=COLORS.get(color_key, COLORS['fg_muted']))

    # ------------------------------------------------------------------
    # Actions: Load Example / Clear All
    # ------------------------------------------------------------------

    def load_example(self):
        self.grammar_text.delete("1.0", tk.END)
        self.grammar_text.insert("1.0", "E -> E+E\nE -> E*E\nE -> id")
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, "id+id*id")
        self.update_status("Example grammar loaded.", 'success')

    def clear_all(self):
        self.grammar_text.delete("1.0", tk.END)
        self.input_entry.delete(0, tk.END)
        self._set_text(self.output_text, "")
        self._set_text(self.left_text, "")
        self._set_text(self.right_text, "")
        self._set_text(self.tree_text, "")
        self._set_text(self.convert_text, "")
        self._set_text(self.det_text, "")
        self._reset_result_banner()
        self._reset_convert_banner()
        self._reset_det_banner()
        self.current_result = None
        self.current_parser = None
        self.update_status("Cleared.", 'fg_muted')

    def _reset_result_banner(self):
        self.result_banner.config(bg=COLORS['card'])
        self.result_icon.config(text="◆", fg=COLORS['border'], bg=COLORS['card'])
        self.result_label.config(text="Ready to Analyze", fg=COLORS['fg_muted'], bg=COLORS['card'])
        self.result_sub.config(
            text="Enter a grammar and input string, then click 'Run Check'",
            fg=COLORS['fg_muted'], bg=COLORS['card'])
        self.result_detail.config(text="")

    def _reset_convert_banner(self):
        self.convert_banner.config(bg=COLORS['card'])
        self.convert_icon.config(text="🔄", bg=COLORS['card'])
        self.convert_title.config(text="Convert Grammar",
                                  fg=COLORS['fg_muted'], bg=COLORS['card'])
        self.convert_sub.config(
            text="Load a grammar and click '🔄 Convert Grammar'",
            fg=COLORS['fg_muted'], bg=COLORS['card'])

    def _reset_det_banner(self):
        self.det_banner.config(bg=COLORS['card'])
        self.det_icon.config(text="🔍", bg=COLORS['card'])
        self.det_title.config(text="Determinism Checker",
                              fg=COLORS['fg_muted'], bg=COLORS['card'])
        self.det_sub.config(
            text="Load a grammar and click '🔍 Determinism'",
            fg=COLORS['fg_muted'], bg=COLORS['card'])

    # ------------------------------------------------------------------
    # Action: Run Ambiguity Check
    # ------------------------------------------------------------------

    def run_check(self):
        grammar_raw = self.grammar_text.get("1.0", tk.END)
        input_str   = self.input_entry.get().strip()

        if not grammar_raw.strip():
            show_error(self, "Validation Error", "Grammar cannot be empty.")
            self.update_status("Grammar empty.", 'danger')
            return
        if not input_str:
            show_error(self, "Validation Error", "Input string cannot be empty.")
            self.update_status("Input string empty.", 'danger')
            return

        parser = CFGParser()
        ok, msg = parser.load_grammar(grammar_raw)
        if not ok:
            show_error(self, "Grammar Error", msg)
            self.update_status(msg, 'danger')
            return

        ok, tokens, msg = parser.tokenize_input(input_str)
        if not ok:
            show_error(self, "Input Error", msg)
            self.update_status(msg, 'danger')
            return

        self.update_status("Analyzing...", 'accent')
        self.current_parser = parser

        checker = AmbiguityChecker(parser)
        result  = checker.analyze(tokens)
        self.current_result = result

        # ── Output Console ────────────────────────────────────────────
        self._set_text(self.output_text, "")
        self._append_text(self.output_text, "=" * 62, 'accent')
        self._append_text(self.output_text,
                          "  G R A M M A R   A M B I G U I T Y   C H E C K   R E P O R T",
                          'bold')
        self._append_text(self.output_text, "=" * 62, 'accent')
        self._append_text(self.output_text, f"\nInput String  : {input_str}")
        self._append_text(self.output_text, f"Tokens        : {tokens}\n")
        self._append_text(self.output_text, "Grammar Productions:", 'bold')
        for nt, prods in parser.grammar.items():
            for p in prods:
                rhs = " ".join(p) if p else "ε"
                self._append_text(self.output_text, f"  {nt} -> {rhs}")
        self._append_text(self.output_text, f"\nParse Trees Found : {result['tree_count']}")
        self._append_text(self.output_text, f"Non-terminals     : {parser.nt_set}")
        self._append_text(self.output_text, f"Terminals         : {parser.terminals}\n")
        for m in result['messages']:
            tag = 'success' if 'UNAMBIGUOUS' in m else 'error' if 'AMBIGUOUS' in m else 'warning'
            self._append_text(self.output_text, f"  ► {m}", tag)
        if result['debug']:
            self._append_text(self.output_text, "\nDebug Log:", 'info')
            for line in result['debug']:
                self._append_text(self.output_text, f"  {line}", 'info')

        # ── Leftmost Derivation ───────────────────────────────────────
        self._set_text(self.left_text, "")
        for i, deriv in enumerate(result['leftmost_derivations']):
            self._append_text(self.left_text,
                              f"─── Leftmost Derivation (Tree {i+1}) ───", 'accent')
            for j, step in enumerate(deriv):
                arrow = " ⇒ " if j > 0 else "   "
                self._append_text(self.left_text, f"{arrow}{step}")
            self._append_text(self.left_text, "")

        # ── Rightmost Derivation ──────────────────────────────────────
        self._set_text(self.right_text, "")
        for i, deriv in enumerate(result['rightmost_derivations']):
            self._append_text(self.right_text,
                              f"─── Rightmost Derivation (Tree {i+1}) ───", 'accent')
            for j, step in enumerate(deriv):
                arrow = " ⇒ " if j > 0 else "   "
                self._append_text(self.right_text, f"{arrow}{step}")
            self._append_text(self.right_text, "")

        # ── Parse Trees (text) ────────────────────────────────────────
        self._set_text(self.tree_text, "")
        gen = TreeGenerator()
        for i, tree in enumerate(result['trees']):
            self._append_text(self.tree_text,
                              f"─── Parse Tree {i+1} ───", 'accent')
            try:
                if TreeGenerator.NLTK_AVAILABLE:
                    nltk_tree = gen.node_to_nltk(tree)
                    self._append_text(self.tree_text, nltk_tree.pformat(margin=90))
                else:
                    self._append_text(self.tree_text, gen.get_ascii_tree(tree))
            except Exception as e:
                self._append_text(self.tree_text, f"Tree formatting error: {e}", 'error')
            self._append_text(self.tree_text, "")

        # ── Result Banner ─────────────────────────────────────────────
        self._update_result_banner(result)
        self._switch_tab(4)

    def _update_result_banner(self, result):
        if result['ambiguous']:
            self.result_banner.config(bg=COLORS['danger_bg'])
            self.result_icon.config(text="✘",  fg=COLORS['danger'],  bg=COLORS['danger_bg'])
            self.result_label.config(text="GRAMMAR IS AMBIGUOUS",
                                     fg=COLORS['danger'],  bg=COLORS['danger_bg'])
            self.result_sub.config(
                text=f"Found {result['tree_count']} distinct parse trees for the given input.",
                fg=COLORS['fg'], bg=COLORS['danger_bg'])
            self.result_detail.config(
                text="The same string can be derived in multiple ways.",
                fg=COLORS['fg_muted'])
            self.update_status("Ambiguity detected! Multiple parse trees exist.", 'danger')
        elif result['tree_count'] == 0:
            self.result_banner.config(bg=COLORS['warning_bg'])
            self.result_icon.config(text="⚠",  fg=COLORS['warning'], bg=COLORS['warning_bg'])
            self.result_label.config(text="STRING NOT IN LANGUAGE",
                                     fg=COLORS['warning'], bg=COLORS['warning_bg'])
            self.result_sub.config(
                text="The input string cannot be derived from the grammar.",
                fg=COLORS['fg'], bg=COLORS['warning_bg'])
            self.result_detail.config(text="Check your grammar and input string.",
                                      fg=COLORS['fg_muted'])
            self.update_status("No valid derivation found.", 'warning')
        else:
            self.result_banner.config(bg=COLORS['success_bg'])
            self.result_icon.config(text="✔",  fg=COLORS['success'], bg=COLORS['success_bg'])
            self.result_label.config(text="GRAMMAR IS UNAMBIGUOUS",
                                     fg=COLORS['success'], bg=COLORS['success_bg'])
            self.result_sub.config(
                text="Exactly one parse tree exists for the given input string.",
                fg=COLORS['fg'], bg=COLORS['success_bg'])
            self.result_detail.config(text="The derivation is unique.",
                                      fg=COLORS['fg_muted'])
            self.update_status("Grammar is unambiguous for this input.", 'success')

    # ------------------------------------------------------------------
    # Action: Generate Tree Image
    # ------------------------------------------------------------------

    def generate_tree(self):
        if not self.current_result or not self.current_result['trees']:
            show_error(self, "No Data",
                       "Please run 'Run Check' first to generate parse trees.")
            return

        gen    = TreeGenerator()
        images = []
        ascii_trees = []
        for i, tree in enumerate(self.current_result['trees']):
            path = gen.render_tree(tree, i)
            if path:
                images.append(path)
            ascii_trees.append(gen.get_ascii_tree(tree))

        if images and PILLOW_AVAILABLE:
            TreePopup(self, images)
        else:
            if not PILLOW_AVAILABLE:
                show_info(self, "Pillow Not Available",
                          "Pillow is required for image rendering.\n"
                          "Install: pip install Pillow")
            elif not images:
                show_info(self, "Graphviz Not Available",
                          "Graphviz binary not found — showing text trees.\n"
                          "Install Graphviz: https://graphviz.org/download/")
            self._set_text(self.tree_text, "")
            for i, ascii_tree in enumerate(ascii_trees):
                self._append_text(self.tree_text, f"─── ASCII Parse Tree {i+1} ───", 'accent')
                self._append_text(self.tree_text, ascii_tree)
                self._append_text(self.tree_text, "")
            self._switch_tab(3)

    # ------------------------------------------------------------------
    # Action: Convert Ambiguous Grammar → Unambiguous
    # ------------------------------------------------------------------

    def convert_grammar(self):
        grammar_raw = self.grammar_text.get("1.0", tk.END)
        if not grammar_raw.strip():
            show_error(self, "Validation Error", "Grammar cannot be empty.")
            self.update_status("Grammar empty.", 'danger')
            return

        parser = CFGParser()
        ok, msg = parser.load_grammar(grammar_raw)
        if not ok:
            show_error(self, "Grammar Error", msg)
            self.update_status(msg, 'danger')
            return

        self.update_status("Converting grammar...", 'accent')

        try:
            converter = GrammarConverter(parser)
            res       = converter.convert()
        except Exception as ex:
            show_error(self, "Conversion Error", str(ex))
            self.update_status("Conversion failed.", 'danger')
            return

        # ── Update banner ──────────────────────────────────────────────
        self.convert_banner.config(bg='#064e3b')
        self.convert_icon.config(text="🔄", bg='#064e3b')
        self.convert_title.config(
            text=f"Conversion Complete  ·  {res['method']}",
            fg='#34d399', bg='#064e3b')
        self.convert_sub.config(
            text="Unambiguous grammar generated — see details below.",
            fg=COLORS['fg'], bg='#064e3b')

        # ── Fill detail text ───────────────────────────────────────────
        self._set_text(self.convert_text, "")

        self._append_text(self.convert_text, "=" * 62, 'accent')
        self._append_text(self.convert_text,
                          "  G R A M M A R   C O N V E R S I O N   R E P O R T", 'bold')
        self._append_text(self.convert_text, "=" * 62, 'accent')
        self._append_text(self.convert_text, f"\nMethod:  {res['method']}\n", 'warning')

        self._append_text(self.convert_text,
                          "─── Original (Ambiguous) Grammar ───", 'accent')
        for line in res['original'].split('\n'):
            self._append_text(self.convert_text, f"  {line}", 'error')
        self._append_text(self.convert_text, "")

        self._append_text(self.convert_text,
                          "─── Conversion Steps ───", 'accent')
        for step in res['steps']:
            if step.strip():
                if step.startswith('STEP'):
                    self._append_text(self.convert_text, "\n" + step, 'warning')
                else:
                    self._append_text(self.convert_text, step)
            else:
                self._append_text(self.convert_text, "")
        self._append_text(self.convert_text, "")


        self._append_text(self.convert_text,
                          "─── Unambiguous Grammar (Result) ───", 'green')
        for line in res['converted'].split('\n'):
            self._append_text(self.convert_text, f"  {line}", 'green')
        self._append_text(self.convert_text, "")

        # Store unambiguous grammar for copy button
        self.current_unambig_grammar = res['converted']
        self._set_text(self.unambig_text, res['converted'])

        self._append_text(self.convert_text,
                          "─── Explanation ───", 'accent')
        for line in res['explanation']:
            if line.strip():
                if line.startswith('WHY') or line.startswith('Benefits') or line.startswith('The') or (line and line[0].isupper() and ':' in line):
                    self._append_text(self.convert_text, line, 'bold')
                else:
                    self._append_text(self.convert_text, line)
            else:
                self._append_text(self.convert_text, "")

        self._switch_tab(5)
        self.update_status(f"Conversion complete — Method: {res['method']}", 'success')

    # ------------------------------------------------------------------
    # Action: Check Determinism (LL(1) Analysis)
    # ------------------------------------------------------------------

    def check_determinism(self):
        grammar_raw = self.grammar_text.get("1.0", tk.END)
        if not grammar_raw.strip():
            show_error(self, "Validation Error", "Grammar cannot be empty.")
            self.update_status("Grammar empty.", 'danger')
            return

        parser = CFGParser()
        ok, msg = parser.load_grammar(grammar_raw)
        if not ok:
            show_error(self, "Grammar Error", msg)
            self.update_status(msg, 'danger')
            return

        self.update_status("Computing FIRST / FOLLOW / Parsing Table...", 'accent')

        try:
            det     = DeterminismChecker(parser)
            res     = det.analyze()
        except Exception as ex:
            show_error(self, "Analysis Error", str(ex))
            self.update_status("Determinism check failed.", 'danger')
            return

        is_ll1 = res['is_ll1']

        # ── Update banner ──────────────────────────────────────────────
        if is_ll1:
            banner_bg   = COLORS['success_bg']
            title_color = COLORS['success']
            icon_text   = "✔"
        else:
            banner_bg   = COLORS['danger_bg']
            title_color = COLORS['danger']
            icon_text   = "✘"

        self.det_banner.config(bg=banner_bg)
        self.det_icon.config(text=icon_text, bg=banner_bg, fg=title_color)
        self.det_title.config(text=res['verdict'],
                              fg=title_color, bg=banner_bg)
        self.det_sub.config(
            text=("No conflicts in parsing table — single lookahead sufficient."
                  if is_ll1 else
                  f"{len(res['conflicts'])} conflict(s) found — see details below."),
            fg=COLORS['fg'], bg=banner_bg)

        # ── Fill detail text ───────────────────────────────────────────
        self._set_text(self.det_text, "")

        self._append_text(self.det_text, "=" * 62, 'accent')
        self._append_text(self.det_text,
                          "  D E T E R M I N I S M   A N A L Y S I S   (LL-1)", 'bold')
        self._append_text(self.det_text, "=" * 62, 'accent')

        verdict_tag = 'success' if is_ll1 else 'error'
        self._append_text(self.det_text,
                          f"\n  ► {res['verdict']}\n", verdict_tag)

        # FIRST sets
        self._append_text(self.det_text, "─── FIRST Sets ───", 'accent')
        for nt, first_set in res['first'].items():
            self._append_text(self.det_text,
                              f"  FIRST({nt})  =  {{ {', '.join(first_set)} }}")
        self._append_text(self.det_text, "")

        # FOLLOW sets
        self._append_text(self.det_text, "─── FOLLOW Sets ───", 'accent')
        for nt, follow_set in res['follow'].items():
            self._append_text(self.det_text,
                              f"  FOLLOW({nt}) =  {{ {', '.join(follow_set)} }}")
        self._append_text(self.det_text, "")

        # Parsing Table
        self._append_text(self.det_text, "─── LL(1) Parsing Table ───", 'accent')
        if res['table']:
            for entry, prod in res['table'].items():
                self._append_text(self.det_text, f"  {entry:<24} →  {prod}")
        else:
            self._append_text(self.det_text, "  (empty — grammar may only have epsilon)", 'info')
        self._append_text(self.det_text, "")

        # Conflicts
        if res['conflicts']:
            self._append_text(self.det_text,
                              f"─── Conflicts ({len(res['conflicts'])}) ───", 'error')
            for c in res['conflicts']:
                self._append_text(self.det_text, f"  ⚠  {c}", 'error')
            self._append_text(self.det_text, "")

        # Explanation
        self._append_text(self.det_text, "─── Analysis & Recommendations ───", 'accent')
        for line in res['explanation']:
            if line.strip():
                if is_ll1 and line.startswith("Grammar IS"):
                    tag = 'success'
                elif 'WHY' in line or line.startswith('Common') or line.startswith('Possible') or line.startswith('Benefits') or line.startswith('Algorithm'):
                    tag = 'bold'
                else:
                    tag = None
                self._append_text(self.det_text, line, tag)
            else:
                self._append_text(self.det_text, "")

        self._switch_tab(6)
        status_key = 'success' if is_ll1 else 'danger'
        self.update_status(res['verdict'], status_key)
