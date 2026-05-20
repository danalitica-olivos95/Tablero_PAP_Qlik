"""Qlik Explorer — ventana principal."""
import asyncio, json, re, sys, threading, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from qlik_mcp.qrs_client import QRSClient
from qlik_mcp.engine_client import SessionManager
from . import styles as st
from .widgets import JsonTreeView

# ── Loop asyncio en hilo background ─────────────────────────────────────────
_loop = asyncio.new_event_loop()
threading.Thread(target=lambda: (asyncio.set_event_loop(_loop), _loop.run_forever()),
                 daemon=True).start()

def run_async(coro, callback=None):
    def _done(fut):
        try:    result = fut.result()
        except Exception as e: result = e
        if callback:
            _root.after(0, lambda: callback(result))
    asyncio.run_coroutine_threadsafe(coro, _loop).add_done_callback(_done)


class QlikExplorer:
    HISTORY_MAX = 10

    def __init__(self, root):
        global _root
        _root = root
        self.root          = root
        self.sessions      = SessionManager()
        self._apps_all     = []
        self._app_ids      = {}
        self._current_app  = None
        self._sheets_data  = []
        self._history      = []   # [{id, name}, ...]
        self._script_find_pos = []

        root.title('Qlik Explorer — Coopserfun')
        root.geometry('1380x800')
        root.configure(bg=st.BG)
        root.minsize(900, 600)

        st.apply(root)
        self._build_ui()
        self._connect()

    # ─────────────────────────────────────────────────────────────────────────
    # CONSTRUCCIÓN UI
    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Top bar
        top = tk.Frame(self.root, bg=st.BG3, height=50)
        top.pack(fill='x', side='top')
        top.pack_propagate(False)
        tk.Label(top, text='⬡  QLIK EXPLORER', bg=st.BG3, fg=st.ACCENT,
                 font=('Segoe UI', 14, 'bold')).pack(side='left', padx=16, pady=10)
        tk.Label(top, text='Coopserfun', bg=st.BG3, fg=st.FG_DARK,
                 font=('Segoe UI', 9)).pack(side='left', pady=10)
        self._status_dot = tk.Label(top, text='●', bg=st.BG3, fg=st.RED, font=('Segoe UI', 13))
        self._status_dot.pack(side='right', padx=4)
        self._status_lbl = tk.Label(top, text='Conectando…', bg=st.BG3, fg=st.FG2,
                                    font=('Segoe UI', 8))
        self._status_lbl.pack(side='right', padx=(0, 6))

        # Main
        main = tk.Frame(self.root, bg=st.BG)
        main.pack(fill='both', expand=True)
        self._build_left(main)
        ttk.Separator(main, orient='vertical').pack(side='left', fill='y', padx=1)
        self._build_center(main)
        ttk.Separator(main, orient='vertical').pack(side='left', fill='y', padx=1)
        self._build_right(main)

        # Status bar
        self._bar = tk.Label(self.root, text='Iniciando…', bg=st.BG3, fg=st.FG2,
                             font=('Segoe UI', 8), anchor='w', padx=10)
        self._bar.pack(fill='x', side='bottom', ipady=3)

    # ── Panel izquierdo: Apps + Historial ────────────────────────────────────
    def _build_left(self, parent):
        frame = tk.Frame(parent, bg=st.BG2, width=320)
        frame.pack(side='left', fill='y')
        frame.pack_propagate(False)

        nb = ttk.Notebook(frame)
        nb.pack(fill='both', expand=True)

        # Tab Apps
        tab_apps = tk.Frame(nb, bg=st.BG2)
        nb.add(tab_apps, text='  Apps  ')
        self._build_apps_tab(tab_apps)

        # Tab Historial
        tab_hist = tk.Frame(nb, bg=st.BG2)
        nb.add(tab_hist, text='  Recientes  ')
        self._build_history_tab(tab_hist)

    def _build_apps_tab(self, parent):
        hdr = tk.Frame(parent, bg=st.BG3, height=32)
        hdr.pack(fill='x'); hdr.pack_propagate(False)
        self._apps_count = tk.Label(hdr, text='', bg=st.BG3, fg=st.FG_DARK,
                                    font=('Segoe UI', 8))
        self._apps_count.pack(side='right', padx=8, pady=6)
        tk.Label(hdr, text='TODAS LAS APPS', bg=st.BG3, fg=st.FG2,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=10, pady=6)

        sf = tk.Frame(parent, bg=st.BG2, pady=5)
        sf.pack(fill='x', padx=8)
        self._search_var = tk.StringVar()
        self._search_var.trace('w', self._filter_apps)
        e = ttk.Entry(sf, textvariable=self._search_var)
        e.pack(fill='x')
        e.insert(0, '  Buscar…')
        e.bind('<FocusIn>',  lambda ev: e.delete(0,'end') if 'Buscar' in e.get() else None)
        e.bind('<FocusOut>', lambda ev: e.insert(0,'  Buscar…') if not e.get().strip() else None)

        tf = tk.Frame(parent, bg=st.BG2)
        tf.pack(fill='both', expand=True)
        self._apps_tree = ttk.Treeview(tf, show='tree', selectmode='browse')
        sc = ttk.Scrollbar(tf, orient='vertical', command=self._apps_tree.yview)
        self._apps_tree.configure(yscrollcommand=sc.set)
        sc.pack(side='right', fill='y')
        self._apps_tree.pack(fill='both', expand=True)
        self._apps_tree.tag_configure('stream', foreground=st.FG_DARK, font=('Segoe UI', 8, 'bold'))
        self._apps_tree.tag_configure('app',    foreground=st.FG,      font=('Segoe UI', 9))
        self._apps_tree.bind('<<TreeviewSelect>>', self._on_app_select)

    def _build_history_tab(self, parent):
        hdr = tk.Frame(parent, bg=st.BG3, height=32)
        hdr.pack(fill='x'); hdr.pack_propagate(False)
        tk.Label(hdr, text='ÚLTIMAS VISITADAS', bg=st.BG3, fg=st.FG2,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=10, pady=6)
        ttk.Button(hdr, text='Limpiar', style='Small.TButton',
                   command=self._clear_history).pack(side='right', padx=6, pady=4)

        tf = tk.Frame(parent, bg=st.BG2)
        tf.pack(fill='both', expand=True)
        self._hist_list = tk.Listbox(
            tf, bg=st.BG2, fg=st.FG, selectbackground=st.ACCENT,
            selectforeground='white', font=('Segoe UI', 9),
            borderwidth=0, highlightthickness=0, activestyle='none')
        sc = ttk.Scrollbar(tf, orient='vertical', command=self._hist_list.yview)
        self._hist_list.configure(yscrollcommand=sc.set)
        sc.pack(side='right', fill='y')
        self._hist_list.pack(fill='both', expand=True)
        self._hist_list.bind('<Double-Button-1>', self._on_history_select)

    # ── Panel central: Hojas ─────────────────────────────────────────────────
    def _build_center(self, parent):
        frame = tk.Frame(parent, bg=st.BG2, width=230)
        frame.pack(side='left', fill='y')
        frame.pack_propagate(False)

        hdr = tk.Frame(frame, bg=st.BG3, height=32)
        hdr.pack(fill='x'); hdr.pack_propagate(False)
        tk.Label(hdr, text='HOJAS', bg=st.BG3, fg=st.FG2,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=10, pady=6)

        lf = tk.Frame(frame, bg=st.BG2)
        lf.pack(fill='both', expand=True)
        self._sheets_list = tk.Listbox(
            lf, bg=st.BG2, fg=st.FG, selectbackground=st.ACCENT,
            selectforeground='white', font=('Segoe UI', 9),
            borderwidth=0, highlightthickness=0, activestyle='none')
        sc = ttk.Scrollbar(lf, orient='vertical', command=self._sheets_list.yview)
        self._sheets_list.configure(yscrollcommand=sc.set)
        sc.pack(side='right', fill='y')
        self._sheets_list.pack(fill='both', expand=True)
        self._sheets_list.bind('<<ListboxSelect>>', self._on_sheet_select)

    # ── Panel derecho: Detalle ────────────────────────────────────────────────
    def _build_right(self, parent):
        frame = tk.Frame(parent, bg=st.BG)
        frame.pack(side='left', fill='both', expand=True)

        # Cabecera de app
        info = tk.Frame(frame, bg=st.BG3, height=88)
        info.pack(fill='x'); info.pack_propagate(False)

        self._app_title = tk.Label(info, text='Selecciona una aplicación',
                                   bg=st.BG3, fg=st.ACCENT,
                                   font=('Segoe UI', 11, 'bold'), anchor='w')
        self._app_title.pack(fill='x', padx=12, pady=(10, 2))

        id_row = tk.Frame(info, bg=st.BG3)
        id_row.pack(fill='x', padx=12)
        tk.Label(id_row, text='ID:', bg=st.BG3, fg=st.FG_DARK,
                 font=('Segoe UI', 8)).pack(side='left')
        self._app_id_lbl = tk.Label(id_row, text='—', bg=st.BG3, fg=st.ACCENT2,
                                    font=('Consolas', 8))
        self._app_id_lbl.pack(side='left', padx=4)
        ttk.Button(id_row, text='Copiar ID', style='Small.TButton',
                   command=self._copy_app_id).pack(side='left', padx=4)
        self._reload_lbl = tk.Label(id_row, text='', bg=st.BG3, fg=st.FG_DARK,
                                    font=('Segoe UI', 8))
        self._reload_lbl.pack(side='right', padx=8)

        self._app_meta = tk.Label(info, text='', bg=st.BG3, fg=st.FG2,
                                  font=('Segoe UI', 8), anchor='w')
        self._app_meta.pack(fill='x', padx=12, pady=(2, 6))

        # Notebook de tabs
        self._nb = ttk.Notebook(frame)
        self._nb.pack(fill='both', expand=True)

        t1 = tk.Frame(self._nb, bg=st.BG2); self._nb.add(t1, text='  Objetos  ')
        t2 = tk.Frame(self._nb, bg=st.BG2); self._nb.add(t2, text='  Propiedades JSON  ')
        t3 = tk.Frame(self._nb, bg=st.BG2); self._nb.add(t3, text='  Script  ')
        t4 = tk.Frame(self._nb, bg=st.BG2); self._nb.add(t4, text='  Variables  ')
        t5 = tk.Frame(self._nb, bg=st.BG2); self._nb.add(t5, text='  Campos  ')
        t6 = tk.Frame(self._nb, bg=st.BG2); self._nb.add(t6, text='  Evaluar  ')

        self._build_tab_objects(t1)
        self._build_tab_props(t2)
        self._build_tab_script(t3)
        self._build_tab_variables(t4)
        self._build_tab_fields(t5)
        self._build_tab_eval(t6)

    # ── Tab Objetos ──────────────────────────────────────────────────────────
    def _build_tab_objects(self, p):
        cols = ('type', 'title', 'id')
        self._obj_tree = ttk.Treeview(p, columns=cols, show='headings', selectmode='browse')
        for col, txt, w in [('type','Tipo',130),('title','Título',300),('id','ID',200)]:
            self._obj_tree.heading(col, text=txt)
            self._obj_tree.column(col, width=w, minwidth=80)
        self._obj_tree.tag_configure('even', background=st.BG2)
        self._obj_tree.tag_configure('odd',  background=st.BG3)
        sc = ttk.Scrollbar(p, orient='vertical', command=self._obj_tree.yview)
        self._obj_tree.configure(yscrollcommand=sc.set)
        sc.pack(side='right', fill='y')
        self._obj_tree.pack(fill='both', expand=True)
        self._obj_tree.bind('<<TreeviewSelect>>', self._on_object_select)

    # ── Tab Propiedades JSON ─────────────────────────────────────────────────
    def _build_tab_props(self, p):
        tb = tk.Frame(p, bg=st.BG3); tb.pack(fill='x')
        tk.Label(tb, text='Propiedades del objeto seleccionado',
                 bg=st.BG3, fg=st.FG2, font=('Segoe UI', 8)).pack(side='left', padx=8, pady=5)
        ttk.Button(tb, text='Expandir', style='Small.TButton',
                   command=lambda: self._json_tree.expand_all()).pack(side='right', padx=4, pady=3)
        ttk.Button(tb, text='Colapsar', style='Small.TButton',
                   command=lambda: self._json_tree.collapse_all()).pack(side='right', padx=2, pady=3)
        ttk.Button(tb, text='Exportar JSON', style='Small.TButton',
                   command=self._export_props).pack(side='right', padx=2, pady=3)

        self._json_tree = JsonTreeView(p)
        scv = ttk.Scrollbar(p, orient='vertical',   command=self._json_tree.yview)
        sch = ttk.Scrollbar(p, orient='horizontal', command=self._json_tree.xview)
        self._json_tree.configure(yscrollcommand=scv.set, xscrollcommand=sch.set)
        scv.pack(side='right', fill='y'); sch.pack(side='bottom', fill='x')
        self._json_tree.pack(fill='both', expand=True)
        self._current_props = {}

    # ── Tab Script ───────────────────────────────────────────────────────────
    def _build_tab_script(self, p):
        tb = tk.Frame(p, bg=st.BG3); tb.pack(fill='x')
        tk.Label(tb, text='Script de carga', bg=st.BG3, fg=st.FG2,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=8, pady=5)
        ttk.Button(tb, text='Exportar .qvs', style='Small.TButton',
                   command=self._export_script).pack(side='right', padx=4, pady=3)
        ttk.Button(tb, text='↓', style='Small.TButton',
                   command=lambda: self._script_find(next_match=True)).pack(side='right', padx=2, pady=3)
        self._script_match_lbl = tk.Label(tb, text='', bg=st.BG3, fg=st.FG_DARK,
                                          font=('Segoe UI', 8))
        self._script_match_lbl.pack(side='right', padx=4)
        self._script_search = tk.StringVar()
        se = ttk.Entry(tb, textvariable=self._script_search, width=20)
        se.pack(side='right', padx=4, pady=4)
        se.bind('<Return>', lambda e: self._script_find())
        tk.Label(tb, text='Buscar:', bg=st.BG3, fg=st.FG2,
                 font=('Segoe UI', 8)).pack(side='right', padx=(8,0))

        body = tk.Frame(p, bg=st.BG2); body.pack(fill='both', expand=True)
        self._ln_text = tk.Text(body, bg=st.BG3, fg=st.FG_DARK, font=('Consolas', 9),
                                width=5, wrap='none', borderwidth=0, highlightthickness=0,
                                state='disabled', cursor='arrow')
        self._ln_text.pack(side='left', fill='y')

        self._script_text = tk.Text(
            body, bg=st.BG2, fg=st.FG, insertbackground=st.FG,
            font=('Consolas', 9), wrap='none', borderwidth=0,
            highlightthickness=0, state='disabled')

        scv = ttk.Scrollbar(body, orient='vertical')
        sch = ttk.Scrollbar(p,    orient='horizontal', command=self._script_text.xview)

        def _sync(*a):
            self._script_text.yview(*a)
            self._ln_text.yview(*a)
        scv.configure(command=_sync)
        self._script_text.configure(yscrollcommand=scv.set, xscrollcommand=sch.set)
        self._script_text.bind('<MouseWheel>',
            lambda e: self._ln_text.yview_moveto(self._script_text.yview()[0]))

        scv.pack(side='right', fill='y'); sch.pack(side='bottom', fill='x')
        self._script_text.pack(side='left', fill='both', expand=True)

        # Tags sintaxis
        self._script_text.tag_configure('kw',   foreground=st.SX_KW)
        self._script_text.tag_configure('fn',   foreground=st.SX_FN)
        self._script_text.tag_configure('str',  foreground=st.SX_STR)
        self._script_text.tag_configure('cmt',  foreground=st.SX_CMT)
        self._script_text.tag_configure('tab',  foreground=st.SX_TAB,  font=('Consolas', 9,'bold'))
        self._script_text.tag_configure('num',  foreground=st.SX_NUM)
        self._script_text.tag_configure('find', background=st.SX_FIND, foreground='black')
        self._script_find_pos = []
        self._script_find_cur = 0

    # ── Tab Variables ────────────────────────────────────────────────────────
    def _build_tab_variables(self, p):
        tb = tk.Frame(p, bg=st.BG3); tb.pack(fill='x')
        tk.Label(tb, text='Variables del app', bg=st.BG3, fg=st.FG2,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=8, pady=5)
        ttk.Button(tb, text='Recargar', style='Small.TButton',
                   command=self._load_variables).pack(side='right', padx=4, pady=3)

        self._var_search = tk.StringVar()
        self._var_search.trace('w', self._filter_variables)
        se = ttk.Entry(tb, textvariable=self._var_search, width=20)
        se.pack(side='right', padx=4, pady=4)
        tk.Label(tb, text='Buscar:', bg=st.BG3, fg=st.FG2,
                 font=('Segoe UI', 8)).pack(side='right', padx=(8,0))

        cols = ('valor', 'definicion')
        self._var_tree = ttk.Treeview(p, columns=cols, show='headings tree',
                                      selectmode='browse')
        self._var_tree.heading('#0',         text='Nombre', anchor='w')
        self._var_tree.heading('valor',      text='Valor',  anchor='w')
        self._var_tree.heading('definicion', text='Definición', anchor='w')
        self._var_tree.column('#0',         width=180, minwidth=100)
        self._var_tree.column('valor',      width=200, minwidth=80)
        self._var_tree.column('definicion', width=320, minwidth=100)
        self._var_tree.tag_configure('even', background=st.BG2)
        self._var_tree.tag_configure('odd',  background=st.BG3)
        self._var_tree.tag_configure('sys',  foreground=st.FG_DARK)

        sc = ttk.Scrollbar(p, orient='vertical', command=self._var_tree.yview)
        self._var_tree.configure(yscrollcommand=sc.set)
        sc.pack(side='right', fill='y')
        self._var_tree.pack(fill='both', expand=True)
        self._vars_all = []

    # ── Tab Campos ───────────────────────────────────────────────────────────
    def _build_tab_fields(self, p):
        tb = tk.Frame(p, bg=st.BG3); tb.pack(fill='x')
        tk.Label(tb, text='Campos del modelo de datos', bg=st.BG3, fg=st.FG2,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=8, pady=5)
        ttk.Button(tb, text='Cargar campos', style='Small.TButton',
                   command=self._load_fields).pack(side='right', padx=4, pady=3)

        self._fld_search = tk.StringVar()
        self._fld_search.trace('w', self._filter_fields)
        se = ttk.Entry(tb, textvariable=self._fld_search, width=20)
        se.pack(side='right', padx=4, pady=4)
        tk.Label(tb, text='Buscar:', bg=st.BG3, fg=st.FG2,
                 font=('Segoe UI', 8)).pack(side='right', padx=(8,0))

        cols = ('card', 'tablas')
        self._fld_tree = ttk.Treeview(p, columns=cols, show='headings tree', selectmode='browse')
        self._fld_tree.heading('#0',     text='Campo',   anchor='w')
        self._fld_tree.heading('card',   text='Valores', anchor='e')
        self._fld_tree.heading('tablas', text='Tablas',  anchor='w')
        self._fld_tree.column('#0',     width=220, minwidth=100)
        self._fld_tree.column('card',   width=90,  minwidth=60, anchor='e')
        self._fld_tree.column('tablas', width=360, minwidth=100)
        self._fld_tree.tag_configure('even', background=st.BG2)
        self._fld_tree.tag_configure('odd',  background=st.BG3)

        sc = ttk.Scrollbar(p, orient='vertical', command=self._fld_tree.yview)
        self._fld_tree.configure(yscrollcommand=sc.set)
        sc.pack(side='right', fill='y')
        self._fld_tree.pack(fill='both', expand=True)
        self._fields_all = []

    # ── Tab Evaluar expresión ────────────────────────────────────────────────
    def _build_tab_eval(self, p):
        tk.Label(p, text='Evalúa cualquier expresión Qlik en tiempo real',
                 bg=st.BG2, fg=st.FG2, font=('Segoe UI', 9)).pack(padx=12, pady=(12,4), anchor='w')

        entry_row = tk.Frame(p, bg=st.BG2); entry_row.pack(fill='x', padx=12, pady=4)
        self._eval_var = tk.StringVar()
        self._eval_entry = ttk.Entry(entry_row, textvariable=self._eval_var,
                                     font=('Consolas', 11))
        self._eval_entry.pack(side='left', fill='x', expand=True)
        self._eval_entry.insert(0, '=SUM(Ejecutado)')
        self._eval_entry.bind('<Return>',   lambda e: self._evaluate())
        self._eval_entry.bind('<KP_Enter>', lambda e: self._evaluate())
        ttk.Button(entry_row, text='Evaluar  ↵', command=self._evaluate).pack(side='left', padx=6)
        ttk.Button(entry_row, text='Limpiar', style='Small.TButton',
                   command=self._eval_clear).pack(side='left', padx=2)

        res_frame = tk.Frame(p, bg=st.BG3, pady=12); res_frame.pack(fill='x', padx=12, pady=8)
        tk.Label(res_frame, text='Resultado:', bg=st.BG3, fg=st.FG2,
                 font=('Segoe UI', 9)).pack(anchor='w', padx=12)
        self._eval_result = tk.Label(res_frame, text='—', bg=st.BG3, fg=st.FG_STR,
                                     font=('Consolas', 18, 'bold'), anchor='w')
        self._eval_result.pack(anchor='w', padx=12, pady=4)

        # Historial de evaluaciones
        tk.Label(p, text='Historial', bg=st.BG2, fg=st.FG_DARK,
                 font=('Segoe UI', 8, 'bold')).pack(padx=12, pady=(8,2), anchor='w')
        hf = tk.Frame(p, bg=st.BG2); hf.pack(fill='both', expand=True, padx=12, pady=(0,8))
        self._eval_hist = tk.Listbox(
            hf, bg=st.BG3, fg=st.FG2, selectbackground=st.ACCENT,
            selectforeground='white', font=('Consolas', 9),
            borderwidth=0, highlightthickness=0, activestyle='none')
        sc = ttk.Scrollbar(hf, orient='vertical', command=self._eval_hist.yview)
        self._eval_hist.configure(yscrollcommand=sc.set)
        sc.pack(side='right', fill='y')
        self._eval_hist.pack(fill='both', expand=True)
        self._eval_hist.bind('<Double-Button-1>', self._eval_from_history)

    # ─────────────────────────────────────────────────────────────────────────
    # CONEXIÓN Y CARGA DE APPS
    # ─────────────────────────────────────────────────────────────────────────
    def _connect(self):
        self._set_status('Conectando…', 'yellow')
        run_async(QRSClient().list_apps(), self._on_apps_loaded)

    def _on_apps_loaded(self, result):
        if isinstance(result, Exception):
            self._set_status(f'Error: {result}', 'red')
            return
        self._apps_all = sorted(result, key=lambda a: (a['stream'], a['name'].upper()))
        self._set_status(f'Conectado — {len(self._apps_all)} apps', 'green')
        self._render_apps(self._apps_all)

    def _render_apps(self, apps):
        if not hasattr(self, '_apps_tree'): return
        self._apps_tree.delete(*self._apps_tree.get_children())
        self._app_ids.clear()
        streams = {}
        for a in apps:
            s = a['stream']
            if s not in streams:
                streams[s] = self._apps_tree.insert('', 'end',
                    text=f'  📁 {s}', tags=('stream',), open=True)
            node = self._apps_tree.insert(streams[s], 'end',
                text=f'  {a["name"]}', tags=('app',))
            self._app_ids[node] = a
        self._apps_count.config(text=f'{len(apps)} apps')

    def _filter_apps(self, *_):
        if not hasattr(self, '_apps_tree'): return
        q = self._search_var.get().strip().lower()
        if not q or 'buscar' in q:
            self._render_apps(self._apps_all)
        else:
            self._render_apps([a for a in self._apps_all
                               if q in a['name'].lower() or q in a.get('description','').lower()])

    # ─────────────────────────────────────────────────────────────────────────
    # SELECCIÓN DE APP
    # ─────────────────────────────────────────────────────────────────────────
    def _on_app_select(self, _):
        sel = self._apps_tree.selection()
        if not sel or sel[0] not in self._app_ids: return
        self._open_app(self._app_ids[sel[0]])

    def _on_history_select(self, _):
        sel = self._hist_list.curselection()
        if not sel: return
        idx = sel[0]
        if idx < len(self._history):
            self._open_app(self._history[idx])

    def _open_app(self, app):
        self._current_app = app
        self._app_title.config(text=app['name'])
        self._app_id_lbl.config(text=app['id'])
        mod = app['last_modified'][:10] if app['last_modified'] else '—'
        self._app_meta.config(text=f"Stream: {app['stream']}   |   Modificado: {mod}")
        self._reload_lbl.config(text='Cargando info…')

        # Limpiar
        self._sheets_list.delete(0, 'end'); self._sheets_data = []
        self._obj_tree.delete(*self._obj_tree.get_children())
        self._json_tree.load({}); self._current_props = {}
        self._script_text.config(state='normal')
        self._script_text.delete('1.0','end')
        self._script_text.config(state='disabled')

        self._status(f'Cargando «{app["name"]}»…')

        # Actualizar historial
        self._history = [h for h in self._history if h['id'] != app['id']]
        self._history.insert(0, app)
        self._history = self._history[:self.HISTORY_MAX]
        self._hist_list.delete(0, 'end')
        for h in self._history:
            self._hist_list.insert('end', f'  {h["name"]}')

        # Cargar en paralelo
        run_async(self._async_load_sheets(app['id']), self._on_sheets_loaded)
        run_async(self._async_load_script(app['id']), lambda r: self._on_script_loaded(r, auto=True))
        run_async(self._async_load_variables(app['id']), self._on_variables_loaded)
        run_async(self._async_app_info(app['id']), self._on_app_info)

    # ─────────────────────────────────────────────────────────────────────────
    # HOJAS
    # ─────────────────────────────────────────────────────────────────────────
    async def _async_load_sheets(self, app_id):
        s = await self.sessions.get(app_id)
        h = await s.create_session_object({
            'qInfo': {'qType': 'SheetList'},
            'qAppObjectListDef': {'qType': 'sheet',
                                  'qData': {'title': '/qMetaDef/title', 'rank': '/rank'}}
        })
        layout = await s.get_layout(h)
        items  = layout.get('qAppObjectList', {}).get('qItems', [])
        sheets = [{'id': i['qInfo']['qId'],
                   'title': i.get('qData', {}).get('title', i['qInfo']['qId']),
                   'rank':  i.get('qData', {}).get('rank', 0)} for i in items]
        return sorted(sheets, key=lambda x: x['rank'])

    def _on_sheets_loaded(self, result):
        if isinstance(result, Exception):
            self._status(f'Error hojas: {result}'); return
        self._sheets_data = result
        self._sheets_list.delete(0, 'end')
        for i, sh in enumerate(result):
            self._sheets_list.insert('end', f'  {i+1:02d}.  {sh["title"]}')
        self._status(f'{len(result)} hojas')

    def _on_sheet_select(self, _):
        sel = self._sheets_list.curselection()
        if not sel or not self._current_app: return
        sh = self._sheets_data[sel[0]]
        self._obj_tree.delete(*self._obj_tree.get_children())
        run_async(self._async_load_objects(self._current_app['id'], sh['id']),
                  self._on_objects_loaded)

    async def _async_load_objects(self, app_id, sheet_id):
        s  = await self.sessions.get(app_id)
        r  = await s.call(s.app_handle, 'GetObject', [sheet_id])
        sh = r['qReturn']['qHandle']
        ly = await s.get_layout(sh)
        return [{'id': c['qInfo']['qId'], 'type': c['qInfo']['qType'],
                 'title': c.get('qMeta', {}).get('title', '')}
                for c in ly.get('qChildList', {}).get('qItems', [])]

    def _on_objects_loaded(self, result):
        if isinstance(result, Exception): return
        self._obj_tree.delete(*self._obj_tree.get_children())
        for i, o in enumerate(result):
            tag = 'even' if i % 2 == 0 else 'odd'
            self._obj_tree.insert('', 'end',
                values=(o['type'], o['title'], o['id']), tags=(tag,), iid=o['id'])
        self._nb.select(0)

    def _on_object_select(self, _):
        sel = self._obj_tree.selection()
        if not sel or not self._current_app: return
        run_async(self._async_load_props(self._current_app['id'], sel[0]),
                  self._on_props_loaded)

    async def _async_load_props(self, app_id, obj_id):
        s  = await self.sessions.get(app_id)
        r  = await s.call(s.app_handle, 'GetObject', [obj_id])
        oh = r['qReturn']['qHandle']
        pr = await s.call(oh, 'GetEffectiveProperties')
        return pr.get('qProp', pr)

    def _on_props_loaded(self, result):
        if isinstance(result, Exception): return
        self._current_props = result
        self._json_tree.load(result)
        self._nb.select(1)

    # ─────────────────────────────────────────────────────────────────────────
    # SCRIPT
    # ─────────────────────────────────────────────────────────────────────────
    async def _async_load_script(self, app_id):
        s = await self.sessions.get(app_id)
        r = await s.call(s.app_handle, 'GetScript')
        return r.get('qScript', '')

    def _on_script_loaded(self, result, auto=False):
        if isinstance(result, Exception): return
        self._script_text.config(state='normal')
        self._script_text.delete('1.0', 'end')
        self._script_text.insert('1.0', result)
        self._highlight_script()
        self._update_line_numbers()
        self._script_text.config(state='disabled')
        if not auto: self._nb.select(2)
        n_lines = result.count('\n')
        self._status(f'Script: {n_lines:,} líneas')

    def _highlight_script(self):
        txt = self._script_text
        for tag in ('kw','fn','str','cmt','tab','num'):
            txt.tag_remove(tag, '1.0', 'end')
        content = txt.get('1.0', 'end')

        def apply_tag(tag, pattern, flags=0):
            for m in re.finditer(pattern, content, flags):
                ls = content[:m.start()].count('\n') + 1
                cs = m.start() - content[:m.start()].rfind('\n') - 1
                le = content[:m.end()].count('\n') + 1
                ce = m.end() - content[:m.end()].rfind('\n') - 1
                txt.tag_add(tag, f'{ls}.{cs}', f'{le}.{ce}')

        apply_tag('tab', r'///\s*\$tab[^\n]*|//\s*\$tab[^\n]*', re.I)
        apply_tag('cmt', r'//[^\n]*')
        apply_tag('cmt', r'/\*.*?\*/', re.DOTALL)
        apply_tag('str', r"'[^'\\]*(?:\\.[^'\\]*)*'")
        apply_tag('str', r'"[^"]*"')
        apply_tag('kw', (
            r'\b(LOAD|FROM|WHERE|GROUP\s+BY|ORDER\s+BY|JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|'
            r'INNER\s+JOIN|AS|ON|IN|AND|OR|NOT|RESIDENT|PRECEDING\s+LOAD|'
            r'CONCATENATE|NoConcatenate|MAPPING\s+LOAD|STORE|INTO|DROP\s+TABLE|'
            r'DROP\s+FIELD|RENAME\s+TABLE|RENAME\s+FIELD|LET|SET|SUB|END\s+SUB|'
            r'FOR|NEXT|IF|THEN|ELSE|END\s+IF|DO|LOOP|WHILE|UNTIL|EXIT\s+SCRIPT|'
            r'DISTINCT|TOP|FIRST|SQL|CONNECT|LIB|DIRECTORY|NOCONCATENATE|'
            r'AUTOGENERATE|INLINE|CROSSTABLE|QUALIFY|UNQUALIFY|BINARY|TRACE|'
            r'COMMENT|FIELD|TABLE|TAG|HIERARCHY|SECTION|ACCESS|APPLICATION|'
            r'REPLACE|ONLY|ALL|BUNDLE|SAMPLE)\b'), re.I)
        apply_tag('fn', (
            r'\b(Date|Time|Timestamp|Year|Month|Day|Hour|Minute|Second|Now|Today|'
            r'MonthStart|MonthEnd|YearStart|YearEnd|QuarterStart|QuarterEnd|'
            r'WeekStart|WeekEnd|AddMonths|Age|NetworkDays|Num|Text|Len|Left|'
            r'Right|Mid|Upper|Lower|Trim|Index|Replace|SubField|Capitalize|'
            r'If|Alt|Pick|Match|WildMatch|Sum|Count|Avg|Min|Max|Stdev|Median|'
            r'RangeSum|RangeAvg|RangeMin|RangeMax|RangeCount|Ceil|Floor|Round|'
            r'Abs|Sign|Pow|Sqrt|Exp|Log|Concat|FirstValue|LastValue|Aggr|Total|'
            r'ApplyMap|MapSubstring|Lookup|Num#|Date#|Time#|Timestamp#|'
            r'IsNull|IsNum|IsText|Dual|Coalesce|Class|Interval|'
            r'RowNo|RecNo|FieldIndex|FieldValue|FileBaseName|Variable|'
            r'GetFieldSelections|GetCurrentSelections)\s*\('), re.I)
        apply_tag('num', r'\b\d+\.?\d*\b')

    def _update_line_numbers(self):
        content = self._script_text.get('1.0', 'end')
        n = content.count('\n')
        self._ln_text.config(state='normal')
        self._ln_text.delete('1.0', 'end')
        self._ln_text.insert('1.0', '\n'.join(f'{i:>4}' for i in range(1, n + 1)))
        self._ln_text.config(state='disabled')

    def _script_find(self, next_match=False):
        q = self._script_search.get().strip()
        if not q: return
        txt = self._script_text
        if not next_match:
            txt.tag_remove('find', '1.0', 'end')
            self._script_find_pos = []
            self._script_find_cur = 0
            content = txt.get('1.0', 'end')
            for m in re.finditer(re.escape(q), content, re.I):
                ls = content[:m.start()].count('\n') + 1
                cs = m.start() - content[:m.start()].rfind('\n') - 1
                le = content[:m.end()].count('\n') + 1
                ce = m.end() - content[:m.end()].rfind('\n') - 1
                txt.tag_add('find', f'{ls}.{cs}', f'{le}.{ce}')
                self._script_find_pos.append(f'{ls}.{cs}')
            n = len(self._script_find_pos)
            self._script_match_lbl.config(text=f'{n} coincidencias')
        if self._script_find_pos:
            pos = self._script_find_pos[self._script_find_cur % len(self._script_find_pos)]
            txt.see(pos)
            self._script_find_cur += 1

    def _export_script(self):
        if not self._current_app: return
        content = self._script_text.get('1.0', 'end')
        if not content.strip(): return
        name = self._current_app['name'].replace('/', '_').replace('\\', '_')
        path = filedialog.asksaveasfilename(
            defaultextension='.qvs',
            filetypes=[('Qlik Script', '*.qvs'), ('Texto', '*.txt'), ('Todos', '*.*')],
            initialfile=f'{name}.qvs',
            title='Exportar script')
        if path:
            Path(path).write_text(content, encoding='utf-8')
            self._status(f'Script exportado: {path}')

    # ─────────────────────────────────────────────────────────────────────────
    # VARIABLES
    # ─────────────────────────────────────────────────────────────────────────
    def _load_variables(self):
        if not self._current_app: return
        run_async(self._async_load_variables(self._current_app['id']),
                  self._on_variables_loaded)

    async def _async_load_variables(self, app_id):
        s = await self.sessions.get(app_id)
        h = await s.create_session_object({
            'qInfo': {'qType': 'VariableList'},
            'qVariableListDef': {'qType': 'variable', 'qData': {'tags': '/tags'}}
        })
        ly = await s.get_layout(h)
        return ly.get('qVariableList', {}).get('qItems', [])

    def _on_variables_loaded(self, result):
        if isinstance(result, Exception): return
        self._vars_all = result
        self._render_variables(result)

    def _render_variables(self, items):
        self._var_tree.delete(*self._var_tree.get_children())
        for i, v in enumerate(items):
            name = v.get('qName', '')
            val  = v.get('qValue', {}).get('qText', '') if isinstance(v.get('qValue'), dict) else str(v.get('qValue', ''))
            defn = v.get('qDefinition', '')[:120]
            is_sys = v.get('qIsScriptCreated', False) or name.startswith('vFecha') or name.startswith('v')
            tag = ('even' if i % 2 == 0 else 'odd',)
            self._var_tree.insert('', 'end', text=f'  {name}',
                                  values=(val[:60], defn), tags=tag,
                                  iid=f'v_{i}')

    def _filter_variables(self, *_):
        q = self._var_search.get().strip().lower()
        if not q:
            self._render_variables(self._vars_all)
        else:
            self._render_variables([v for v in self._vars_all
                                    if q in v.get('qName','').lower()
                                    or q in v.get('qDefinition','').lower()])

    # ─────────────────────────────────────────────────────────────────────────
    # CAMPOS
    # ─────────────────────────────────────────────────────────────────────────
    def _load_fields(self):
        if not self._current_app: return
        self._status('Cargando campos…')
        run_async(self._async_load_fields(self._current_app['id']),
                  self._on_fields_loaded)

    async def _async_load_fields(self, app_id):
        s = await self.sessions.get(app_id)
        h = await s.create_session_object({
            'qInfo': {'qType': 'FieldList'},
            'qFieldListDef': {'qShowSystem': False, 'qShowHidden': False,
                              'qShowDerivedFields': True,
                              'qShowSemantic': True, 'qShowSrcTables': True}
        })
        ly = await s.get_layout(h)
        return ly.get('qFieldList', {}).get('qItems', [])

    def _on_fields_loaded(self, result):
        if isinstance(result, Exception):
            self._status(f'Error campos: {result}'); return
        self._fields_all = sorted(result, key=lambda f: f.get('qName','').upper())
        self._render_fields(self._fields_all)
        self._status(f'{len(self._fields_all)} campos cargados')
        self._nb.select(4)

    def _render_fields(self, items):
        self._fld_tree.delete(*self._fld_tree.get_children())
        for i, f in enumerate(items):
            name  = f.get('qName', '')
            card  = f.get('qCardinal', 0)
            tbls  = ', '.join(f.get('qSrcTables', []))
            tag   = 'even' if i % 2 == 0 else 'odd'
            self._fld_tree.insert('', 'end', text=f'  {name}',
                                  values=(f'{card:,}', tbls[:80]), tags=(tag,))

    def _filter_fields(self, *_):
        q = self._fld_search.get().strip().lower()
        if not q: self._render_fields(self._fields_all)
        else: self._render_fields([f for f in self._fields_all
                                   if q in f.get('qName','').lower()])

    # ─────────────────────────────────────────────────────────────────────────
    # EVALUADOR DE EXPRESIONES
    # ─────────────────────────────────────────────────────────────────────────
    def _evaluate(self):
        if not self._current_app:
            self._eval_result.config(text='Selecciona un app primero', fg=st.RED); return
        expr = self._eval_var.get().strip()
        if not expr: return
        self._eval_result.config(text='Calculando…', fg=st.FG2)
        run_async(self._async_evaluate(self._current_app['id'], expr),
                  lambda r: self._on_evaluate(r, expr))

    async def _async_evaluate(self, app_id, expr):
        s = await self.sessions.get(app_id)
        e = expr if expr.startswith('=') else f'={expr}'
        r = await s.call(s.app_handle, 'EvaluateEx', [e])
        return r.get('qValue', {})

    def _on_evaluate(self, result, expr):
        if isinstance(result, Exception):
            self._eval_result.config(text=str(result), fg=st.RED); return
        txt = result.get('qText', '')
        num = result.get('qNum')
        if num is not None and str(num) != 'NaN':
            try:
                display = f'{float(num):,.2f}'
            except: display = txt
        else:
            display = txt or 'null'
        self._eval_result.config(text=display, fg=st.FG_STR)
        entry = f'{expr}  →  {display}'
        self._eval_hist.insert(0, f'  {entry}')
        if self._eval_hist.size() > 30:
            self._eval_hist.delete(30, 'end')

    def _eval_from_history(self, _):
        sel = self._eval_hist.curselection()
        if not sel: return
        line = self._eval_hist.get(sel[0]).strip()
        expr = line.split('  →  ')[0].strip()
        self._eval_var.set(expr)
        self._evaluate()

    def _eval_clear(self):
        self._eval_var.set('')
        self._eval_result.config(text='—', fg=st.FG_STR)

    # ─────────────────────────────────────────────────────────────────────────
    # INFO RECARGA DEL APP
    # ─────────────────────────────────────────────────────────────────────────
    async def _async_app_info(self, app_id):
        s = await self.sessions.get(app_id)
        r = await s.call(s.app_handle, 'GetAppLayout')
        return r.get('qLayout', {})

    def _on_app_info(self, result):
        if isinstance(result, Exception): return
        reload_time = result.get('qLastReloadTime', '')
        if reload_time:
            ts = reload_time[:19].replace('T', ' ')
            self._reload_lbl.config(text=f'Último reload: {ts}', fg=st.FG2)
        else:
            self._reload_lbl.config(text='')

    # ─────────────────────────────────────────────────────────────────────────
    # UTILIDADES
    # ─────────────────────────────────────────────────────────────────────────
    def _export_props(self):
        if not self._current_props: return
        path = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON', '*.json'), ('Todos', '*.*')],
            title='Exportar propiedades')
        if path:
            Path(path).write_text(json.dumps(self._current_props, indent=2,
                                             ensure_ascii=False), encoding='utf-8')
            self._status(f'Exportado: {path}')

    def _copy_app_id(self):
        if self._current_app:
            self.root.clipboard_clear()
            self.root.clipboard_append(self._current_app['id'])
            self._status(f'ID copiado: {self._current_app["id"]}')

    def _clear_history(self):
        self._history = []
        self._hist_list.delete(0, 'end')

    def _set_status(self, msg, color='grey'):
        c = {'green': st.GREEN, 'red': st.RED, 'yellow': st.YELLOW}.get(color, st.FG_DARK)
        self._status_dot.config(fg=c)
        self._status_lbl.config(text=msg)

    def _status(self, msg):
        self._bar.config(text=f'  {msg}')
