"""
Qlik Explorer — Ventana de escritorio para explorar apps, hojas y objetos
Ejecutar: python qlik_explorer.py
"""
import asyncio
import json
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, font

sys.path.insert(0, 'src')
from qlik_mcp.qrs_client import QRSClient
from qlik_mcp.engine_client import SessionManager


# ─────────────────────────────────────────────────────────────────────────────
# HILO ASYNCIO (corre en background, recibe tareas desde tkinter)
# ─────────────────────────────────────────────────────────────────────────────
_loop = asyncio.new_event_loop()

def _start_loop():
    asyncio.set_event_loop(_loop)
    _loop.run_forever()

threading.Thread(target=_start_loop, daemon=True).start()

def run_async(coro, callback=None):
    """Envía una coroutine al loop background y llama callback(result) en el hilo tkinter."""
    def _done(fut):
        try:
            result = fut.result()
        except Exception as e:
            result = e
        if callback:
            _root.after(0, lambda: callback(result))

    fut = asyncio.run_coroutine_threadsafe(coro, _loop)
    fut.add_done_callback(_done)


# ─────────────────────────────────────────────────────────────────────────────
# COLORES Y ESTILOS
# ─────────────────────────────────────────────────────────────────────────────
BG       = '#1e1e2e'
BG2      = '#2a2a3d'
BG3      = '#313149'
ACCENT   = '#7c6af7'
ACCENT2  = '#5c9ef5'
FG       = '#cdd6f4'
FG2      = '#a6adc8'
FG_KEY   = '#89b4fa'
FG_STR   = '#a6e3a1'
FG_NUM   = '#fab387'
FG_BOOL  = '#f38ba8'
FG_DARK  = '#6c7086'
SEL_BG   = '#45475a'
GREEN    = '#a6e3a1'
RED      = '#f38ba8'
YELLOW   = '#f9e2af'
BORDER   = '#45475a'


# ─────────────────────────────────────────────────────────────────────────────
# VISOR JSON COMO ÁRBOL
# ─────────────────────────────────────────────────────────────────────────────
class JsonTreeView(ttk.Treeview):
    def __init__(self, parent, **kw):
        super().__init__(parent, columns=('value',), **kw)
        self.heading('#0',      text='Clave',  anchor='w')
        self.heading('value',   text='Valor',  anchor='w')
        self.column('#0',       width=240, minwidth=120)
        self.column('value',    width=400, minwidth=100)
        self.tag_configure('key',   foreground=FG_KEY)
        self.tag_configure('str',   foreground=FG_STR)
        self.tag_configure('num',   foreground=FG_NUM)
        self.tag_configure('bool',  foreground=FG_BOOL)
        self.tag_configure('null',  foreground=FG_DARK)
        self.tag_configure('arr',   foreground=YELLOW)
        self.tag_configure('obj',   foreground=ACCENT)

    def load(self, data, label='root'):
        self.delete(*self.get_children())
        self._insert(self, '', label, data)

    def _insert(self, parent, parent_id, key, value):
        if isinstance(value, dict):
            node = parent.insert(parent_id, 'end', text=str(key),
                                 values=(f'{{ {len(value)} }}',), tags=('obj',), open=False)
            for k, v in value.items():
                self._insert(self, node, k, v)
        elif isinstance(value, list):
            node = parent.insert(parent_id, 'end', text=str(key),
                                 values=(f'[ {len(value)} ]',), tags=('arr',), open=False)
            for i, v in enumerate(value):
                self._insert(self, node, i, v)
        elif isinstance(value, bool):
            parent.insert(parent_id, 'end', text=str(key),
                          values=(str(value).lower(),), tags=('bool',))
        elif value is None:
            parent.insert(parent_id, 'end', text=str(key),
                          values=('null',), tags=('null',))
        elif isinstance(value, (int, float)):
            parent.insert(parent_id, 'end', text=str(key),
                          values=(str(value),), tags=('num',))
        else:
            display = str(value)[:120] + ('…' if len(str(value)) > 120 else '')
            parent.insert(parent_id, 'end', text=str(key),
                          values=(display,), tags=('str',))


# ─────────────────────────────────────────────────────────────────────────────
# APLICACIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
class QlikExplorer:
    def __init__(self, root):
        global _root
        _root = root
        self.root      = root
        self.sessions  = SessionManager()
        self._apps_all = []          # lista completa de apps
        self._app_ids  = {}          # nombre→id
        self._current_app = None

        root.title('Qlik Explorer — Coopserfun')
        root.geometry('1280x750')
        root.configure(bg=BG)
        root.resizable(True, True)

        self._apply_styles()
        self._build_ui()
        self._connect()

    # ── Estilos ttk ──────────────────────────────────────────────────────────
    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.',              background=BG,   foreground=FG,   borderwidth=0)
        style.configure('TFrame',         background=BG)
        style.configure('Panel.TFrame',   background=BG2)
        style.configure('TLabel',         background=BG,   foreground=FG,   font=('Segoe UI', 9))
        style.configure('Title.TLabel',   background=BG2,  foreground=ACCENT, font=('Segoe UI', 10, 'bold'))
        style.configure('Sub.TLabel',     background=BG2,  foreground=FG2,  font=('Segoe UI', 8))
        style.configure('Meta.TLabel',    background=BG,   foreground=FG2,  font=('Segoe UI', 8))
        style.configure('Status.TLabel',  background=BG,   foreground=FG2,  font=('Segoe UI', 8))
        style.configure('ID.TLabel',      background=BG3,  foreground=ACCENT2, font=('Consolas', 8))

        style.configure('TButton',
                        background=ACCENT, foreground='white',
                        font=('Segoe UI', 9), relief='flat', padding=(8, 4))
        style.map('TButton',
                  background=[('active', '#6352e0'), ('pressed', '#5242d0')],
                  foreground=[('active', 'white')])

        style.configure('Small.TButton',
                        background=BG3, foreground=FG2,
                        font=('Segoe UI', 8), relief='flat', padding=(4, 2))
        style.map('Small.TButton',
                  background=[('active', SEL_BG)])

        style.configure('TEntry',
                        fieldbackground=BG3, foreground=FG,
                        insertcolor=FG, borderwidth=1, relief='flat', padding=4)

        style.configure('Treeview',
                        background=BG2, foreground=FG,
                        fieldbackground=BG2, borderwidth=0,
                        rowheight=22, font=('Segoe UI', 9))
        style.configure('Treeview.Heading',
                        background=BG3, foreground=FG2,
                        font=('Segoe UI', 9, 'bold'), relief='flat')
        style.map('Treeview',
                  background=[('selected', ACCENT)],
                  foreground=[('selected', 'white')])

        style.configure('TScrollbar',
                        background=BG3, troughcolor=BG2,
                        arrowcolor=FG2, borderwidth=0, arrowsize=12)
        style.configure('TNotebook',       background=BG,  borderwidth=0)
        style.configure('TNotebook.Tab',
                        background=BG3, foreground=FG2,
                        font=('Segoe UI', 9), padding=(12, 5))
        style.map('TNotebook.Tab',
                  background=[('selected', BG2)],
                  foreground=[('selected', FG)])
        style.configure('TSeparator',      background=BORDER)

    # ── Construcción de la UI ─────────────────────────────────────────────────
    def _build_ui(self):
        # ── Top bar ──
        top = tk.Frame(self.root, bg=BG3, height=48)
        top.pack(fill='x', side='top')
        top.pack_propagate(False)

        tk.Label(top, text='⬡  QLIK EXPLORER', bg=BG3, fg=ACCENT,
                 font=('Segoe UI', 13, 'bold')).pack(side='left', padx=16, pady=10)

        self._status_dot = tk.Label(top, text='●', bg=BG3, fg=RED, font=('Segoe UI', 12))
        self._status_dot.pack(side='right', padx=4, pady=10)
        self._status_lbl = ttk.Label(top, text='Conectando…', style='Status.TLabel')
        self._status_lbl['background'] = BG3
        self._status_lbl.pack(side='right', padx=(0, 8), pady=10)

        # ── Main area (3 paneles) ──
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill='both', expand=True)

        # Panel APPS (izquierda)
        self._build_apps_panel(main)

        ttk.Separator(main, orient='vertical').pack(side='left', fill='y', padx=1)

        # Panel HOJAS (centro)
        self._build_sheets_panel(main)

        ttk.Separator(main, orient='vertical').pack(side='left', fill='y', padx=1)

        # Panel DETALLE (derecha)
        self._build_detail_panel(main)

        # ── Status bar ──
        self._statusbar = tk.Label(self.root, text='Iniciando…',
                                   bg=BG3, fg=FG2, font=('Segoe UI', 8),
                                   anchor='w', padx=10)
        self._statusbar.pack(fill='x', side='bottom', ipady=3)

    def _build_apps_panel(self, parent):
        frame = tk.Frame(parent, bg=BG2, width=310)
        frame.pack(side='left', fill='y')
        frame.pack_propagate(False)

        # Cabecera
        hdr = tk.Frame(frame, bg=BG3, height=36)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        tk.Label(hdr, text='APLICACIONES', bg=BG3, fg=FG2,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=10, pady=8)
        self._apps_count = tk.Label(hdr, text='', bg=BG3, fg=FG_DARK,
                                    font=('Segoe UI', 8))
        self._apps_count.pack(side='right', padx=8)

        # Buscador
        search_frame = tk.Frame(frame, bg=BG2, pady=6)
        search_frame.pack(fill='x', padx=8)
        self._search_var = tk.StringVar()
        self._search_var.trace('w', self._filter_apps)
        entry = ttk.Entry(search_frame, textvariable=self._search_var)
        entry.pack(fill='x')
        entry.insert(0, '  Buscar app…')
        entry.bind('<FocusIn>',  lambda e: entry.delete(0, 'end') if entry.get().strip() == 'Buscar app…' else None)
        entry.bind('<FocusOut>', lambda e: entry.insert(0, '  Buscar app…') if not entry.get().strip() else None)

        # Árbol de apps
        tree_frame = tk.Frame(frame, bg=BG2)
        tree_frame.pack(fill='both', expand=True)

        self._apps_tree = ttk.Treeview(tree_frame, show='tree', selectmode='browse')
        scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self._apps_tree.yview)
        self._apps_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self._apps_tree.pack(fill='both', expand=True)
        self._apps_tree.bind('<<TreeviewSelect>>', self._on_app_select)

        # Tags de árbol
        self._apps_tree.tag_configure('stream',  foreground=FG_DARK,  font=('Segoe UI', 8, 'bold'))
        self._apps_tree.tag_configure('app',     foreground=FG,       font=('Segoe UI', 9))
        self._apps_tree.tag_configure('app_sel', foreground=ACCENT2,  font=('Segoe UI', 9, 'bold'))

    def _build_sheets_panel(self, parent):
        frame = tk.Frame(parent, bg=BG2, width=240)
        frame.pack(side='left', fill='y')
        frame.pack_propagate(False)

        hdr = tk.Frame(frame, bg=BG3, height=36)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        tk.Label(hdr, text='HOJAS', bg=BG3, fg=FG2,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=10, pady=8)

        list_frame = tk.Frame(frame, bg=BG2)
        list_frame.pack(fill='both', expand=True)

        self._sheets_list = tk.Listbox(
            list_frame, bg=BG2, fg=FG, selectbackground=ACCENT,
            selectforeground='white', font=('Segoe UI', 9),
            borderwidth=0, highlightthickness=0, activestyle='none',
            relief='flat')
        scroll2 = ttk.Scrollbar(list_frame, orient='vertical', command=self._sheets_list.yview)
        self._sheets_list.configure(yscrollcommand=scroll2.set)
        scroll2.pack(side='right', fill='y')
        self._sheets_list.pack(fill='both', expand=True)
        self._sheets_list.bind('<<ListboxSelect>>', self._on_sheet_select)

        self._sheets_data = []   # [{id, title}, ...]

    def _build_detail_panel(self, parent):
        frame = tk.Frame(parent, bg=BG)
        frame.pack(side='left', fill='both', expand=True)

        # Info del app seleccionada
        info = tk.Frame(frame, bg=BG3, height=80)
        info.pack(fill='x')
        info.pack_propagate(False)

        self._app_title  = ttk.Label(info, text='Selecciona una aplicación', style='Title.TLabel')
        self._app_title['background'] = BG3
        self._app_title.pack(anchor='w', padx=12, pady=(10, 2))

        id_row = tk.Frame(info, bg=BG3)
        id_row.pack(anchor='w', padx=12)
        tk.Label(id_row, text='ID:', bg=BG3, fg=FG_DARK, font=('Segoe UI', 8)).pack(side='left')
        self._app_id_lbl = tk.Label(id_row, text='—', bg=BG3, fg=ACCENT2, font=('Consolas', 8))
        self._app_id_lbl.pack(side='left', padx=4)
        self._copy_btn = ttk.Button(id_row, text='Copiar', style='Small.TButton',
                                    command=self._copy_app_id)
        self._copy_btn.pack(side='left', padx=4)

        self._app_meta = ttk.Label(info, text='', style='Sub.TLabel')
        self._app_meta['background'] = BG3
        self._app_meta.pack(anchor='w', padx=12, pady=(2, 4))

        # Tabs: Objetos / Propiedades / Script
        self._nb = ttk.Notebook(frame)
        self._nb.pack(fill='both', expand=True, padx=0, pady=0)

        # Tab Objetos
        tab_obj = tk.Frame(self._nb, bg=BG2)
        self._nb.add(tab_obj, text='  Objetos de la hoja  ')
        self._build_objects_tab(tab_obj)

        # Tab Propiedades JSON
        tab_props = tk.Frame(self._nb, bg=BG2)
        self._nb.add(tab_props, text='  Propiedades (JSON)  ')
        self._build_props_tab(tab_props)

        # Tab Script
        tab_script = tk.Frame(self._nb, bg=BG2)
        self._nb.add(tab_script, text='  Script de carga  ')
        self._build_script_tab(tab_script)

    def _build_objects_tab(self, parent):
        cols = ('type', 'title', 'id')
        self._obj_tree = ttk.Treeview(parent, columns=cols, show='headings', selectmode='browse')
        self._obj_tree.heading('type',  text='Tipo')
        self._obj_tree.heading('title', text='Título')
        self._obj_tree.heading('id',    text='ID')
        self._obj_tree.column('type',  width=130, minwidth=80)
        self._obj_tree.column('title', width=280, minwidth=100)
        self._obj_tree.column('id',    width=200, minwidth=100)
        self._obj_tree.tag_configure('even', background=BG2)
        self._obj_tree.tag_configure('odd',  background=BG3)

        scroll = ttk.Scrollbar(parent, orient='vertical', command=self._obj_tree.yview)
        self._obj_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self._obj_tree.pack(fill='both', expand=True)
        self._obj_tree.bind('<<TreeviewSelect>>', self._on_object_select)

    def _build_props_tab(self, parent):
        toolbar = tk.Frame(parent, bg=BG3, height=30)
        toolbar.pack(fill='x')
        toolbar.pack_propagate(False)
        tk.Label(toolbar, text='Propiedades del objeto seleccionado',
                 bg=BG3, fg=FG2, font=('Segoe UI', 8)).pack(side='left', padx=8, pady=6)
        ttk.Button(toolbar, text='Expandir todo', style='Small.TButton',
                   command=lambda: self._expand_all(self._json_tree)).pack(side='right', padx=6, pady=4)
        ttk.Button(toolbar, text='Colapsar todo', style='Small.TButton',
                   command=lambda: self._collapse_all(self._json_tree)).pack(side='right', padx=2, pady=4)

        self._json_tree = JsonTreeView(parent)
        scroll = ttk.Scrollbar(parent, orient='vertical', command=self._json_tree.yview)
        scroll_h = ttk.Scrollbar(parent, orient='horizontal', command=self._json_tree.xview)
        self._json_tree.configure(yscrollcommand=scroll.set, xscrollcommand=scroll_h.set)
        scroll.pack(side='right', fill='y')
        scroll_h.pack(side='bottom', fill='x')
        self._json_tree.pack(fill='both', expand=True)

    def _build_script_tab(self, parent):
        # Toolbar con buscador
        toolbar = tk.Frame(parent, bg=BG3)
        toolbar.pack(fill='x')

        tk.Label(toolbar, text='Script de carga', bg=BG3, fg=FG2,
                 font=('Segoe UI', 8, 'bold')).pack(side='left', padx=8, pady=6)

        # Buscador dentro del script
        self._script_search = tk.StringVar()
        search_e = ttk.Entry(toolbar, textvariable=self._script_search, width=22)
        search_e.pack(side='right', padx=4, pady=4)
        search_e.bind('<Return>',   lambda e: self._script_find())
        search_e.bind('<KP_Enter>', lambda e: self._script_find())
        tk.Label(toolbar, text='Buscar:', bg=BG3, fg=FG2,
                 font=('Segoe UI', 8)).pack(side='right', padx=(8, 0), pady=6)
        self._script_match_lbl = tk.Label(toolbar, text='', bg=BG3, fg=FG_DARK,
                                          font=('Segoe UI', 8))
        self._script_match_lbl.pack(side='right', padx=4)

        # Editor de texto
        txt_frame = tk.Frame(parent, bg=BG2)
        txt_frame.pack(fill='both', expand=True)

        # Números de línea
        self._script_lines = tk.Text(
            txt_frame, bg=BG3, fg=FG_DARK, font=('Consolas', 9),
            width=5, wrap='none', borderwidth=0, highlightthickness=0,
            state='disabled', cursor='arrow')
        self._script_lines.pack(side='left', fill='y')

        self._script_text = tk.Text(
            txt_frame, bg=BG2, fg=FG, insertbackground=FG,
            font=('Consolas', 9), wrap='none', borderwidth=0,
            highlightthickness=0, state='disabled', undo=True)

        scroll_v = ttk.Scrollbar(txt_frame, orient='vertical')
        scroll_h = ttk.Scrollbar(parent,    orient='horizontal', command=self._script_text.xview)

        def _sync_scroll(*args):
            self._script_text.yview(*args)
            self._script_lines.yview(*args)

        scroll_v.configure(command=_sync_scroll)
        self._script_text.configure(yscrollcommand=scroll_v.set,
                                    xscrollcommand=scroll_h.set)

        def _on_scroll(event):
            self._script_lines.yview_moveto(self._script_text.yview()[0])

        self._script_text.bind('<MouseWheel>', _on_scroll)

        scroll_v.pack(side='right',  fill='y')
        scroll_h.pack(side='bottom', fill='x')
        self._script_text.pack(side='left', fill='both', expand=True)

        # Tags de sintaxis Qlik
        kw_color   = '#569cd6'   # azul — palabras clave SQL/Qlik
        fn_color   = '#dcdcaa'   # amarillo — funciones
        str_color  = '#ce9178'   # naranja — strings
        cmt_color  = '#6a9955'   # verde — comentarios
        tab_color  = '#c586c0'   # morado — tab markers (//$tab)
        num_color  = '#b5cea8'   # verde claro — números
        find_color = '#ffd700'   # dorado — resultados de búsqueda

        self._script_text.tag_configure('kw',   foreground=kw_color)
        self._script_text.tag_configure('fn',   foreground=fn_color)
        self._script_text.tag_configure('str',  foreground=str_color)
        self._script_text.tag_configure('cmt',  foreground=cmt_color)
        self._script_text.tag_configure('tab',  foreground=tab_color,  font=('Consolas', 9, 'bold'))
        self._script_text.tag_configure('num',  foreground=num_color)
        self._script_text.tag_configure('find', background=find_color, foreground='black')

        self._script_find_positions = []
        self._script_find_idx = 0

    # ── Conexión ─────────────────────────────────────────────────────────────
    def _connect(self):
        self._set_status('Conectando a Qlik…', 'yellow')
        run_async(self._async_load_apps(), self._on_apps_loaded)

    async def _async_load_apps(self):
        qrs = QRSClient()
        return await qrs.list_apps()

    def _on_apps_loaded(self, result):
        if isinstance(result, Exception):
            self._set_status(f'Error de conexión: {result}', 'red')
            messagebox.showerror('Error', f'No se pudo conectar a Qlik:\n{result}')
            return
        self._apps_all = sorted(result, key=lambda a: (a['stream'], a['name'].upper()))
        self._set_status(f'Conectado — {len(self._apps_all)} apps disponibles', 'green')
        self._render_apps(self._apps_all)

    # ── Render de apps ────────────────────────────────────────────────────────
    def _render_apps(self, apps):
        self._apps_tree.delete(*self._apps_tree.get_children())
        self._app_ids.clear()
        streams = {}
        for a in apps:
            s = a['stream']
            if s not in streams:
                streams[s] = self._apps_tree.insert('', 'end', text=f'  📁 {s}',
                                                     tags=('stream',), open=True)
            node = self._apps_tree.insert(streams[s], 'end',
                                          text=f'  {a["name"]}',
                                          tags=('app',))
            self._app_ids[node] = a
        self._apps_count.config(text=f'{len(apps)} apps')

    def _filter_apps(self, *_):
        if not hasattr(self, '_apps_tree'): return
        q = self._search_var.get().strip().lower()
        if q in ('', 'buscar app…'):
            self._render_apps(self._apps_all)
        else:
            filtered = [a for a in self._apps_all
                        if q in a['name'].lower() or q in a.get('description', '').lower()]
            self._render_apps(filtered)

    # ── Selección de app ──────────────────────────────────────────────────────
    def _on_app_select(self, _):
        sel = self._apps_tree.selection()
        if not sel: return
        node = sel[0]
        if node not in self._app_ids: return
        app = self._app_ids[node]
        self._current_app = app

        self._app_title.config(text=app['name'])
        self._app_id_lbl.config(text=app['id'])
        stream = app['stream']
        mod    = app['last_modified'][:10] if app['last_modified'] else '—'
        self._app_meta.config(text=f'Stream: {stream}   |   Última modificación: {mod}')

        # Limpiar paneles
        self._sheets_list.delete(0, 'end')
        self._obj_tree.delete(*self._obj_tree.get_children())
        self._json_tree.load({})
        self._sheets_data = []

        self._status(f'Cargando hojas de «{app["name"]}»…')
        run_async(self._async_load_sheets(app['id']), self._on_sheets_loaded)
        # Cargar script automáticamente
        self._load_script(app['id'], auto=True)

    async def _async_load_sheets(self, app_id):
        s = await self.sessions.get(app_id)
        sheet_def = {
            'qInfo': {'qType': 'SheetList'},
            'qAppObjectListDef': {
                'qType': 'sheet',
                'qData': {'title': '/qMetaDef/title', 'rank': '/rank'},
            }
        }
        handle = await s.create_session_object(sheet_def)
        layout = await s.get_layout(handle)
        items  = layout.get('qAppObjectList', {}).get('qItems', [])
        sheets = [
            {'id': i['qInfo']['qId'],
             'title': i.get('qData', {}).get('title', i['qInfo']['qId']),
             'rank':  i.get('qData', {}).get('rank', 0)}
            for i in items
        ]
        return sorted(sheets, key=lambda x: x['rank'])

    def _on_sheets_loaded(self, result):
        if isinstance(result, Exception):
            self._status(f'Error cargando hojas: {result}')
            return
        self._sheets_data = result
        self._sheets_list.delete(0, 'end')
        for i, sh in enumerate(result):
            self._sheets_list.insert('end', f'  {i+1:02d}.  {sh["title"]}')
        self._status(f'{len(result)} hojas cargadas')

    # ── Selección de hoja ─────────────────────────────────────────────────────
    def _on_sheet_select(self, _):
        sel = self._sheets_list.curselection()
        if not sel or not self._current_app: return
        idx   = sel[0]
        sheet = self._sheets_data[idx]
        self._obj_tree.delete(*self._obj_tree.get_children())
        self._json_tree.load({})
        self._status(f'Cargando objetos de hoja «{sheet["title"]}»…')
        run_async(self._async_load_objects(self._current_app['id'], sheet['id']),
                  self._on_objects_loaded)

    async def _async_load_objects(self, app_id, sheet_id):
        s      = await self.sessions.get(app_id)
        result = await s.call(s.app_handle, 'GetObject', [sheet_id])
        sh_h   = result['qReturn']['qHandle']
        layout = await s.get_layout(sh_h)
        items  = layout.get('qChildList', {}).get('qItems', [])
        return [
            {'id':    c['qInfo']['qId'],
             'type':  c['qInfo']['qType'],
             'title': c.get('qMeta', {}).get('title', '')}
            for c in items
        ]

    def _on_objects_loaded(self, result):
        if isinstance(result, Exception):
            self._status(f'Error: {result}')
            return
        self._obj_tree.delete(*self._obj_tree.get_children())
        for i, obj in enumerate(result):
            tag = 'even' if i % 2 == 0 else 'odd'
            self._obj_tree.insert('', 'end',
                                  values=(obj['type'], obj['title'], obj['id']),
                                  tags=(tag,), iid=obj['id'])
        self._status(f'{len(result)} objetos en la hoja')
        self._nb.select(0)

    # ── Selección de objeto → propiedades ─────────────────────────────────────
    def _on_object_select(self, _):
        sel = self._obj_tree.selection()
        if not sel or not self._current_app: return
        obj_id = sel[0]
        self._status(f'Cargando propiedades de {obj_id}…')
        run_async(self._async_load_props(self._current_app['id'], obj_id),
                  self._on_props_loaded)

    async def _async_load_props(self, app_id, obj_id):
        s      = await self.sessions.get(app_id)
        result = await s.call(s.app_handle, 'GetObject', [obj_id])
        oh     = result['qReturn']['qHandle']
        props  = await s.call(oh, 'GetEffectiveProperties')
        return props.get('qProp', props)

    def _on_props_loaded(self, result):
        if isinstance(result, Exception):
            self._status(f'Error: {result}')
            return
        self._json_tree.load(result)
        self._nb.select(1)
        self._status('Propiedades cargadas')

    # ── Script de carga ───────────────────────────────────────────────────────
    def _load_script(self, app_id=None, auto=False):
        aid = app_id or (self._current_app['id'] if self._current_app else None)
        if not aid: return
        self._status('Cargando script…')
        run_async(self._async_load_script(aid),
                  lambda r: self._on_script_loaded(r, auto=auto))

    async def _async_load_script(self, app_id):
        s      = await self.sessions.get(app_id)
        result = await s.call(s.app_handle, 'GetScript')
        return result.get('qScript', '')

    def _on_script_loaded(self, result, auto=False):
        if isinstance(result, Exception):
            self._status(f'Error cargando script: {result}')
            return
        self._script_text.config(state='normal')
        self._script_text.delete('1.0', 'end')
        self._script_text.insert('1.0', result)
        self._script_highlight()
        self._script_update_lines()
        self._script_text.config(state='disabled')
        if not auto:
            self._nb.select(2)
        self._status(f'Script cargado — {result.count(chr(10)):,} líneas, {len(result):,} caracteres')

    def _script_highlight(self):
        """Aplica resaltado de sintaxis Qlik al script."""
        import re
        txt = self._script_text
        # Limpiar tags anteriores
        for tag in ('kw','fn','str','cmt','tab','num'):
            txt.tag_remove(tag, '1.0', 'end')

        content = txt.get('1.0', 'end')

        # Tab markers  ///$tab  o  //$tab
        for m in re.finditer(r'///\s*\$tab[^\n]*|//\s*\$tab[^\n]*', content, re.IGNORECASE):
            self._apply_tag(txt, 'tab', content, m.start(), m.end())

        # Comentarios de línea //  (que no sean $tab)
        for m in re.finditer(r'//[^\n]*', content):
            self._apply_tag(txt, 'cmt', content, m.start(), m.end())

        # Comentarios de bloque /* ... */
        for m in re.finditer(r'/\*.*?\*/', content, re.DOTALL):
            self._apply_tag(txt, 'cmt', content, m.start(), m.end())

        # Strings entre comillas simples
        for m in re.finditer(r"'[^'\\]*(?:\\.[^'\\]*)*'", content):
            self._apply_tag(txt, 'str', content, m.start(), m.end())

        # Strings entre comillas dobles (nombres de campo)
        for m in re.finditer(r'"[^"]*"', content):
            self._apply_tag(txt, 'str', content, m.start(), m.end())

        # Palabras clave Qlik/SQL
        keywords = (
            r'\b(LOAD|FROM|WHERE|GROUP BY|ORDER BY|HAVING|JOIN|LEFT JOIN|RIGHT JOIN|'
            r'INNER JOIN|OUTER JOIN|AS|ON|IN|NOT IN|AND|OR|NOT|IS NULL|IS NOT NULL|'
            r'RESIDENT|PRECEDING LOAD|CONCATENATE|NoConcatenate|MAPPING LOAD|'
            r'STORE|INTO|DROP TABLE|DROP FIELD|RENAME TABLE|RENAME FIELD|'
            r'LET|SET|CALL|SUB|END SUB|FOR|NEXT|IF|THEN|ELSE|END IF|'
            r'DO|LOOP|WHILE|UNTIL|EXIT|WHEN|UNLESS|'
            r'NOCONCATENATE|DISTINCT|TOP|FIRST|SAMPLE|'
            r'SQL|CONNECT|OLEDB|ODBC|CUSTOM|LIB|DIRECTORY|'
            r'ADD|REPLACE|ONLY|ALL|BUNDLE|'
            r'AUTOGENERATE|INLINE|CROSSTABLE|INTERVALMATCH|'
            r'QUALIFY|UNQUALIFY|SEMANTIC|BINARY|'
            r'TRACE|COMMENT|FIELD|FIELDS|TABLE|TABLES|TAG|TAGS|'
            r'HIERARCHY|HIERARCHYBELONGSTO|'
            r'SECTION|ACCESS|APPLICATION|EXIT SCRIPT|'
            r'QVD|QVX|TXT|CSV|FIX|DIF|XLS|XLSX|XML|HTML|KML|'
            r'UTF8|UNICODE|ANSI|OEM|CODEPAGE|NO LABELS|LABELS|'
            r'DELIMITER|QUOTE|MSQUERY|NATIVE)\b'
        )
        for m in re.finditer(keywords, content, re.IGNORECASE):
            self._apply_tag(txt, 'kw', content, m.start(), m.end())

        # Funciones comunes
        functions = (
            r'\b(Date|Time|Timestamp|Year|Month|Day|Hour|Minute|Second|Now|Today|'
            r'MonthStart|MonthEnd|YearStart|YearEnd|QuarterStart|QuarterEnd|'
            r'WeekStart|WeekEnd|AddMonths|Age|NetworkDays|'
            r'Num|Text|Len|Left|Right|Mid|Upper|Lower|Trim|'
            r'Index|Replace|SubField|Capitalize|Chr|Ord|'
            r'If|Alt|Pick|Match|WildMatch|'
            r'Sum|Count|Avg|Min|Max|Stdev|Median|Mode|'
            r'RangeSum|RangeAvg|RangeMin|RangeMax|RangeCount|'
            r'Ceil|Floor|Round|Frac|Div|Mod|Pow|Sqrt|Exp|Log|'
            r'Abs|Sign|Even|Odd|'
            r'Concat|FirstValue|LastValue|FirstSortedValue|'
            r'Aggr|Total|Dimensionality|'
            r'ApplyMap|MapSubstring|Lookup|'
            r'Num\#|Date\#|Time\#|Timestamp\#|Interval\#|Money\#|'
            r'Color|RGB|ARGB|HSL|Colormix|'
            r'GetFieldSelections|GetCurrentSelections|'
            r'RowNo|RecNo|IterNo|FieldIndex|FieldValue|'
            r'FileBaseName|FilePath|FileSize|FileTime|'
            r'Variable|GetObjectField|'
            r'Class|Interval|ValueList|ValueLoop|'
            r'IsNull|IsNum|IsText|IsPartialReload|'
            r'Coalesce|Dual|'
            r'SUM|COUNT|AVG|MIN|MAX)\s*\('
        )
        for m in re.finditer(functions, content, re.IGNORECASE):
            end = m.end() - 1  # excluir el '('
            self._apply_tag(txt, 'fn', content, m.start(), end)

        # Números
        for m in re.finditer(r'\b\d+\.?\d*\b', content):
            self._apply_tag(txt, 'num', content, m.start(), m.end())

    def _apply_tag(self, txt, tag, content, start, end):
        """Convierte offset de string a índice tkinter y aplica tag."""
        line_s = content[:start].count('\n') + 1
        col_s  = start - content[:start].rfind('\n') - 1
        line_e = content[:end].count('\n') + 1
        col_e  = end - content[:end].rfind('\n') - 1
        txt.tag_add(tag, f'{line_s}.{col_s}', f'{line_e}.{col_e}')

    def _script_update_lines(self):
        """Actualiza el panel de números de línea."""
        content  = self._script_text.get('1.0', 'end')
        n_lines  = content.count('\n')
        self._script_lines.config(state='normal')
        self._script_lines.delete('1.0', 'end')
        nums = '\n'.join(f'{i:>4}' for i in range(1, n_lines + 1))
        self._script_lines.insert('1.0', nums)
        self._script_lines.config(state='disabled')

    def _script_find(self):
        """Busca texto en el script y resalta todas las coincidencias."""
        q = self._script_search.get().strip()
        self._script_text.tag_remove('find', '1.0', 'end')
        self._script_find_positions = []
        if not q:
            self._script_match_lbl.config(text='')
            return
        content = self._script_text.get('1.0', 'end')
        import re
        for m in re.finditer(re.escape(q), content, re.IGNORECASE):
            line_s = content[:m.start()].count('\n') + 1
            col_s  = m.start() - content[:m.start()].rfind('\n') - 1
            line_e = content[:m.end()].count('\n') + 1
            col_e  = m.end() - content[:m.end()].rfind('\n') - 1
            self._script_text.tag_add('find', f'{line_s}.{col_s}', f'{line_e}.{col_e}')
            self._script_find_positions.append(f'{line_s}.{col_s}')
        n = len(self._script_find_positions)
        self._script_match_lbl.config(text=f'{n} coincidencias')
        if self._script_find_positions:
            self._script_text.see(self._script_find_positions[0])

    # ── Utilidades ────────────────────────────────────────────────────────────
    def _copy_app_id(self):
        if self._current_app:
            self.root.clipboard_clear()
            self.root.clipboard_append(self._current_app['id'])
            self._status(f'ID copiado: {self._current_app["id"]}')

    def _set_status(self, msg, color='grey'):
        colors = {'green': GREEN, 'red': RED, 'yellow': YELLOW, 'grey': FG_DARK}
        dot_color = colors.get(color, FG_DARK)
        self._status_dot.config(fg=dot_color)
        self._status_lbl.config(text=msg)

    def _status(self, msg):
        self._statusbar.config(text=f'  {msg}')

    def _expand_all(self, tree):
        def expand(node):
            tree.item(node, open=True)
            for child in tree.get_children(node):
                expand(child)
        for node in tree.get_children():
            expand(node)

    def _collapse_all(self, tree):
        def collapse(node):
            tree.item(node, open=False)
            for child in tree.get_children(node):
                collapse(child)
        for node in tree.get_children():
            collapse(node)


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    root = tk.Tk()
    app  = QlikExplorer(root)
    root.mainloop()
    _loop.call_soon_threadsafe(_loop.stop)
