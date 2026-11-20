import queue
import threading
import tkinter as tk
from tkinter import ttk

from model import FormatterModel
from viewmodel import (MainViewModel, DatabaseViewModel, FormatViewModel,
                       build_preview_query)


class NoteWindow(tk.Toplevel):
    def __init__(self, master, vm):
        super().__init__(master)
        self.vm = vm
        self.title("Bloc-notes")
        self.geometry("400x300+200+200")
        self.attributes("-topmost", True)
        self.text = tk.Text(self, wrap="word", undo=True)
        self.text.pack(fill="both", expand=True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.vm.close()
        self.destroy()


def set_readonly_text(widget, content):
    widget.config(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", content)
    widget.config(state="disabled")


class DatabaseWindow(tk.Toplevel):
    FIELDS = [("IP", "127.0.0.1"), ("Port", "3306"), ("Login", ""),
              ("Mot de passe", ""), ("Base", ""), ("Table", "")]

    def __init__(self, master):
        super().__init__(master)
        self.vm = DatabaseViewModel()
        self.title("Database")
        self.geometry("600x650")

        form = ttk.Frame(self, padding=10)
        form.pack(fill="x")
        self.entries = {}
        for row, (label, default) in enumerate(self.FIELDS):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=2)
            entry = ttk.Entry(form, width=30,
                              show="*" if label == "Mot de passe" else "")
            entry.insert(0, default)
            entry.grid(row=row, column=1, sticky="we", pady=2)
            self.entries[label] = entry

        self.tls = tk.BooleanVar(value=False)
        ttk.Checkbutton(form, text="Utiliser TLS (certificat vérifié)",
                        variable=self.tls).grid(row=len(self.FIELDS), column=0,
                                                columnspan=2, sticky="w", pady=2)

        ttk.Label(self, text="Requête (lecture seule)").pack(anchor="w", padx=10)
        self.query = tk.Text(self, height=5)
        self.query.pack(fill="x", padx=10)

        buttons = ttk.Frame(self, padding=10)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Générer SELECT", command=self.fill_query).pack(side="left")
        self.run_btn = ttk.Button(buttons, text="Exécuter", command=self.run)
        self.run_btn.pack(side="right")

        self.output = tk.Text(self, state="disabled")
        self.output.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def fill_query(self):
        try:
            query = build_preview_query(self.entries["Table"].get())
        except ValueError as e:
            set_readonly_text(self.output, str(e))
            return
        self.query.delete("1.0", "end")
        self.query.insert("1.0", query)

    def run(self):
        e = self.entries
        params = (e["IP"].get().strip(), e["Port"].get().strip(),
                  e["Login"].get().strip(), e["Mot de passe"].get(),
                  e["Base"].get().strip(), self.query.get("1.0", "end").strip(),
                  self.tls.get())
        self.run_btn.config(state="disabled")
        set_readonly_text(self.output, "Exécution en cours...")
        result = queue.Queue()
        threading.Thread(target=lambda: result.put(self.vm.run(*params)),
                         daemon=True).start()
        self.after(100, self._poll, result)

    def _poll(self, result):
        if not self.winfo_exists():
            return
        try:
            text = result.get_nowait()
        except queue.Empty:
            self.after(100, self._poll, result)
            return
        set_readonly_text(self.output, text)
        self.run_btn.config(state="normal")


class FormatWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.vm = FormatViewModel()
        self.title("Formatter")
        self.geometry("600x600")

        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="Langage").pack(side="left")
        self.lang = ttk.Combobox(top, values=FormatterModel.LANGUAGES,
                                 state="readonly", width=12)
        self.lang.set("JSON")
        self.lang.pack(side="left", padx=5)
        ttk.Button(top, text="Formater", command=self.run).pack(side="right")

        ttk.Label(self, text="Texte à formater").pack(anchor="w", padx=10)
        self.input = tk.Text(self, height=12)
        self.input.pack(fill="both", expand=True, padx=10)

        ttk.Label(self, text="Résultat").pack(anchor="w", padx=10, pady=(10, 0))
        self.output = tk.Text(self, height=12, state="disabled")
        self.output.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def run(self):
        self.vm.format(self.lang.get(), self.input.get("1.0", "end").strip())
        set_readonly_text(self.output, self.vm.output)


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.vm = MainViewModel()
        self.title("Accueil")
        self.geometry("300x200")
        ttk.Button(self, text="Nouveau texte", command=self.open_note).pack(fill="x", padx=20, pady=8)
        ttk.Button(self, text="Database", command=self.open_db).pack(fill="x", padx=20, pady=8)
        ttk.Button(self, text="Formatter", command=self.open_format).pack(fill="x", padx=20, pady=8)

    def open_note(self):
        NoteWindow(self, self.vm.add_note())

    def open_db(self):
        DatabaseWindow(self)

    def open_format(self):
        FormatWindow(self)
