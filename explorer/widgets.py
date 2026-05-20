"""Widgets personalizados para Qlik Explorer."""
import tkinter as tk
from tkinter import ttk
from .styles import (BG2, BG3, FG, FG2, FG_DARK, FG_KEY, FG_STR,
                     FG_NUM, FG_BOOL, ACCENT, YELLOW)


class JsonTreeView(ttk.Treeview):
    """Árbol expandible para visualizar datos JSON."""

    def __init__(self, parent, **kw):
        super().__init__(parent, columns=('value',), **kw)
        self.heading('#0',    text='Clave',  anchor='w')
        self.heading('value', text='Valor',  anchor='w')
        self.column('#0',     width=240, minwidth=120)
        self.column('value',  width=400, minwidth=100)
        self.tag_configure('str',  foreground=FG_STR)
        self.tag_configure('num',  foreground=FG_NUM)
        self.tag_configure('bool', foreground=FG_BOOL)
        self.tag_configure('null', foreground=FG_DARK)
        self.tag_configure('arr',  foreground=YELLOW)
        self.tag_configure('obj',  foreground=ACCENT)

    def load(self, data, label='root'):
        self.delete(*self.get_children())
        self._insert('', label, data)

    def _insert(self, parent_id, key, value):
        if isinstance(value, dict):
            node = self.insert(parent_id, 'end', text=str(key),
                               values=(f'{{ {len(value)} }}',),
                               tags=('obj',), open=False)
            for k, v in value.items():
                self._insert(node, k, v)
        elif isinstance(value, list):
            node = self.insert(parent_id, 'end', text=str(key),
                               values=(f'[ {len(value)} ]',),
                               tags=('arr',), open=False)
            for i, v in enumerate(value):
                self._insert(node, i, v)
        elif isinstance(value, bool):
            self.insert(parent_id, 'end', text=str(key),
                        values=(str(value).lower(),), tags=('bool',))
        elif value is None:
            self.insert(parent_id, 'end', text=str(key),
                        values=('null',), tags=('null',))
        elif isinstance(value, (int, float)):
            self.insert(parent_id, 'end', text=str(key),
                        values=(str(value),), tags=('num',))
        else:
            display = str(value)[:150] + ('…' if len(str(value)) > 150 else '')
            self.insert(parent_id, 'end', text=str(key),
                        values=(display,), tags=('str',))

    def expand_all(self):
        def _exp(node):
            self.item(node, open=True)
            for c in self.get_children(node): _exp(c)
        for n in self.get_children(): _exp(n)

    def collapse_all(self):
        def _col(node):
            self.item(node, open=False)
            for c in self.get_children(node): _col(c)
        for n in self.get_children(): _col(n)
