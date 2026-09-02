"""
Subliminal Flash - by você :)
Exibe mensagens subliminares na tela de forma configurável.
Dependências: apenas Python 3.8+ (tkinter já vem incluso)
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import tkinter.font as tkfont
import threading
import json
import os
import random
import sys

# ─── Configuração padrão ───────────────────────────────────────────────────────

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "messages": [
        "Eu sou confiante",
        "Eu sou focado",
        "Eu alcanço meus objetivos",
    ],
    "display_time": 33,        # ms que o texto fica visível
    "interval": 5000,          # ms entre cada flash
    "font_family": "Arial",
    "font_size": 48,
    "font_bold": True,
    "text_color": "#FFFFFF",
    "bg_color": "#000000",
    "use_transparent_bg": True, # fundo totalmente transparente
    "opacity": 0.9,             # usado quando fundo não é transparente
    "position": "center",       # center | top | bottom | random
    "order": "sequential",      # sequential | random
}

# ─── Janela subliminar (overlay) ──────────────────────────────────────────────

class SubliminalOverlay:
    """Janela invisível que pisca o texto na tela por X milissegundos."""

    _TRANS_KEY = "#010203"  # cor usada como chave de transparência

    def __init__(self, parent: tk.Tk, config: dict):
        self.parent = parent
        self.config = config
        self.win: tk.Toplevel | None = None
        self.label: tk.Label | None = None
        self._build()

    def _build(self):
        w = tk.Toplevel(self.parent)
        w.withdraw()
        w.overrideredirect(True)          # sem barra de título
        w.wm_attributes("-topmost", True) # sempre na frente
        w.wm_attributes("-disabled", True)# não captura cliques

        sw = w.winfo_screenwidth()
        sh = w.winfo_screenheight()
        w.geometry(f"{sw}x{sh}+0+0")

        cfg = self.config
        font_weight = "bold" if cfg["font_bold"] else "normal"

        if cfg["use_transparent_bg"]:
            w.configure(bg=self._TRANS_KEY)
            w.wm_attributes("-transparentcolor", self._TRANS_KEY)
            lbl_bg = self._TRANS_KEY
        else:
            w.configure(bg=cfg["bg_color"])
            try:
                w.wm_attributes("-alpha", float(cfg["opacity"]))
            except Exception:
                pass
            lbl_bg = cfg["bg_color"]

        label = tk.Label(
            w,
            text="",
            fg=cfg["text_color"],
            bg=lbl_bg,
            font=(cfg["font_family"], int(cfg["font_size"]), font_weight),
        )
        label.place(relx=0.5, rely=0.5, anchor="center")  # posição inicial

        self.win = w
        self.label = label

    def flash(self, text: str):
        if not self.win:
            return
        self.label.config(text=text)
        self._reposition()
        self.win.deiconify()
        self.win.after(int(self.config["display_time"]), self._hide)

    def _reposition(self):
        pos = self.config["position"]
        if pos == "center":
            self.label.place(relx=0.5, rely=0.5, anchor="center")
        elif pos == "top":
            self.label.place(relx=0.5, rely=0.08, anchor="center")
        elif pos == "bottom":
            self.label.place(relx=0.5, rely=0.92, anchor="center")
        elif pos == "random":
            self.label.place(
                relx=random.uniform(0.1, 0.9),
                rely=random.uniform(0.1, 0.9),
                anchor="center",
            )

    def _hide(self):
        if self.win:
            self.win.withdraw()

    def rebuild(self, config: dict):
        self.config = config
        if self.win:
            self.win.destroy()
        self._build()

    def destroy(self):
        if self.win:
            self.win.destroy()
            self.win = None

# ─── Aplicativo principal ─────────────────────────────────────────────────────

BG      = "#1e1e2e"
BG2     = "#313244"
ACCENT  = "#89b4fa"
GREEN   = "#a6e3a1"
RED     = "#f38ba8"
FG      = "#cdd6f4"
FGDIM   = "#6c7086"


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Subliminal Flash")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.config = self._load_config()
        self.running = False
        self._stop_event = threading.Event()
        self._msg_index = 0
        self.overlay: SubliminalOverlay | None = None

        self._setup_style()
        self._build_ui()

    # ── Persistência ──────────────────────────────────────────────────────────

    def _load_config(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(saved)
                return merged
            except Exception:
                pass
        return DEFAULT_CONFIG.copy()

    def _save_config(self):
        self._collect_config()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Salvo", "Configurações salvas com sucesso!")

    # ── Estilo ────────────────────────────────────────────────────────────────

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook",        background=BG,  borderwidth=0)
        style.configure("TNotebook.Tab",    background=BG2, foreground=FG,   padding=[14, 6])
        style.map("TNotebook.Tab",          background=[("selected", ACCENT)], foreground=[("selected", BG)])
        style.configure("TFrame",           background=BG)
        style.configure("TCombobox",        fieldbackground=BG2, background=BG2,
                                            foreground=FG, selectbackground=ACCENT)

    # ── Interface ────────────────────────────────────────────────────────────

    def _build_ui(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=12, pady=(12, 4))

        self.f_msg  = tk.Frame(nb, bg=BG)
        self.f_time = tk.Frame(nb, bg=BG)
        self.f_look = tk.Frame(nb, bg=BG)

        nb.add(self.f_msg,  text="  💬 Mensagens  ")
        nb.add(self.f_time, text="  ⏱ Tempo  ")
        nb.add(self.f_look, text="  🎨 Aparência  ")

        self._build_tab_messages()
        self._build_tab_timing()
        self._build_tab_appearance()
        self._build_control_bar()

    # ── Aba Mensagens ─────────────────────────────────────────────────────────

    def _build_tab_messages(self):
        f = self.f_msg

        self._heading(f, "Mensagens Subliminares").pack(pady=(12, 4), padx=12, anchor="w")

        # Listbox com scroll
        lf = tk.Frame(f, bg=BG2, bd=0)
        lf.pack(fill="both", expand=True, padx=12, pady=4)

        sb = tk.Scrollbar(lf)
        sb.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            lf,
            yscrollcommand=sb.set,
            bg=BG2, fg=FG,
            selectbackground=ACCENT, selectforeground=BG,
            font=("Arial", 10), height=8,
            borderwidth=0, highlightthickness=0,
            activestyle="none",
        )
        self.listbox.pack(fill="both", expand=True, padx=4, pady=4)
        sb.config(command=self.listbox.yview)

        for msg in self.config["messages"]:
            self.listbox.insert("end", msg)

        # Campo de entrada
        ef = tk.Frame(f, bg=BG)
        ef.pack(fill="x", padx=12, pady=(4, 2))

        self.entry_msg = tk.Entry(ef, bg=BG2, fg=FG, insertbackground=FG,
                                   font=("Arial", 10), relief="flat")
        self.entry_msg.pack(fill="x", ipady=5)
        self.entry_msg.bind("<Return>", lambda _: self._add_msg())

        # Botões
        bf = tk.Frame(f, bg=BG)
        bf.pack(pady=4)
        self._btn(bf, "➕ Adicionar", self._add_msg,    GREEN).pack(side="left", padx=4)
        self._btn(bf, "✏️ Editar",    self._edit_msg,   ACCENT).pack(side="left", padx=4)
        self._btn(bf, "🗑 Remover",   self._remove_msg, RED).pack(side="left", padx=4)

        # Ordem
        of = tk.Frame(f, bg=BG)
        of.pack(pady=(4, 8))
        tk.Label(of, text="Ordem:", bg=BG, fg=FG).pack(side="left", padx=6)
        self.order_var = tk.StringVar(value=self.config["order"])
        for val, txt in [("sequential", "Sequencial"), ("random", "Aleatória")]:
            tk.Radiobutton(
                of, text=txt, variable=self.order_var, value=val,
                bg=BG, fg=FG, selectcolor=BG2, activebackground=BG,
                command=self._apply_config,
            ).pack(side="left", padx=4)

    def _add_msg(self):
        msg = self.entry_msg.get().strip()
        if msg:
            self.listbox.insert("end", msg)
            self.entry_msg.delete(0, "end")
            self._sync_messages()

    def _edit_msg(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma mensagem para editar.")
            return
        idx = sel[0]
        self.entry_msg.delete(0, "end")
        self.entry_msg.insert(0, self.listbox.get(idx))
        self.listbox.delete(idx)
        self._sync_messages()

    def _remove_msg(self):
        sel = self.listbox.curselection()
        if sel:
            self.listbox.delete(sel[0])
            self._sync_messages()

    def _sync_messages(self):
        self.config["messages"] = list(self.listbox.get(0, "end"))

    # ── Aba Tempo ─────────────────────────────────────────────────────────────

    def _build_tab_timing(self):
        f = self.f_time
        self._heading(f, "Configurações de Tempo").grid(row=0, column=0, columnspan=3,
                                                         pady=(12,6), padx=12, sticky="w")

        self.display_var = tk.IntVar(value=self.config["display_time"])
        self._row_slider(f, row=1,
                         label="Tempo de exibição (ms):",
                         var=self.display_var,
                         from_=10, to=500, resolution=1,
                         hint="⚡ 10–33 ms = subliminar   |   100 ms+ = visível")

        self.interval_var = tk.IntVar(value=self.config["interval"])
        self._row_slider(f, row=3,
                         label="Intervalo entre flashes (ms):",
                         var=self.interval_var,
                         from_=500, to=30000, resolution=500,
                         hint="Tempo de descanso entre cada mensagem")

        f.columnconfigure(1, weight=1)

    def _row_slider(self, parent, row, label, var, from_, to, resolution, hint=""):
        tk.Label(parent, text=label, bg=BG, fg=FG).grid(
            row=row, column=0, sticky="w", padx=12, pady=(10, 0))

        sl = tk.Scale(parent, from_=from_, to=to, orient="horizontal",
                      variable=var, resolution=resolution,
                      bg=BG, fg=FG, troughcolor=BG2, highlightthickness=0,
                      showvalue=False, command=lambda _: self._apply_config())
        sl.grid(row=row, column=1, sticky="ew", padx=8)

        tk.Label(parent, textvariable=var, bg=BG, fg=ACCENT, width=6,
                 font=("Arial", 10, "bold")).grid(row=row, column=2, padx=4)

        if hint:
            tk.Label(parent, text=hint, bg=BG, fg=FGDIM,
                     font=("Arial", 8)).grid(row=row+1, column=0, columnspan=3,
                                             sticky="w", padx=14, pady=(0,4))

    # ── Aba Aparência ─────────────────────────────────────────────────────────

    def _build_tab_appearance(self):
        f = self.f_look
        self._heading(f, "Aparência do Flash").grid(row=0, column=0, columnspan=3,
                                                     pady=(12,6), padx=12, sticky="w")

        # Fonte
        tk.Label(f, text="Fonte:", bg=BG, fg=FG).grid(row=1, column=0, sticky="w", padx=12, pady=4)
        families = sorted(set(tkfont.families()))
        self.font_var = tk.StringVar(value=self.config["font_family"])
        combo = ttk.Combobox(f, textvariable=self.font_var, values=families, width=22)
        combo.grid(row=1, column=1, sticky="w", padx=8)
        combo.bind("<<ComboboxSelected>>", lambda _: self._apply_config())

        # Tamanho
        tk.Label(f, text="Tamanho:", bg=BG, fg=FG).grid(row=2, column=0, sticky="w", padx=12, pady=4)
        self.size_var = tk.IntVar(value=self.config["font_size"])
        tk.Scale(f, from_=12, to=120, orient="horizontal", variable=self.size_var,
                 bg=BG, fg=FG, troughcolor=BG2, highlightthickness=0, showvalue=True,
                 command=lambda _: self._apply_config()).grid(row=2, column=1, sticky="ew", padx=8)

        # Negrito
        self.bold_var = tk.BooleanVar(value=self.config["font_bold"])
        tk.Checkbutton(f, text="Negrito", variable=self.bold_var,
                       bg=BG, fg=FG, selectcolor=BG2, activebackground=BG,
                       command=self._apply_config).grid(row=2, column=2, padx=4)

        # Cor do texto
        tk.Label(f, text="Cor do texto:", bg=BG, fg=FG).grid(row=3, column=0, sticky="w", padx=12, pady=4)
        self.text_color = self.config["text_color"]
        self.btn_text_color = tk.Button(
            f, bg=self.text_color, width=5, relief="flat",
            command=lambda: self._pick("text"))
        self.btn_text_color.grid(row=3, column=1, sticky="w", padx=8)

        # Fundo transparente
        self.transp_var = tk.BooleanVar(value=self.config["use_transparent_bg"])
        tk.Checkbutton(f, text="Fundo transparente (recomendado)",
                       variable=self.transp_var,
                       bg=BG, fg=FG, selectcolor=BG2, activebackground=BG,
                       command=self._apply_config).grid(row=4, column=0, columnspan=3,
                                                         sticky="w", padx=12, pady=4)

        # Cor do fundo
        tk.Label(f, text="Cor do fundo:", bg=BG, fg=FG).grid(row=5, column=0, sticky="w", padx=12, pady=4)
        self.bg_color = self.config["bg_color"]
        self.btn_bg_color = tk.Button(
            f, bg=self.bg_color, width=5, relief="flat",
            command=lambda: self._pick("bg"))
        self.btn_bg_color.grid(row=5, column=1, sticky="w", padx=8)

        # Opacidade
        tk.Label(f, text="Opacidade do fundo:", bg=BG, fg=FG).grid(row=6, column=0, sticky="w", padx=12, pady=4)
        self.opacity_var = tk.DoubleVar(value=self.config["opacity"])
        tk.Scale(f, from_=0.1, to=1.0, resolution=0.05, orient="horizontal",
                 variable=self.opacity_var, bg=BG, fg=FG, troughcolor=BG2,
                 highlightthickness=0, showvalue=True,
                 command=lambda _: self._apply_config()).grid(row=6, column=1, sticky="ew", padx=8)

        # Posição
        tk.Label(f, text="Posição:", bg=BG, fg=FG).grid(row=7, column=0, sticky="w", padx=12, pady=4)
        pf = tk.Frame(f, bg=BG)
        pf.grid(row=7, column=1, columnspan=2, sticky="w", padx=8)
        self.pos_var = tk.StringVar(value=self.config["position"])
        for val, txt in [("center","Centro"), ("top","Topo"), ("bottom","Rodapé"), ("random","Aleatório")]:
            tk.Radiobutton(pf, text=txt, variable=self.pos_var, value=val,
                           bg=BG, fg=FG, selectcolor=BG2, activebackground=BG,
                           command=self._apply_config).pack(side="left", padx=3)

        f.columnconfigure(1, weight=1)

    def _pick(self, target):
        initial = self.text_color if target == "text" else self.bg_color
        result = colorchooser.askcolor(color=initial, title="Escolha a cor")
        if result and result[1]:
            color = result[1]
            if target == "text":
                self.text_color = color
                self.btn_text_color.config(bg=color)
            else:
                self.bg_color = color
                self.btn_bg_color.config(bg=color)
            self._apply_config()

    # ── Barra de controle ─────────────────────────────────────────────────────

    def _build_control_bar(self):
        bar = tk.Frame(self.root, bg="#181825")
        bar.pack(fill="x", pady=(4, 0))

        self.lbl_status = tk.Label(bar, text="● Parado", bg="#181825", fg=RED,
                                    font=("Arial", 10, "bold"))
        self.lbl_status.pack(side="left", padx=14, pady=6)

        self._btn(bar, "💾 Salvar", self._save_config, ACCENT).pack(side="right", padx=6, pady=6)
        self.btn_toggle = self._btn(bar, "▶  Iniciar", self._toggle, GREEN, big=True)
        self.btn_toggle.pack(side="right", padx=6, pady=6)

    # ── Helpers de widget ─────────────────────────────────────────────────────

    def _heading(self, parent, text):
        return tk.Label(parent, text=text, bg=BG, fg=ACCENT, font=("Arial", 11, "bold"))

    def _btn(self, parent, text, cmd, color=ACCENT, big=False):
        size = 10 if big else 9
        return tk.Button(
            parent, text=text, command=cmd,
            bg=color, fg=BG, font=("Arial", size, "bold"),
            relief="flat", padx=12, pady=4, cursor="hand2",
            activebackground=color, activeforeground=BG,
        )

    # ── Lógica principal ──────────────────────────────────────────────────────

    def _collect_config(self):
        self._sync_messages()
        self.config.update({
            "display_time":     self.display_var.get(),
            "interval":         self.interval_var.get(),
            "font_family":      self.font_var.get(),
            "font_size":        self.size_var.get(),
            "font_bold":        self.bold_var.get(),
            "text_color":       self.text_color,
            "bg_color":         self.bg_color,
            "use_transparent_bg": self.transp_var.get(),
            "opacity":          self.opacity_var.get(),
            "position":         self.pos_var.get(),
            "order":            self.order_var.get(),
        })

    def _apply_config(self):
        self._collect_config()
        if self.overlay:
            self.overlay.rebuild(self.config)

    def _toggle(self):
        if self.running:
            self._stop()
        else:
            self._start()

    def _start(self):
        self._collect_config()
        if not self.config["messages"]:
            messagebox.showwarning("Aviso", "Adicione pelo menos uma mensagem!")
            return

        self.running = True
        self._stop_event.clear()
        self._msg_index = 0

        self.btn_toggle.config(text="⏹  Parar", bg=RED)
        self.lbl_status.config(text="● Rodando", fg=GREEN)

        self.overlay = SubliminalOverlay(self.root, self.config)

        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _stop(self):
        self.running = False
        self._stop_event.set()
        if self.overlay:
            self.root.after(0, self.overlay.destroy)
            self.overlay = None
        self.btn_toggle.config(text="▶  Iniciar", bg=GREEN)
        self.lbl_status.config(text="● Parado", fg=RED)

    def _loop(self):
        """Thread que dispara os flashes no intervalo configurado."""
        while not self._stop_event.is_set():
            msgs = self.config["messages"]
            if msgs:
                if self.config["order"] == "random":
                    msg = random.choice(msgs)
                else:
                    msg = msgs[self._msg_index % len(msgs)]
                    self._msg_index += 1
                # sempre executa UI na thread principal
                self.root.after(0, lambda m=msg: self._fire(m))

            self._stop_event.wait(self.config["interval"] / 1000)

    def _fire(self, msg: str):
        if self.running and self.overlay:
            self.overlay.flash(msg)

    def on_close(self):
        self._stop()
        self._collect_config()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        self.root.destroy()


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    root.configure(bg=BG)
    root.minsize(480, 520)

    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
