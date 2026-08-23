import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from conversor.core import SKIP_SUFFIXES, convert_many, iter_input_files, unify_files


def _resource_path(*parts: str) -> Path:
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = Path(__file__).resolve().parents[2]
    return Path(base).joinpath(*parts)


def _enable_dpi_awareness() -> None:
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


class ConversorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Conversor a Markdown")
        self.root.geometry("680x560")
        self.root.minsize(600, 460)

        self._set_icon()

        self.items: list[Path] = []
        self.unify = tk.BooleanVar(value=False)
        self.output_dir = tk.StringVar(value="")
        self.unify_name = tk.StringVar(value="combinado.md")

        self._queue: queue.Queue = queue.Queue()
        self._worker: threading.Thread | None = None

        self._build_layout()

    def _set_icon(self) -> None:
        try:
            ico = _resource_path("assets", "icon.ico")
            if ico.exists():
                self.root.iconbitmap(default=str(ico))
        except Exception:
            pass

    def _build_layout(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")
        ttk.Button(top, text="Agregar archivos...", command=self.add_files).pack(side="left")
        ttk.Button(top, text="Agregar carpeta...", command=self.add_folder).pack(side="left", padx=(8, 0))

        list_frame = ttk.Frame(self.root, padding=(10, 0))
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(list_frame, selectmode="extended")
        self.listbox.pack(side="left", fill="both", expand=True)
        list_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        list_scroll.pack(side="left", fill="y")
        self.listbox.config(yscrollcommand=list_scroll.set)

        list_btns = ttk.Frame(list_frame)
        list_btns.pack(side="left", fill="y", padx=(8, 0))
        ttk.Button(list_btns, text="Subir", command=self.move_up, width=12).pack()
        ttk.Button(list_btns, text="Bajar", command=self.move_down, width=12).pack(pady=(4, 0))
        ttk.Button(list_btns, text="Quitar", command=self.remove_selected, width=12).pack(pady=(4, 0))
        ttk.Button(list_btns, text="Vaciar lista", command=self.clear_all, width=12).pack(pady=(4, 0))

        opts = ttk.LabelFrame(self.root, text="Opciones", padding=10)
        opts.pack(fill="x", padx=10, pady=(10, 0))

        out_row = ttk.Frame(opts)
        out_row.pack(fill="x")
        ttk.Label(out_row, text="Carpeta de salida (vacío = junto al original):").pack(side="left")
        ttk.Entry(out_row, textvariable=self.output_dir).pack(side="left", fill="x", expand=True, padx=(6, 6))
        ttk.Button(out_row, text="Elegir...", command=self.choose_output_dir).pack(side="left")

        unify_row = ttk.Frame(opts)
        unify_row.pack(fill="x", pady=(8, 0))
        ttk.Checkbutton(
            unify_row,
            text="Unificar todo en un solo archivo:",
            variable=self.unify,
            command=self._toggle_unify,
        ).pack(side="left")
        self.unify_entry = ttk.Entry(unify_row, textvariable=self.unify_name, state="disabled")
        self.unify_entry.pack(side="left", fill="x", expand=True, padx=(6, 0))

        action = ttk.Frame(self.root, padding=10)
        action.pack(fill="x")
        self.convert_btn = ttk.Button(action, text="Convertir", command=self.start_conversion)
        self.convert_btn.pack(side="left")
        self.progress = ttk.Progressbar(action, mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True, padx=(10, 0))

        log_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(log_frame, height=10, state="disabled", wrap="word")
        self.log.pack(side="left", fill="both", expand=True)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        log_scroll.pack(side="left", fill="y")
        self.log.config(yscrollcommand=log_scroll.set)

    # -- lista de archivos -------------------------------------------------

    def add_files(self) -> None:
        selected = filedialog.askopenfilenames(title="Elegí uno o más archivos")
        for p in selected:
            self._add_item(Path(p))

    def add_folder(self) -> None:
        folder = filedialog.askdirectory(title="Elegí una carpeta")
        if not folder:
            return
        recursive = messagebox.askyesno("Subcarpetas", "¿Incluir también los archivos de las subcarpetas?")
        files, _missing = iter_input_files([Path(folder)], recursive)
        for f in files:
            self._add_item(f)
        if not files:
            messagebox.showinfo("Conversor", "No se encontraron archivos convertibles en esa carpeta.")

    def _add_item(self, path: Path) -> None:
        if path in self.items:
            return
        self.items.append(path)
        self.listbox.insert("end", str(path))

    def move_up(self) -> None:
        self._move_selected(-1)

    def move_down(self) -> None:
        self._move_selected(1)

    def _move_selected(self, delta: int) -> None:
        sel = list(self.listbox.curselection())
        if not sel:
            return
        indices = sel if delta < 0 else list(reversed(sel))
        for i in indices:
            j = i + delta
            if 0 <= j < len(self.items):
                self.items[i], self.items[j] = self.items[j], self.items[i]
        new_selection = [i + delta for i in sel if 0 <= i + delta < len(self.items)]
        self._refresh_listbox(new_selection)

    def remove_selected(self) -> None:
        for i in sorted(self.listbox.curselection(), reverse=True):
            del self.items[i]
        self._refresh_listbox()

    def clear_all(self) -> None:
        self.items = []
        self._refresh_listbox()

    def _refresh_listbox(self, new_selection: list[int] | None = None) -> None:
        self.listbox.delete(0, "end")
        for p in self.items:
            self.listbox.insert("end", str(p))
        for i in new_selection or []:
            self.listbox.selection_set(i)

    # -- opciones ------------------------------------------------------------

    def choose_output_dir(self) -> None:
        folder = filedialog.askdirectory(title="Carpeta de salida")
        if folder:
            self.output_dir.set(folder)

    def _toggle_unify(self) -> None:
        self.unify_entry.config(state="normal" if self.unify.get() else "disabled")

    # -- conversión ------------------------------------------------------------

    def start_conversion(self) -> None:
        if not self.items:
            messagebox.showwarning("Conversor", "Agregá al menos un archivo o una carpeta.")
            return

        unify = self.unify.get()
        unify_name = self.unify_name.get().strip()
        if unify and not unify_name:
            messagebox.showwarning("Conversor", "Indicá un nombre para el archivo combinado.")
            return

        output_dir = Path(self.output_dir.get().strip()) if self.output_dir.get().strip() else None
        items = list(self.items)
        omitidos: list[Path] = []

        if not unify:
            omitidos = [p for p in items if p.suffix.lower() in SKIP_SUFFIXES]
            items = [p for p in items if p.suffix.lower() not in SKIP_SUFFIXES]
            if not items:
                messagebox.showwarning(
                    "Conversor",
                    "No queda ningún archivo convertible (¿son todos .md? "
                    "Activá 'Unificar' para incluirlos tal cual).",
                )
                return

        self.convert_btn.config(state="disabled")
        self._clear_log()
        for p in omitidos:
            self._log(f"Aviso: '{p}' ya es .md, se omite (activá 'Unificar' para incluirlo tal cual).")
        self.progress.config(maximum=len(items), value=0)

        self._queue = queue.Queue()
        self._worker = threading.Thread(
            target=self._run_worker, args=(items, output_dir, unify, unify_name), daemon=True
        )
        self._worker.start()
        self.root.after(80, self._poll_queue)

    def _run_worker(
        self, items: list[Path], output_dir: Path | None, unify: bool, unify_name: str
    ) -> None:
        try:
            if unify:
                salida = Path(unify_name)
                if salida.suffix.lower() != ".md":
                    salida = salida.with_suffix(".md")
                if not salida.is_absolute():
                    base_dir = output_dir if output_dir is not None else items[0].parent
                    salida = base_dir / salida

                def on_result_unify(src: Path, error: Exception | None) -> None:
                    self._queue.put(("progress", src, error))

                ok, failed = unify_files(items, salida, on_result_unify)
                self._queue.put(("done_unify", ok, failed, salida))
            else:

                def on_result_many(src: Path, dest: Path | None, error: Exception | None) -> None:
                    self._queue.put(("progress", src, error))

                ok, failed = convert_many(items, output_dir, on_result_many)
                self._queue.put(("done_many", ok, failed))
        except Exception as exc:
            self._queue.put(("fatal", exc))

    def _poll_queue(self) -> None:
        try:
            while True:
                event = self._queue.get_nowait()
                kind = event[0]
                if kind == "progress":
                    _, src, error = event
                    self.progress.step(1)
                    if error is None:
                        self._log(f"OK  {src}")
                    else:
                        self._log(f"ERROR {src}: {error}")
                elif kind == "done_many":
                    _, ok, failed = event
                    self._log(f"\nListo: {ok} convertidos, {failed} con error.")
                    self._finish()
                elif kind == "done_unify":
                    _, ok, failed, salida = event
                    if ok:
                        self._log(f"\nCombinado -> {salida}")
                    self._log(f"Listo: {ok} incluidos, {failed} con error.")
                    self._finish()
                elif kind == "fatal":
                    _, exc = event
                    self._log(f"\nError inesperado: {exc}")
                    self._finish()
        except queue.Empty:
            pass
        if self._worker is not None and self._worker.is_alive():
            self.root.after(80, self._poll_queue)

    def _finish(self) -> None:
        self.convert_btn.config(state="normal")
        messagebox.showinfo("Conversor", "Conversión terminada. Mirá el detalle en el registro.")

    def _log(self, text: str) -> None:
        self.log.config(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _clear_log(self) -> None:
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")


def gui_main() -> None:
    _enable_dpi_awareness()
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("vista")
    except tk.TclError:
        pass
    ConversorApp(root)
    root.mainloop()


if __name__ == "__main__":
    gui_main()
