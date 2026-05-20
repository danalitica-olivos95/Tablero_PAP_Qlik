"""Entry point: python -m explorer  o  python explorer/"""
import sys
from pathlib import Path

# Asegurar que src/ quede en el path antes de importar el paquete
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import tkinter as tk
from explorer.app import QlikExplorer


def main():
    root = tk.Tk()
    QlikExplorer(root)
    root.mainloop()


if __name__ == '__main__':
    main()
