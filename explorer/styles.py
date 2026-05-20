"""Colores y estilos ttk para Qlik Explorer."""
from tkinter import ttk

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

# Sintaxis script
SX_KW    = '#569cd6'
SX_FN    = '#dcdcaa'
SX_STR   = '#ce9178'
SX_CMT   = '#6a9955'
SX_TAB   = '#c586c0'
SX_NUM   = '#b5cea8'
SX_FIND  = '#ffd700'


def apply(root):
    s = ttk.Style(root)
    s.theme_use('clam')

    s.configure('.',              background=BG,   foreground=FG,   borderwidth=0)
    s.configure('TFrame',         background=BG)
    s.configure('TLabel',         background=BG,   foreground=FG,   font=('Segoe UI', 9))
    s.configure('Title.TLabel',   background=BG2,  foreground=ACCENT,  font=('Segoe UI', 10, 'bold'))
    s.configure('Sub.TLabel',     background=BG2,  foreground=FG2,  font=('Segoe UI', 8))
    s.configure('Status.TLabel',  background=BG3,  foreground=FG2,  font=('Segoe UI', 8))
    s.configure('Result.TLabel',  background=BG3,  foreground=FG_STR,  font=('Consolas', 10, 'bold'))
    s.configure('TButton',
                background=ACCENT, foreground='white',
                font=('Segoe UI', 9), relief='flat', padding=(8, 4))
    s.map('TButton',
          background=[('active', '#6352e0')])
    s.configure('Small.TButton',
                background=BG3, foreground=FG2,
                font=('Segoe UI', 8), relief='flat', padding=(4, 2))
    s.map('Small.TButton',
          background=[('active', SEL_BG)])
    s.configure('TEntry',
                fieldbackground=BG3, foreground=FG,
                insertcolor=FG, borderwidth=1, relief='flat', padding=4)
    s.configure('Treeview',
                background=BG2, foreground=FG,
                fieldbackground=BG2, borderwidth=0,
                rowheight=22, font=('Segoe UI', 9))
    s.configure('Treeview.Heading',
                background=BG3, foreground=FG2,
                font=('Segoe UI', 9, 'bold'), relief='flat')
    s.map('Treeview',
          background=[('selected', ACCENT)],
          foreground=[('selected', 'white')])
    s.configure('TScrollbar',
                background=BG3, troughcolor=BG2,
                arrowcolor=FG2, borderwidth=0, arrowsize=12)
    s.configure('TNotebook',     background=BG,  borderwidth=0)
    s.configure('TNotebook.Tab',
                background=BG3, foreground=FG2,
                font=('Segoe UI', 9), padding=(12, 5))
    s.map('TNotebook.Tab',
          background=[('selected', BG2)],
          foreground=[('selected', FG)])
    s.configure('TSeparator', background=BORDER)
