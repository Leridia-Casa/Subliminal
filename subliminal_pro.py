"""
Subliminal Pro — Software Subliminar Avançado para Windows 11
Instalação: pip install pystray pillow
Execução:   python subliminal_pro.py
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, simpledialog, filedialog
import tkinter.font as tkfont
import threading, json, os, random, re, sqlite3, subprocess, ctypes, time, csv
from ctypes import windll, Structure, POINTER
from datetime import datetime, timedelta

try:
    from PIL import Image, ImageDraw, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pystray
    HAS_TRAY = HAS_PIL  # o ícone da bandeja também é desenhado com Pillow
except ImportError:
    HAS_TRAY = False

# ── Atalhos globais ────────────────────────────────────────────────────────────
# Virtual key codes
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1

_hotkey_app = None
_hotkey_root = None
_hotkey_running = False

def _is_key_pressed(vk):
    """Verifica se uma tecla está fisicamente pressionada."""
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)

def _is_ctrl_shift_pressed():
    """Verifica se Ctrl+Shift está pressionado."""
    return (_is_key_pressed(VK_LCONTROL) or _is_key_pressed(VK_RCONTROL)) and \
           (_is_key_pressed(VK_LSHIFT) or _is_key_pressed(VK_RSHIFT))

def _letter_vk(letter, fallback):
    """Converte uma letra A-Z configurada no VK code correspondente (coincide com o código ASCII no Windows)."""
    letter = (letter or "").strip().upper()
    return ord(letter) if len(letter) == 1 and letter.isalpha() else fallback

def register_global_hotkeys(root, app):
    """Monitora hotkeys globais via polling do estado das teclas."""
    global _hotkey_app, _hotkey_root, _hotkey_running
    _hotkey_app = app
    _hotkey_root = root
    _hotkey_running = True

    print(" Atalhos globais ativos (letras configuráveis na aba Tempo)")

    # Estados anteriores (para detectar transição pressionado→solto)
    p_was_down = False
    s_was_down = False

    def hotkey_poller():
        global _hotkey_running
        nonlocal p_was_down, s_was_down

        while _hotkey_running:
            try:
                vk_p = _letter_vk(_hotkey_app.config.get("hotkey_pause", "P"), 0x50)
                vk_s = _letter_vk(_hotkey_app.config.get("hotkey_stop", "S"), 0x53)
                ctrl_shift = _is_ctrl_shift_pressed()
                p_down = ctrl_shift and _is_key_pressed(vk_p)
                s_down = ctrl_shift and _is_key_pressed(vk_s)

                # Detecta o momento de pressionar (transição de solto para pressionado)
                if p_down and not p_was_down:
                    p_was_down = True
                    try:
                        _hotkey_root.after(0, _hotkey_app._toggle)
                    except Exception as e:
                        print(f" Erro toggle: {e}")
                elif not p_down:
                    p_was_down = False

                if s_down and not s_was_down:
                    s_was_down = True
                    try:
                        _hotkey_root.after(0, lambda: (_hotkey_app._stop(), _hotkey_app.tray.tip("Subliminal Pro — Parado")))
                    except Exception as e:
                        print(f" Erro stop: {e}")
                elif not s_down:
                    s_was_down = False

            except Exception as e:
                print(f" Erro no poller: {e}")

            time.sleep(0.1)  # Polling a cada 100ms

    t = threading.Thread(target=hotkey_poller, daemon=True)
    t.start()

def unregister_global_hotkeys(root=None):
    """Para o monitoramento de hotkeys."""
    global _hotkey_running
    _hotkey_running = False

# ── Paleta ────────────────────────────────────────────────────────────────────
BG    = "#0d0d1a"; BG2 = "#1a1a2e"; BG3 = "#16213e"; CARD = "#1e1e3a"
ACC   = "#7c3aed"; ACC2 = "#3b82f6"; GREEN = "#10b981"; RED = "#ef4444"
YELL  = "#f59e0b"; FG = "#e2e8f0"; DIM = "#64748b"; BOR = "#2d2d5b"

def _lighten(hexcolor, amount=0.18):
    """Clareia uma cor hex, usado no efeito hover dos botões."""
    hexcolor = hexcolor.lstrip("#")
    r, g, b = (int(hexcolor[i:i + 2], 16) for i in (0, 2, 4))
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    return f"#{r:02x}{g:02x}{b:02x}"

def _parse_phrases(text):
    """Quebra um texto colado em frases, aceitando vírgula ou quebra de linha."""
    return [p.strip() for p in re.split(r"[\n,]+", text) if p.strip()]

CONFIG_FILE = "subliminal_config.json"
DB_FILE     = "subliminal_stats.db"

# ── Biblioteca padrão de frases ───────────────────────────────────────────────
DEFAULT_LIBRARY = {
    "Foco & Concentração": {
        "weight": 20, "active": True,
        "messages": [
            {"text": "Minha mente está completamente focada",         "weight": 10},
            {"text": "Elimino distrações com facilidade",             "weight": 10},
            {"text": "Concentro-me profundamente em cada tarefa",     "weight": 10},
            {"text": "Minha atenção é afiada e precisa",              "weight":  8},
            {"text": "Trabalho com clareza mental absoluta",          "weight": 10},
            {"text": "Permaneço no estado de fluxo facilmente",       "weight":  9},
            {"text": "Sou imune a distrações externas",               "weight":  8},
            {"text": "Cada minuto meu é produtivo e valioso",         "weight":  7},
        ]
    },
    "Confiança & Autoestima": {
        "weight": 20, "active": True,
        "messages": [
            {"text": "Sou confiante e seguro de mim mesmo",           "weight": 10},
            {"text": "Acredito no meu potencial ilimitado",           "weight": 10},
            {"text": "Mereço todo o sucesso que conquisto",           "weight":  9},
            {"text": "Sou capaz de realizar qualquer objetivo",       "weight": 10},
            {"text": "Minha autoestima cresce a cada dia",            "weight":  8},
            {"text": "Expresso minha confiança naturalmente",         "weight":  8},
            {"text": "Sou digno de amor e respeito",                  "weight":  9},
            {"text": "Minha presença irradia segurança e poder",      "weight":  7},
            {"text": "Acredito em mim mesmo completamente",           "weight": 10},
        ]
    },
    "Motivação & Produtividade": {
        "weight": 20, "active": True,
        "messages": [
            {"text": "Tenho energia e motivação abundantes",          "weight": 10},
            {"text": "Ajo com determinação e propósito claro",        "weight": 10},
            {"text": "Cada ação me aproxima dos meus sonhos",         "weight":  9},
            {"text": "Sou altamente produtivo e eficiente",           "weight": 10},
            {"text": "A disciplina é minha maior aliada",             "weight":  8},
            {"text": "Supero obstáculos com determinação",            "weight":  9},
            {"text": "Minha motivação é inabalável",                  "weight":  8},
            {"text": "Faço mais e melhor a cada dia",                 "weight":  7},
        ]
    },
    "Aprendizado Acelerado": {
        "weight": 15, "active": True,
        "messages": [
            {"text": "Absorvo conhecimento com facilidade",           "weight": 10},
            {"text": "Minha memória é excelente e poderosa",          "weight": 10},
            {"text": "Aprendo novas habilidades rapidamente",         "weight":  9},
            {"text": "Cada informação fica gravada em mim",           "weight":  8},
            {"text": "Meu cérebro processa ideias com clareza",       "weight":  8},
            {"text": "Retenho tudo que leio e estudo",                "weight":  9},
            {"text": "Sou um aprendiz natural e veloz",               "weight":  7},
        ]
    },
    "Abundância & Prosperidade": {
        "weight": 15, "active": True,
        "messages": [
            {"text": "Atraio riqueza e prosperidade",                 "weight": 10},
            {"text": "O dinheiro flui para mim naturalmente",         "weight":  9},
            {"text": "Sou merecedor de abundância total",             "weight": 10},
            {"text": "Crio valor e sou recompensado generosamente",   "weight":  9},
            {"text": "Minha mente está programada para o sucesso",    "weight": 10},
            {"text": "Oportunidades aparecem constantemente",         "weight":  8},
            {"text": "Minha renda cresce consistentemente",           "weight":  7},
        ]
    },
    "Paz & Equilíbrio Emocional": {
        "weight": 10, "active": True,
        "messages": [
            {"text": "Mantenho a calma em qualquer situação",         "weight": 10},
            {"text": "Controlo minhas emoções com maestria",          "weight":  9},
            {"text": "Sou uma pessoa tranquila e equilibrada",        "weight": 10},
            {"text": "Libero o estresse e a raiva com facilidade",    "weight":  9},
            {"text": "Paz e serenidade habitam em mim",               "weight":  8},
            {"text": "Reajo com sabedoria e equilíbrio",              "weight":  7},
        ]
    },
    "Saúde & Vitalidade": {
        "weight": 10, "active": True,
        "messages": [
            {"text": "Meu corpo está saudável e forte",               "weight": 10},
            {"text": "Tenho energia vital abundante",                 "weight":  9},
            {"text": "Cuido do meu corpo com amor e disciplina",      "weight":  8},
            {"text": "Durmo profundamente e acordo renovado",         "weight":  8},
            {"text": "Minha saúde melhora a cada dia",                "weight": 10},
            {"text": "Meu corpo se regenera naturalmente",            "weight":  7},
        ]
    },
    "Sucesso & Realizações": {
        "weight": 10, "active": True,
        "messages": [
            {"text": "Sou uma pessoa de alto desempenho",             "weight": 10},
            {"text": "O sucesso é meu estado natural",                "weight": 10},
            {"text": "Alcanço todos os meus objetivos",               "weight":  9},
            {"text": "Penso grande e realizo grande",                 "weight":  9},
            {"text": "Sou persistente e nunca desisto",               "weight":  8},
            {"text": "Transformo visão em realidade",                 "weight":  7},
        ]
    },
}

DEFAULT_CONFIG = {
    "library":             DEFAULT_LIBRARY,
    "display_time":        70,
    "interval":            3000,
    "font_family":         "Segoe UI",
    "font_size":           48,
    "font_bold":           True,
    "text_color":          "#FFFFFF",
    "use_transparent_bg":  True,
    "bg_color":            "#000000",
    "opacity":             0.9,
    "position":            "center",
    "order":               "random",
    "monitor_mode":        "primary",
    "selected_monitors":   [0],
    "auto_pause_loom":     True,
    "auto_pause_meeting":  True,
    "auto_pause_ps":       True,
    "schedule_enabled":    False,
    "schedule_start":      "09:00",
    "schedule_end":        "18:00",
    "hotkey_pause":        "P",
    "hotkey_stop":         "S",
    "goals":               [],
}

# ── ctypes: detecção de monitores ─────────────────────────────────────────────
class _RECT(Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

class _MONINFO(Structure):
    _fields_ = [("cbSize", ctypes.c_ulong), ("rcMonitor", _RECT),
                ("rcWork", _RECT), ("dwFlags", ctypes.c_ulong)]

def get_monitors(root=None):
    mons = []
    try:
        PROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong,
                                   ctypes.c_ulong, POINTER(_RECT), ctypes.c_double)
        def cb(hM, hdcM, lprc, d):
            info = _MONINFO()
            info.cbSize = ctypes.sizeof(_MONINFO)
            windll.user32.GetMonitorInfoW(hM, ctypes.byref(info))
            mons.append({"x": info.rcMonitor.left,  "y": info.rcMonitor.top,
                          "w": info.rcMonitor.right  - info.rcMonitor.left,
                          "h": info.rcMonitor.bottom - info.rcMonitor.top,
                          "primary": bool(info.dwFlags & 1)})
            return True
        windll.user32.EnumDisplayMonitors(None, None, PROC(cb), 0)
    except Exception:
        pass
    # Alguns drivers/configurações de multi-monitor reportam o mesmo monitor
    # físico duas vezes (mesma posição e tamanho) — remove essas duplicatas
    # pra não criar duas janelas de overlay sobrepostas no mesmo lugar.
    seen = set()
    unique = []
    for m in mons:
        key = (m["x"], m["y"], m["w"], m["h"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(m)
    mons = unique
    if not mons:
        if root:
            try:
                w = root.winfo_screenwidth()
                h = root.winfo_screenheight()
                mons = [{"x": 0, "y": 0, "w": w, "h": h, "primary": True}]
            except:
                pass
        else:
            # Fallback: usa primario virtual genérico
            mons = [{"x": 0, "y": 0, "w": 1920, "h": 1080, "primary": True}]
    return mons

# ── Detecção de processos externos ────────────────────────────────────────────
VK_SNAPSHOT = 0x2C

def _tasklist():
    try:
        r = subprocess.run(["tasklist", "/fo", "csv", "/nh"],
                           capture_output=True, text=True, timeout=3,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        return r.stdout.lower()
    except Exception:
        return ""

def is_loom_active():
    """Detecta se o Loom está aberto, olhando os processos rodando."""
    return any(x in _tasklist() for x in ["loom.exe", "loom helper"])

def is_meeting_active():
    """Detecta se algum app de reunião/conferência dedicado está aberto."""
    return any(x in _tasklist() for x in [
        "zoom.exe", "teams.exe", "ms-teams.exe", "skype.exe",
        "webexmta.exe", "gotomeeting.exe",
    ])

def is_printscreen():
    try:
        return bool(ctypes.windll.user32.GetAsyncKeyState(VK_SNAPSHOT) & 0x8000)
    except Exception:
        return False

# ── Esconder janela da barra de tarefas / Central de Ações ───────────────────
_GWL_EXSTYLE      = -20
_WS_EX_TOOLWINDOW = 0x00000080
_WS_EX_APPWINDOW  = 0x00040000

def hide_from_taskbar(win):
    """Marca a janela como 'tool window' pro Windows não tratá-la como app
    de verdade — sem isso, o overlay aparece/some da barra de tarefas e
    dispara o ícone de notificação (sininho) da Central de Ações a cada flash."""
    try:
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
        style = (style & ~_WS_EX_APPWINDOW) | _WS_EX_TOOLWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, _GWL_EXSTYLE, style)
    except Exception:
        pass

# ── Banco de dados de estatísticas ────────────────────────────────────────────
class StatsDB:
    def __init__(self):
        self._lock = threading.Lock()
        self.conn  = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS flash_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL, message TEXT NOT NULL, category TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS i_ts ON flash_log(ts);
        """)
        self.conn.commit()

    def log(self, msg, cat):
        with self._lock:
            self.conn.execute("INSERT INTO flash_log(ts,message,category) VALUES(?,?,?)",
                              (datetime.now().isoformat(), msg, cat))
            self.conn.commit()

    def _since(self, p):
        n = datetime.now()
        if p == "today": return n.replace(hour=0, minute=0, second=0, microsecond=0)
        if p == "week":  return n - timedelta(days=7)
        if p == "month": return n - timedelta(days=30)
        return None

    def _q(self, sql, params, since):
        p = list(params)
        if since:
            sql += (" WHERE " if "WHERE" not in sql else " AND ") + "ts >= ?"
            p.append(since.isoformat())
        return self.conn.execute(sql, p).fetchall()

    def total(self, period="all"):
        since = self._since(period)
        with self._lock:
            q = "SELECT COUNT(*) FROM flash_log"
            if since: q += " WHERE ts >= ?"; params = [since.isoformat()]
            else: params = []
            return self.conn.execute(q, params).fetchone()[0]

    def by_category(self, period="all"):
        since = self._since(period)
        with self._lock:
            q = "SELECT category,COUNT(*) as c FROM flash_log"
            if since: q += " WHERE ts >= ?"
            q += " GROUP BY category ORDER BY c DESC"
            p = [since.isoformat()] if since else []
            return self.conn.execute(q, p).fetchall()

    def top_messages(self, period="all", limit=5):
        since = self._since(period)
        with self._lock:
            q = "SELECT message,category,COUNT(*) as c FROM flash_log"
            if since: q += " WHERE ts >= ?"
            q += f" GROUP BY message ORDER BY c DESC LIMIT {limit}"
            p = [since.isoformat()] if since else []
            return self.conn.execute(q, p).fetchall()

    def timeline(self, period="week"):
        since = self._since(period)
        fmt = "%Y-%m-%d %H" if period == "today" else "%Y-%m-%d"
        with self._lock:
            q = f"SELECT strftime('{fmt}',ts),COUNT(*) FROM flash_log"
            if since: q += " WHERE ts >= ?"
            q += " GROUP BY 1 ORDER BY 1"
            p = [since.isoformat()] if since else []
            return self.conn.execute(q, p).fetchall()

    def all_rows(self, period="all"):
        since = self._since(period)
        with self._lock:
            q = "SELECT ts, message, category FROM flash_log"
            if since: q += " WHERE ts >= ?"
            q += " ORDER BY ts"
            p = [since.isoformat()] if since else []
            return self.conn.execute(q, p).fetchall()

    def close(self):
        self.conn.close()

# ── Overlay subliminar ────────────────────────────────────────────────────────
class Overlay:
    _TRANS = "#010203"

    def __init__(self, parent, config, monitors):
        self.parent = parent; self.config = config
        self.wins = []
        self._build(monitors)

    def _build(self, monitors):
        mode = self.config.get("monitor_mode", "primary")
        if mode == "primary":
            # Só o PRIMEIRO monitor marcado como principal — nunca mais que um,
            # mesmo que (por bug de driver) mais de um venha marcado como primário.
            primaries = [m for m in monitors if m.get("primary")]
            mons = [primaries[0]] if primaries else [monitors[0]]
        elif mode == "all":
            mons = monitors
        else:
            ids = self.config.get("selected_monitors", [0])
            mons = [monitors[i] for i in ids if i < len(monitors)]
        for m in mons:
            self._add(m)

    def _add(self, mon):
        w = tk.Toplevel(self.parent)
        w.withdraw()
        w.overrideredirect(True)
        w.wm_attributes("-topmost", True)
        w.wm_attributes("-disabled", True)
        try: w.wm_attributes("-toolwindow", True)  # nativo do Tk no Windows: some da barra de tarefas
        except Exception: pass
        w.geometry(f"{mon['w']}x{mon['h']}+{mon['x']}+{mon['y']}")
        w.update_idletasks()
        hide_from_taskbar(w)
        cfg = self.config
        fw = "bold" if cfg["font_bold"] else "normal"
        if cfg["use_transparent_bg"]:
            w.configure(bg=self._TRANS)
            w.wm_attributes("-transparentcolor", self._TRANS)
            lbg = self._TRANS
        else:
            w.configure(bg=cfg["bg_color"])
            try: w.wm_attributes("-alpha", float(cfg["opacity"]))
            except: pass
            lbg = cfg["bg_color"]
        lbl = tk.Label(w, text="", fg=cfg["text_color"], bg=lbg,
                       font=(cfg["font_family"], int(cfg["font_size"]), fw))
        self.wins.append((w, lbl))
        if cfg["use_transparent_bg"]:
            # Mapeia a janela uma única vez (fica sempre "aberta", porém
            # invisível pela cor-chave). Depois só o conteúdo do label muda.
            # Isso evita ficar abrindo/fechando a janela a cada flash, que é
            # o que fazia o Windows disparar o ícone de notificação da
            # Central de Ações toda vez que uma mensagem aparecia.
            w.deiconify()

    # (relx, rely, anchor) — o anchor fica preso naquele ponto e o texto
    # cresce pra dentro da tela, então cantos nunca ficam cortados na borda.
    _POSITIONS = {
        "center":       (0.5,  0.5,  "center"),
        "top":          (0.5,  0.06, "n"),
        "bottom":       (0.5,  0.94, "s"),
        "top_left":     (0.03, 0.06, "nw"),
        "top_right":    (0.97, 0.06, "ne"),
        "bottom_left":  (0.03, 0.94, "sw"),
        "bottom_right": (0.97, 0.94, "se"),
    }

    def flash(self, text, image_path=None):
        pos = self.config.get("position", "center")
        transparent = self.config.get("use_transparent_bg", True)
        photo = self._load_image(image_path) if image_path else None
        for w, lbl in self.wins:
            if photo:
                # compound="bottom" garante que o texto continua aparecendo
                # junto, embaixo da imagem, em vez de ser substituído por ela.
                lbl.config(image=photo, text=text, compound="bottom")
                lbl.image = photo  # mantém referência viva (senão o GC apaga a imagem)
            else:
                lbl.config(image="", text=text, compound="none")
                lbl.image = None

            if pos == "random":
                rx, ry, anchor = self._random_safe_spot(w, lbl)
            else:
                rx, ry, anchor = self._POSITIONS.get(pos, self._POSITIONS["center"])

            lbl.place(relx=rx, rely=ry, anchor=anchor)

            if transparent:
                # a janela já está mapeada (ver _add); o conteúdo some depois.
                # place_forget() (não só limpar o texto) garante que a posição
                # antiga é totalmente desenhada de novo — sem isso, ao pular
                # pra uma posição bem diferente (modo Aleatório), um resquício
                # da mensagem anterior podia ficar visível por um instante no
                # lugar velho, parecendo duas mensagens ao mesmo tempo.
                w.after(int(self.config["display_time"]),
                        lambda l=lbl: (l.place_forget(),
                                        l.config(text="", image="", compound="none")))
            else:
                w.deiconify()
                w.after(int(self.config["display_time"]), w.withdraw)

    def _random_safe_spot(self, w, lbl):
        """Sorteia uma posição garantindo que a frase (e imagem) inteira
        caiba dentro do monitor, sem cortar em nenhuma borda."""
        w.update_idletasks()
        lw, lh = lbl.winfo_reqwidth(), lbl.winfo_reqheight()
        ww = max(w.winfo_width(), 1)
        wh = max(w.winfo_height(), 1)
        mx = min(0.48, (lw / 2) / ww)
        my = min(0.48, (lh / 2) / wh)
        rx = random.uniform(mx, 1 - mx)
        ry = random.uniform(my, 1 - my)
        return rx, ry, "center"

    def _load_image(self, path):
        if not HAS_PIL: return None
        try:
            img = Image.open(path)
            img.thumbnail((480, 360))
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def rebuild(self, config, monitors):
        self.destroy(); self.config = config; self.wins = []
        self._build(monitors)

    def destroy(self):
        for w, _ in self.wins:
            try: w.destroy()
            except: pass
        self.wins = []

# ── Bandeja do sistema ────────────────────────────────────────────────────────
class Tray:
    def __init__(self, app):
        self.app = app; self.icon = None

    def start(self):
        if not HAS_TRAY: return
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([4, 4, 60, 60], fill="#7c3aed")
        d.text((16, 16), "SP", fill="white")
        menu = pystray.Menu(
            pystray.MenuItem("Mostrar janela",    self._show),
            pystray.MenuItem("▶/⏸ Pausar",        self._toggle),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair",              self._quit),
        )
        self.icon = pystray.Icon("SubliminalPro", img, "Subliminal Pro", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def tip(self, t):
        if self.icon:
            try: self.icon.title = t
            except: pass

    def _show(self, *_):    self.app.root.after(0, self.app.root.deiconify)
    def _toggle(self, *_):  self.app.root.after(0, self.app._toggle)
    def _quit(self, *_):    self.app.root.after(0, self.app.on_close)

    def stop(self):
        if self.icon:
            try: self.icon.stop()
            except: pass

# ── Switch liga/desliga (substitui o checkbox clássico) ───────────────────────
class ToggleSwitch(tk.Canvas):
    """Switch on/off desenhado no Canvas, no lugar do checkbox quadrado clássico."""
    def __init__(self, parent, variable, command=None, bg=None, w=40, h=22):
        bg = bg or parent["bg"]
        super().__init__(parent, width=w, height=h, bg=bg,
                          highlightthickness=0, cursor="hand2")
        self.var, self.command, self.w, self.h = variable, command, w, h
        self.bind("<Button-1>", self._on_click)
        # redesenha sozinho quando a variável muda por qualquer motivo, não só
        # pelo clique (ex: trocar de categoria selecionada atualiza o valor)
        self._trace_id = variable.trace_add("write", lambda *_: self._draw())
        self.bind("<Destroy>", lambda _: variable.trace_remove("write", self._trace_id))
        self._draw()

    def _on_click(self, _=None):
        self.var.set(not self.var.get())
        if self.command: self.command()

    def _draw(self):
        self.delete("all")
        on = bool(self.var.get())
        track = GREEN if on else BOR
        r = self.h / 2
        self.create_oval(0, 0, self.h, self.h, fill=track, outline="")
        self.create_oval(self.w - self.h, 0, self.w, self.h, fill=track, outline="")
        self.create_rectangle(r, 0, self.w - r, self.h, fill=track, outline="")
        kx = self.w - self.h + 2 if on else 2
        self.create_oval(kx, 2, kx + self.h - 4, self.h - 2, fill="white", outline="")

# ── Aplicativo principal ──────────────────────────────────────────────────────
class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Subliminal Pro")
        self.root.configure(bg=BG)
        self.root.minsize(760, 640)

        self.config   = self._load_cfg()
        self.monitors = get_monitors(root)
        self.db       = StatsDB()
        self.tray     = Tray(self)

        self.running     = False
        self._stop_evt   = threading.Event()
        self._flash_cnt  = 0
        self._last_proc  = 0
        self._proc_pause = False
        self.overlay: Overlay | None = None
        self._test_overlay: Overlay | None = None

        self._text_color = self.config["text_color"]
        self._bg_color   = self.config["bg_color"]

        self._setup_style()
        self._build_ui()
        self.tray.start()

        # Minimizar/fechar vão para a bandeja em vez de encerrar o app
        # (só a opção "Sair" do menu da bandeja encerra de verdade)
        self.root.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
        self.root.bind("<Unmap>", self._on_minimize)

        # Atalhos globais
        try:
            register_global_hotkeys(self.root, self)
        except Exception as e:
            print(f" Atalhos globais indisponíveis: {e}")

    # ── Config ────────────────────────────────────────────────────────────────
    def _load_cfg(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                m = DEFAULT_CONFIG.copy(); m.update(saved)
                return m
            except: pass
        return DEFAULT_CONFIG.copy()

    def _save_cfg(self):
        self._collect()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def _collect(self):
        try:
            self.config.update({
                "display_time":       self.v_disp.get(),
                "interval":           self.v_intv.get(),
                "font_family":        self.v_font.get(),
                "font_size":          self.v_size.get(),
                "font_bold":          self.v_bold.get(),
                "text_color":         self._text_color,
                "use_transparent_bg": self.v_transp.get(),
                "bg_color":           self._bg_color,
                "opacity":            self.v_opac.get(),
                "position":           self.v_pos.get(),
                "order":              self.v_order.get(),
                "monitor_mode":       self.v_mon_mode.get(),
                "auto_pause_loom":    self.v_p_loom.get(),
                "auto_pause_meeting": self.v_p_meet.get(),
                "auto_pause_ps":      self.v_p_ps.get(),
                "schedule_enabled":   self.v_sched_on.get(),
                "schedule_start":     self.v_sched_start.get().strip(),
                "schedule_end":       self.v_sched_end.get().strip(),
                "hotkey_pause":       self.v_hk_pause.get(),
                "hotkey_stop":        self.v_hk_stop.get(),
            })
        except AttributeError:
            pass

    # ── Estilo ────────────────────────────────────────────────────────────────
    def _setup_style(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("TNotebook",     background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=BG2, foreground=FG, padding=[14, 7])
        s.map("TNotebook.Tab",
              background=[("selected", ACC)],
              foreground=[("selected", "white")])
        s.configure("TFrame", background=BG)
        s.configure("TCombobox", fieldbackground=BG2, background=BG2,
                    foreground=FG, selectbackground=ACC)

    # ── UI principal ──────────────────────────────────────────────────────────
    def _build_ui(self):
        # A barra inferior é montada e fixada com side="bottom" ANTES do
        # Notebook, para reservar seu espaço primeiro. Se o Notebook (que usa
        # expand=True) fosse empacotado antes, ele tomaria toda a altura da
        # janela e a barra de baixo ficaria espremida/sem espaço.
        self._build_bar()
        self._build_topbar()
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=10, pady=(10, 4))
        tabs = [("💬 Mensagens", self._tab_messages),
                ("⏱ Tempo",     self._tab_timing),
                ("🎨 Aparência", self._tab_appearance),
                ("🖥 Monitores", self._tab_monitors),
                ("📊 Stats",     self._tab_stats),
                ("🎯 Metas",     self._tab_goals)]
        for name, fn in tabs:
            f = tk.Frame(nb, bg=BG)
            nb.add(f, text=f"  {name}  ")
            fn(f)

    # ── Cabeçalho ─────────────────────────────────────────────────────────────
    def _build_topbar(self):
        top = tk.Frame(self.root, bg=BG2, height=52)
        top.pack(side="top", fill="x")
        top.pack_propagate(False)
        logo = tk.Canvas(top, width=32, height=32, bg=BG2, highlightthickness=0)
        logo.pack(side="left", padx=(16, 10), pady=10)
        logo.create_oval(2, 2, 30, 30, fill=ACC, outline="")
        logo.create_text(16, 16, text="SP", fill="white", font=("Segoe UI", 9, "bold"))
        tk.Label(top, text="Subliminal Pro", bg=BG2, fg=FG,
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        tk.Frame(top, bg=ACC, height=2).pack(side="bottom", fill="x")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _h(self, p, t):
        return tk.Label(p, text=t, bg=BG3, fg=ACC, font=("Segoe UI", 10, "bold"))
    def _lbl(self, p, t, **k):
        return tk.Label(p, text=t, bg=BG, fg=FG, **k)
    def _btn(self, p, t, cmd, color=ACC, sz=9):
        hover = _lighten(color)
        b = tk.Button(p, text=t, command=cmd, bg=color, fg=BG,
                      font=("Segoe UI", sz, "bold"), relief="flat", bd=0,
                      padx=12, pady=6, cursor="hand2",
                      activebackground=hover, activeforeground=BG)
        b.bind("<Enter>", lambda _: b.config(bg=hover))
        b.bind("<Leave>", lambda _: b.config(bg=color))
        return b
    def _card(self, p, **k):
        return tk.Frame(p, bg=BG3, **k)

    def _toggle_row(self, parent, text, variable, command=None, bg=None):
        """Linha com texto + switch liga/desliga, no lugar do checkbox clássico."""
        bg = bg or parent["bg"]
        row = tk.Frame(parent, bg=bg)
        tk.Label(row, text=text, bg=bg, fg=FG, font=("Segoe UI", 9)).pack(side="left")
        ToggleSwitch(row, variable, command=command, bg=bg).pack(side="right")
        return row

    # ── Tab 1: Mensagens ──────────────────────────────────────────────────────
    def _tab_messages(self, f):
        tk.Label(f, text="Categorias e Mensagens", bg=BG, fg=ACC,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(20, 10))

        pane = tk.Frame(f, bg=BG)
        pane.pack(fill="both", expand=True, padx=10, pady=4)

        # ── Coluna esquerda: categorias ───────────────────────────────────────
        lf = self._card(pane, width=230)
        lf.pack(side="left", fill="y", padx=(0, 6))
        lf.pack_propagate(False)

        tk.Label(lf, text="CATEGORIAS", bg=BG3, fg=DIM,
                 font=("Segoe UI", 8, "bold")).pack(pady=(10, 0))
        tk.Label(lf, text="Ctrl/Shift+clique para selecionar várias", bg=BG3, fg=DIM,
                 font=("Segoe UI", 7)).pack(pady=(0, 0))
        tk.Label(lf, text="Texto claro = ativa   |   Texto apagado = inativa",
                 bg=BG3, fg=DIM, font=("Segoe UI", 7)).pack(pady=(0, 4))

        # Controles de tamanho fixo: empacotados com side="bottom" ANTES da
        # listbox, para reservarem seu espaço primeiro. Se a listbox (que usa
        # expand=True) fosse empacotada antes, ela tomaria toda a cavidade
        # vertical disponível e esses controles ficariam espremidos/sobrepostos.
        bottom = tk.Frame(lf, bg=BG3)
        bottom.pack(side="bottom", fill="x")

        self._btn(bottom, "➕ Nova categoria", self._add_cat, GREEN, 8)\
            .pack(fill="x", padx=4, pady=(4, 2))

        # Mostrado quando exatamente 1 categoria está selecionada
        self.single_cat_ctrls = tk.Frame(bottom, bg=BG3)
        wf = tk.Frame(self.single_cat_ctrls, bg=BG3)
        wf.pack(fill="x", padx=6, pady=4)
        tk.Label(wf, text="Frequência da categoria:", bg=BG3, fg=DIM,
                 font=("Segoe UI", 8)).pack(anchor="w")
        self.v_cat_w = tk.IntVar(value=10)
        self.sl_cat_w = tk.Scale(wf, from_=1, to=100, orient="horizontal",
                                  variable=self.v_cat_w, bg=BG3, fg=FG,
                                  troughcolor=BG2, highlightthickness=0,
                                  bd=0, sliderrelief="flat", sliderlength=16,
                                  showvalue=True, command=self._save_cat_w)
        self.sl_cat_w.pack(fill="x")

        self.v_cat_act = tk.BooleanVar(value=True)
        self._toggle_row(self.single_cat_ctrls, "Categoria ativa", self.v_cat_act,
                          command=self._save_cat_active, bg=BG3)\
            .pack(fill="x", padx=6, pady=4)

        cat_btns = tk.Frame(self.single_cat_ctrls, bg=BG3)
        cat_btns.pack(fill="x", padx=4, pady=(0, 8))
        self._btn(cat_btns, "✏️ Renomear", self._rename_cat, ACC2, 8)\
            .pack(side="left", fill="x", expand=True, padx=(0, 2))
        self._btn(cat_btns, "🗑 Remover", self._remove_cat, RED, 8)\
            .pack(side="left", fill="x", expand=True, padx=(2, 0))

        # Mostrado quando 0 ou 2+ categorias estão selecionadas (ação em lote)
        self.bulk_cat_ctrls = tk.Frame(bottom, bg=BG3)
        tk.Label(self.bulk_cat_ctrls,
                 text="Selecione várias categorias\npra ativar/desativar em lote:",
                 bg=BG3, fg=DIM, font=("Segoe UI", 8), justify="left")\
            .pack(anchor="w", padx=6, pady=(4, 6))
        bulk_btns = tk.Frame(self.bulk_cat_ctrls, bg=BG3)
        bulk_btns.pack(fill="x", padx=4, pady=(0, 8))
        self._btn(bulk_btns, "✅ Ativar", self._bulk_activate_cats, GREEN, 8)\
            .pack(side="left", fill="x", expand=True, padx=(0, 2))
        self._btn(bulk_btns, "🚫 Desativar", self._bulk_deactivate_cats, RED, 8)\
            .pack(side="left", fill="x", expand=True, padx=(2, 0))

        sb_cat = tk.Scrollbar(lf)
        sb_cat.pack(side="right", fill="y")
        self.cat_lb = tk.Listbox(lf, yscrollcommand=sb_cat.set,
                                  bg=BG3, fg=FG, selectbackground=ACC,
                                  selectforeground="white", font=("Segoe UI", 9),
                                  borderwidth=0, highlightthickness=0,
                                  activestyle="none", height=10,
                                  exportselection=False, selectmode="extended")
        self.cat_lb.pack(fill="both", expand=True, side="left")
        sb_cat.config(command=self.cat_lb.yview)
        self.cat_lb.bind("<<ListboxSelect>>", self._on_cat_sel)

        # ── Coluna direita: mensagens da categoria ────────────────────────────
        rf = self._card(pane)
        rf.pack(side="left", fill="both", expand=True)

        tk.Label(rf, text="MENSAGENS", bg=BG3, fg=DIM,
                 font=("Segoe UI", 8, "bold")).pack(pady=(10, 2))

        sb_msg = tk.Scrollbar(rf)
        sb_msg.pack(side="right", fill="y")
        self.msg_lb = tk.Listbox(rf, yscrollcommand=sb_msg.set,
                                  bg=BG3, fg=FG, selectbackground=ACC,
                                  selectforeground="white", font=("Segoe UI", 9),
                                  borderwidth=0, highlightthickness=0,
                                  activestyle="none", height=10,
                                  exportselection=False)
        self.msg_lb.pack(fill="both", expand=True, side="left")
        sb_msg.config(command=self.msg_lb.yview)
        self.msg_lb.bind("<<ListboxSelect>>", self._on_msg_sel)

        # Mostrado só quando 1 única categoria está selecionada
        self.msg_placeholder = tk.Label(rf, bg=BG3, fg=DIM,
                                         font=("Segoe UI", 9), justify="center")

        self.msg_edit_frame = tk.Frame(rf, bg=BG3)
        mwf = tk.Frame(self.msg_edit_frame, bg=BG3)
        mwf.pack(fill="x", padx=6, pady=4)
        tk.Label(mwf, text="Frequência desta mensagem:", bg=BG3, fg=DIM,
                 font=("Segoe UI", 8)).pack(side="left")
        self.v_msg_w = tk.IntVar(value=10)
        tk.Scale(mwf, from_=1, to=100, orient="horizontal", variable=self.v_msg_w,
                 bg=BG3, fg=FG, troughcolor=BG2, highlightthickness=0,
                 bd=0, sliderrelief="flat", sliderlength=16,
                 showvalue=True, length=180, command=self._save_msg_w)\
            .pack(side="left", fill="x", expand=True)

        # Entrada + botões
        ef = tk.Frame(self.msg_edit_frame, bg=BG3)
        ef.pack(fill="x", padx=6, pady=4)
        self.msg_ent = tk.Entry(ef, bg=BG2, fg=FG, insertbackground=FG,
                                 font=("Segoe UI", 9), relief="flat")
        self.msg_ent.pack(fill="x", ipady=5, pady=(0, 4))
        self.msg_ent.bind("<Return>", lambda _: self._add_msg())

        bf = tk.Frame(ef, bg=BG3)
        bf.pack(fill="x")
        self._btn(bf, "Adicionar", self._add_msg,    GREEN, 8).pack(side="left", padx=2)
        self._btn(bf, "✏️ Editar",    self._edit_msg,   ACC2,  8).pack(side="left", padx=2)
        self._btn(bf, "🖼 Imagem",    self._toggle_msg_image, YELL, 8).pack(side="left", padx=2)
        self._btn(bf, "🗑 Remover",   self._remove_msg, RED,   8).pack(side="left", padx=2)

        self._refresh_cats()

    def _refresh_cats(self):
        self.cat_lb.delete(0, "end")
        for cat in self.config.get("library", {}):
            self.cat_lb.insert("end", cat)
        self._style_cat_list()
        if self.cat_lb.size():
            self.cat_lb.selection_set(0)
        self._on_cat_sel(None)

    def _style_cat_list(self):
        """Pinta cada categoria da lista de acordo com o estado ativa/inativa,
        pra dar pra ver isso sem precisar clicar em cada uma."""
        lib = self.config.get("library", {})
        for i in range(self.cat_lb.size()):
            active = lib.get(self.cat_lb.get(i), {}).get("active", True)
            self.cat_lb.itemconfig(i, fg=FG if active else DIM)

    def _selected_cats(self):
        return [self.cat_lb.get(i) for i in self.cat_lb.curselection()]

    def _cur_cat(self):
        cats = self._selected_cats()
        return cats[0] if len(cats) == 1 else None

    def _bulk_set_active(self, active):
        lib = self.config.get("library", {})
        for cat in self._selected_cats():
            if cat in lib:
                lib[cat]["active"] = active
        self._style_cat_list()

    def _bulk_activate_cats(self):   self._bulk_set_active(True)
    def _bulk_deactivate_cats(self): self._bulk_set_active(False)

    def _on_cat_sel(self, _):
        cats = self._selected_cats()
        if len(cats) == 1:
            cat = cats[0]
            data = self.config.get("library", {}).get(cat, {})
            self.v_cat_w.set(data.get("weight", 10))
            self.v_cat_act.set(data.get("active", True))
            self.bulk_cat_ctrls.pack_forget()
            self.single_cat_ctrls.pack(fill="x")
            self.msg_placeholder.pack_forget()
            self.msg_edit_frame.pack(fill="x")
            self._populate_msg_lb(cat)
        else:
            self.single_cat_ctrls.pack_forget()
            self.bulk_cat_ctrls.pack(fill="x")
            self.msg_edit_frame.pack_forget()
            self.msg_lb.delete(0, "end")
            self.msg_placeholder.config(
                text="Selecione uma categoria\npra ver e editar as frases dela."
                if not cats else
                "Várias categorias selecionadas.\nSelecione só 1 pra editar as frases\n"
                "(ou use os botões ao lado para\nativar/desativar em lote).")
            self.msg_placeholder.pack(fill="both", expand=True, pady=30)

    def _populate_msg_lb(self, cat):
        self.msg_lb.delete(0, "end")
        for m in self.config.get("library", {}).get(cat, {}).get("messages", []):
            prefix = "🖼 " if m.get("image") else ""
            self.msg_lb.insert("end", prefix + m["text"])

    def _on_msg_sel(self, _):
        cat = self._cur_cat()
        if not cat: return
        sel = self.msg_lb.curselection()
        if not sel: return
        msgs = self.config["library"][cat]["messages"]
        if sel[0] < len(msgs):
            self.v_msg_w.set(msgs[sel[0]].get("weight", 10))

    def _save_cat_w(self, _=None):
        cat = self._cur_cat()
        if cat and cat in self.config.get("library", {}):
            self.config["library"][cat]["weight"] = self.v_cat_w.get()

    def _save_cat_active(self):
        cat = self._cur_cat()
        if cat and cat in self.config.get("library", {}):
            self.config["library"][cat]["active"] = self.v_cat_act.get()
            self._style_cat_list()

    def _save_msg_w(self, _=None):
        cat = self._cur_cat()
        if not cat: return
        sel = self.msg_lb.curselection()
        if not sel: return
        msgs = self.config["library"][cat]["messages"]
        if sel[0] < len(msgs):
            msgs[sel[0]]["weight"] = self.v_msg_w.get()

    def _add_cat(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Nova Categoria")
        dlg.configure(bg=BG)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.geometry("480x600")

        tk.Label(dlg, text="Nova Categoria", bg=BG, fg=ACC,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=16, pady=(16, 4))

        tk.Label(dlg, text="Nome da categoria", bg=BG, fg=FG,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(8, 2))
        tk.Label(dlg, bg=BG, fg=DIM, font=("Segoe UI", 8), justify="left", wraplength=448,
                 text="O nome organiza suas frases por tema (ex: Foco, Confiança, "
                      "Saúde). Escolha algo curto que descreva o objetivo em comum "
                      "das afirmações que você vai colocar aqui.")\
            .pack(anchor="w", padx=16, pady=(0, 6))
        name_ent = tk.Entry(dlg, bg=BG2, fg=FG, insertbackground=FG,
                             font=("Segoe UI", 10), relief="flat")
        name_ent.pack(fill="x", padx=16, ipady=6, pady=(0, 14))
        name_ent.focus_set()

        tk.Label(dlg, text="Frases (opcional)", bg=BG, fg=FG,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(0, 2))
        tk.Label(dlg, text="Cole uma frase por linha, ou separadas por vírgula.",
                 bg=BG, fg=DIM, font=("Segoe UI", 8))\
            .pack(anchor="w", padx=16, pady=(0, 6))

        tips = (
            "Boas práticas de afirmações subliminares:\n"
            "• Frases positivas, sobre o que você QUER — não sobre o que quer evitar\n"
            "• Evite a palavra \"não\" e negações (o subconsciente tende a ignorar a "
            "negação: troque \"não sou ansioso\" por \"sou calmo e tranquilo\")\n"
            "• Primeira pessoa, tempo presente (\"eu sou\", \"eu tenho\", \"eu faço\")\n"
            "• Curtas e diretas — precisam ser captadas num piscar de olhos\n"
            "• Emocionalmente positivas, algo que você realmente queira reforçar"
        )
        tk.Label(dlg, text=tips, bg=BG2, fg=FG, font=("Segoe UI", 8),
                 justify="left", wraplength=440, padx=10, pady=8)\
            .pack(fill="x", padx=16, pady=(0, 8))

        phrases_txt = tk.Text(dlg, height=8, bg=BG2, fg=FG, insertbackground=FG,
                               font=("Segoe UI", 9), relief="flat", wrap="word")
        phrases_txt.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        def submit():
            name = name_ent.get().strip()
            if not name:
                messagebox.showwarning("Nova Categoria", "Digite um nome pra categoria.", parent=dlg)
                return
            if name in self.config["library"]:
                messagebox.showwarning("Nova Categoria", "Já existe uma categoria com esse nome.", parent=dlg)
                return
            phrases = _parse_phrases(phrases_txt.get("1.0", "end"))
            self.config["library"][name] = {
                "weight": 10, "active": True,
                "messages": [{"text": p, "weight": 10, "image": None} for p in phrases],
            }
            dlg.destroy()
            self._refresh_cats()

        btns = tk.Frame(dlg, bg=BG)
        btns.pack(fill="x", padx=16, pady=(0, 16))
        self._btn(btns, "Cancelar", dlg.destroy, DIM, 9).pack(side="right", padx=(6, 0))
        self._btn(btns, "Criar categoria", submit, GREEN, 9).pack(side="right")

    def _rename_cat(self):
        cat = self._cur_cat()
        if not cat: return
        new = simpledialog.askstring("Renomear Categoria", "Novo nome:", initialvalue=cat)
        new = new.strip() if new else ""
        if not new or new == cat: return
        if new in self.config["library"]:
            messagebox.showwarning("Aviso", "Já existe uma categoria com esse nome.")
            return
        lib = self.config["library"]
        lib[new] = lib.pop(cat)
        self._refresh_cats()

    def _remove_cat(self):
        cat = self._cur_cat()
        if not cat: return
        if not messagebox.askyesno("Remover Categoria",
                f"Remover a categoria \"{cat}\" e todas as suas mensagens?"):
            return
        del self.config["library"][cat]
        self._refresh_cats()

    def _add_msg(self):
        cat = self._cur_cat()
        if not cat: return
        text = self.msg_ent.get().strip()
        if not text: return
        self.config["library"][cat]["messages"].append({"text": text, "weight": 10, "image": None})
        self._populate_msg_lb(cat)
        self.msg_ent.delete(0, "end")

    def _edit_msg(self):
        cat = self._cur_cat()
        if not cat: return
        sel = self.msg_lb.curselection()
        if not sel: return
        idx = sel[0]
        cur = self.config["library"][cat]["messages"][idx]["text"]
        new = simpledialog.askstring("Editar", "Mensagem:", initialvalue=cur)
        if new and new.strip():
            self.config["library"][cat]["messages"][idx]["text"] = new.strip()
            self._populate_msg_lb(cat)

    def _toggle_msg_image(self):
        if not HAS_PIL:
            messagebox.showinfo("Imagem",
                "Instale a biblioteca Pillow (pip install pillow) para usar imagens nas mensagens.")
            return
        cat = self._cur_cat()
        if not cat:
            messagebox.showinfo("Imagem", "Selecione uma categoria primeiro.")
            return
        sel = self.msg_lb.curselection()
        if not sel:
            messagebox.showinfo("Imagem", "Selecione uma mensagem na lista primeiro.")
            return
        idx = sel[0]
        msgs = self.config["library"][cat]["messages"]
        if idx >= len(msgs): return
        m = msgs[idx]
        if m.get("image"):
            if messagebox.askyesno("Imagem",
                    "Esta mensagem já tem uma imagem anexada.\nRemover a imagem?"):
                m["image"] = None
        else:
            path = filedialog.askopenfilename(
                title="Escolher imagem para a mensagem",
                filetypes=[("Imagens", "*.png *.jpg *.jpeg *.gif *.bmp")])
            if path:
                m["image"] = path
        self._populate_msg_lb(cat)

    def _remove_msg(self):
        cat = self._cur_cat()
        if not cat: return
        sel = self.msg_lb.curselection()
        if not sel: return
        del self.config["library"][cat]["messages"][sel[0]]
        self.msg_lb.delete(sel[0])

    # ── Tab 2: Tempo ──────────────────────────────────────────────────────────
    def _tab_timing(self, f):
        tk.Label(f, text="Tempo & Comportamento", bg=BG, fg=ACC,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(20, 10))

        # Sliders
        cf = self._card(f); cf.pack(fill="x", padx=12, pady=6)
        self.v_disp = tk.IntVar(value=self.config["display_time"])
        self.v_intv = tk.IntVar(value=self.config["interval"])

        rows = [
            ("Tempo de exibição (ms):", self.v_disp, 10, 500, 1,
             "⚡ Recomendado: 70ms (subliminar)   |   100ms+ = visível"),
            ("Intervalo entre flashes (ms):", self.v_intv, 500, 60000, 500,
             "Pausa entre cada mensagem   |   Padrão recomendado: 3000ms"),
        ]
        cf.columnconfigure(1, weight=1)
        for i, (lbl, var, lo, hi, res, hint) in enumerate(rows):
            tk.Label(cf, text=lbl, bg=BG3, fg=FG)\
                .grid(row=i*2, column=0, sticky="w", padx=12, pady=(10, 0))
            tk.Scale(cf, from_=lo, to=hi, orient="horizontal", variable=var,
                     resolution=res, bg=BG3, fg=FG, troughcolor=BG2,
                     highlightthickness=0, bd=0, sliderrelief="flat", sliderlength=16,
                     showvalue=True,
                     command=lambda _: self._apply())\
                .grid(row=i*2, column=1, sticky="ew", padx=8)
            tk.Label(cf, text=hint, bg=BG3, fg=DIM, font=("Segoe UI", 8))\
                .grid(row=i*2+1, column=0, columnspan=2, sticky="w", padx=14)

        # Ordem
        of = self._card(f); of.pack(fill="x", padx=12, pady=6)
        tk.Label(of, text="Ordem de exibição", bg=BG3, fg=ACC,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_order = tk.StringVar(value=self.config.get("order", "random"))
        for val, txt, desc in [
            ("random",          "🔀 Aleatória simples",    "(ignora pesos) — recomendado"),
            ("weighted_random", "🎲 Aleatória ponderada", "(usa os pesos de frequência)"),
            ("sequential",      "↕ Sequencial",           "(na ordem das categorias)"),
        ]:
            row = tk.Frame(of, bg=BG3); row.pack(anchor="w", padx=12, pady=2)
            tk.Radiobutton(row, text=txt, variable=self.v_order, value=val,
                           bg=BG3, fg=FG, selectcolor=BG2, activebackground=BG3,
                           command=self._apply).pack(side="left")
            tk.Label(row, text=desc, bg=BG3, fg=DIM, font=("Segoe UI", 8)).pack(side="left", padx=4)
        tk.Frame(of, height=8, bg=BG3).pack()

        # Auto-pause
        pf = self._card(f); pf.pack(fill="x", padx=12, pady=6)
        tk.Label(pf, text="⏸ Pausa Automática", bg=BG3, fg=ACC,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_p_loom = tk.BooleanVar(value=self.config.get("auto_pause_loom", True))
        self.v_p_meet = tk.BooleanVar(value=self.config.get("auto_pause_meeting", True))
        self.v_p_ps   = tk.BooleanVar(value=self.config.get("auto_pause_ps", True))
        for var, txt in [
            (self.v_p_loom, "🔴 Loom (gravação de tela aberta)"),
            (self.v_p_meet, "📹 Reunião ou compartilhamento de tela (Zoom, Teams, Meet…)"),
            (self.v_p_ps,   "📷 Print Screen pressionado"),
        ]:
            self._toggle_row(pf, txt, var, command=self._apply, bg=BG3)\
                .pack(fill="x", padx=14, pady=4)
        tk.Frame(pf, height=8, bg=BG3).pack()

        # Agendamento por horário
        sf = self._card(f); sf.pack(fill="x", padx=12, pady=6)
        tk.Label(sf, text="🕐 Agendamento por horário", bg=BG3, fg=ACC,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(8, 4))
        self.v_sched_on = tk.BooleanVar(value=self.config.get("schedule_enabled", False))
        self._toggle_row(sf, "Só exibir flashes dentro do horário abaixo",
                          self.v_sched_on, command=self._apply, bg=BG3)\
            .pack(fill="x", padx=14, pady=4)
        srow = tk.Frame(sf, bg=BG3); srow.pack(anchor="w", padx=14, pady=(2, 8))
        tk.Label(srow, text="Das", bg=BG3, fg=FG).pack(side="left")
        self.v_sched_start = tk.StringVar(value=self.config.get("schedule_start", "09:00"))
        e1 = tk.Entry(srow, textvariable=self.v_sched_start, width=6, bg=BG2, fg=FG,
                      insertbackground=FG, relief="flat", justify="center")
        e1.pack(side="left", padx=6)
        tk.Label(srow, text="até", bg=BG3, fg=FG).pack(side="left")
        self.v_sched_end = tk.StringVar(value=self.config.get("schedule_end", "18:00"))
        e2 = tk.Entry(srow, textvariable=self.v_sched_end, width=6, bg=BG2, fg=FG,
                      insertbackground=FG, relief="flat", justify="center")
        e2.pack(side="left", padx=6)
        tk.Label(srow, text="(formato 24h, HH:MM)", bg=BG3, fg=DIM,
                 font=("Segoe UI", 8)).pack(side="left", padx=6)
        for e in (e1, e2):
            e.bind("<FocusOut>", lambda _: self._apply())
            e.bind("<Return>", lambda _: self._apply())

        # Atalhos globais
        hf = self._card(f); hf.pack(fill="x", padx=12, pady=6)
        tk.Label(hf, text="⌨ Atalhos globais (Ctrl+Shift+letra)", bg=BG3, fg=ACC,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(8, 4))
        letters = [chr(c) for c in range(65, 91)]
        hrow = tk.Frame(hf, bg=BG3); hrow.pack(anchor="w", padx=14, pady=(0, 8))
        tk.Label(hrow, text="Pausar/retomar:", bg=BG3, fg=FG).pack(side="left")
        self.v_hk_pause = tk.StringVar(value=self.config.get("hotkey_pause", "P"))
        cb1 = ttk.Combobox(hrow, textvariable=self.v_hk_pause, values=letters,
                            width=3, state="readonly")
        cb1.pack(side="left", padx=(4, 14))
        tk.Label(hrow, text="Parar:", bg=BG3, fg=FG).pack(side="left")
        self.v_hk_stop = tk.StringVar(value=self.config.get("hotkey_stop", "S"))
        cb2 = ttk.Combobox(hrow, textvariable=self.v_hk_stop, values=letters,
                            width=3, state="readonly")
        cb2.pack(side="left", padx=4)
        for cb in (cb1, cb2):
            cb.bind("<<ComboboxSelected>>", lambda _: self._apply())

    # ── Tab 3: Aparência + Preview ────────────────────────────────────────────
    def _tab_appearance(self, f):
        tk.Label(f, text="Aparência do Flash", bg=BG, fg=ACC,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(20, 10))

        pane = tk.Frame(f, bg=BG)
        pane.pack(fill="both", expand=True, padx=10, pady=4)

        # Configurações
        lf = self._card(pane, width=300)
        lf.pack(side="left", fill="y", padx=(0, 6))
        lf.pack_propagate(False)

        def row(lbl, fn, pady=4):
            r = tk.Frame(lf, bg=BG3); r.pack(fill="x", padx=8, pady=pady)
            tk.Label(r, text=lbl, bg=BG3, fg=FG, width=16, anchor="w").pack(side="left")
            fn(r); return r

        self.v_font = tk.StringVar(value=self.config["font_family"])
        def _font(p):
            families = sorted(set(tkfont.families()))
            cb = ttk.Combobox(p, textvariable=self.v_font, values=families, width=16)
            cb.pack(side="left")
            cb.bind("<<ComboboxSelected>>", lambda _: self._apply())
        row("Fonte:", _font)

        self.v_size = tk.IntVar(value=self.config["font_size"])
        def _size(p):
            tk.Scale(p, from_=12, to=120, orient="horizontal", variable=self.v_size,
                     bg=BG3, fg=FG, troughcolor=BG2, highlightthickness=0,
                     bd=0, sliderrelief="flat", sliderlength=16,
                     showvalue=True, command=lambda _: self._apply())\
                .pack(side="left", fill="x", expand=True)
        row("Tamanho:", _size)

        self.v_bold = tk.BooleanVar(value=self.config["font_bold"])
        def _bold(p):
            tk.Label(p, text="Negrito", bg=BG3, fg=FG, font=("Segoe UI", 9))\
                .pack(side="left", padx=(0, 8))
            ToggleSwitch(p, self.v_bold, command=self._apply, bg=BG3).pack(side="left")
        row("Estilo:", _bold)

        def _tcol(p):
            presets = ["#FFFFFF", "#000000", "#FFFF00", "#EF4444"]
            for color in presets:
                tk.Button(p, bg=color, width=2, relief="flat", bd=0,
                          cursor="hand2", command=lambda c=color: self._set_text_color(c))\
                    .pack(side="left", padx=1)
            self._btn_tc = tk.Button(p, bg=self._text_color, width=5, relief="flat",
                command=lambda: self._pick("text"))
            self._btn_tc.pack(side="left", padx=(8, 0))
        row("Cor do texto:", _tcol)

        self.v_transp = tk.BooleanVar(value=self.config["use_transparent_bg"])
        def _transp(p):
            tk.Label(p, text="Transparente", bg=BG3, fg=FG, font=("Segoe UI", 9))\
                .pack(side="left", padx=(0, 8))
            ToggleSwitch(p, self.v_transp, command=self._apply, bg=BG3).pack(side="left")
        row("Fundo:", _transp)

        def _bgcol(p):
            self._btn_bg = tk.Button(p, bg=self._bg_color, width=5, relief="flat",
                command=lambda: self._pick("bg"))
            self._btn_bg.pack(side="left")
        row("Cor do fundo:", _bgcol)

        self.v_opac = tk.DoubleVar(value=self.config["opacity"])
        def _opac(p):
            tk.Scale(p, from_=0.1, to=1.0, resolution=0.05, orient="horizontal",
                     variable=self.v_opac, bg=BG3, fg=FG, troughcolor=BG2,
                     highlightthickness=0, bd=0, sliderrelief="flat", sliderlength=16,
                     showvalue=True,
                     command=lambda _: self._apply()).pack(side="left", fill="x", expand=True)
        row("Opacidade:", _opac)

        self.v_pos = tk.StringVar(value=self.config["position"])
        pf = tk.Frame(lf, bg=BG3)
        pf.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(pf, text="Posição:", bg=BG3, fg=FG, anchor="w")\
            .pack(anchor="w", pady=(0, 4))
        pos_grid = tk.Frame(pf, bg=BG3)
        pos_grid.pack(fill="x")
        pos_options = [
            ("center",       "Centro"),
            ("top",          "Topo"),
            ("bottom",       "Rodapé"),
            ("top_left",     "Sup. esquerda"),
            ("top_right",    "Sup. direita"),
            ("bottom_left",  "Inf. esquerda"),
            ("bottom_right", "Inf. direita"),
            ("random",       "🎲 Aleatório (recomendado)"),
        ]
        for i, (val, txt) in enumerate(pos_options):
            tk.Radiobutton(pos_grid, text=txt, variable=self.v_pos, value=val,
                           bg=BG3, fg=FG, selectcolor=BG2, activebackground=BG3,
                           font=("Segoe UI", 8), command=self._apply)\
                .grid(row=i // 2, column=i % 2, sticky="w", padx=2, pady=1)
        tk.Label(pf, text="Aleatório nunca deixa a frase cortada na borda do monitor.",
                 bg=BG3, fg=DIM, font=("Segoe UI", 7), wraplength=280, justify="left")\
            .pack(anchor="w", pady=(4, 0))

        # Preview ao vivo
        rf = self._card(pane)
        rf.pack(side="left", fill="both", expand=True)
        tk.Label(rf, text="🔍 Preview ao vivo", bg=BG3, fg=ACC,
                 font=("Segoe UI", 10, "bold")).pack(pady=(8, 2))
        self._btn(rf, "⚡ Testar flash agora", self._test_flash, YELL, 9)\
            .pack(pady=(0, 6))
        self.prev_cv = tk.Canvas(rf, bg="#111122", highlightthickness=1,
                                  highlightbackground=BOR)
        self.prev_cv.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.prev_cv.bind("<Configure>", lambda _: self._draw_preview())
        self.root.after(300, self._draw_preview)

    def _test_flash(self):
        self._collect()
        text, image_path = "Mensagem Subliminar de Teste", None
        cat = self._cur_cat()
        sel = self.msg_lb.curselection() if cat else ()
        if cat and sel:
            msgs = self.config["library"][cat]["messages"]
            if sel[0] < len(msgs):
                text = msgs[sel[0]]["text"]
                image_path = msgs[sel[0]].get("image")
        # Destrói qualquer teste anterior ainda de pé antes de criar um novo,
        # senão cliques repetidos empilham overlays e mostram flashes duplicados.
        if self._test_overlay:
            self._test_overlay.destroy()
        self._test_overlay = Overlay(self.root, self.config, self.monitors)
        self._test_overlay.flash(text, image_path)
        self.root.after(int(self.config["display_time"]) + 400, self._test_overlay.destroy)

    def _set_text_color(self, color):
        self._text_color = color
        try: self._btn_tc.config(bg=color)
        except Exception: pass
        self._apply()

    def _pick(self, target):
        init = self._text_color if target == "text" else self._bg_color
        res = colorchooser.askcolor(color=init, title="Escolha a cor")
        if res and res[1]:
            color = res[1]
            if target == "text":
                self._text_color = color
                try: self._btn_tc.config(bg=color)
                except: pass
            else:
                self._bg_color = color
                try: self._btn_bg.config(bg=color)
                except: pass
            self._apply()

    def _draw_preview(self):
        c = self.prev_cv
        try:
            c.delete("all")
            cw, ch = c.winfo_width(), c.winfo_height()
            if cw < 20 or ch < 20: return
            bg = "#111122" if self.v_transp.get() else self._bg_color
            c.configure(bg=bg)
            fw = "bold" if self.v_bold.get() else "normal"
            scale = min(cw / 900, ch / 200)
            size = max(8, int(self.v_size.get() * scale * 0.65))
            font = (self.v_font.get(), size, fw)
            pos = self.v_pos.get()
            preview_pts = {
                "center": (0.5, 0.5), "top": (0.5, 0.12), "bottom": (0.5, 0.88),
                "top_left": (0.18, 0.14), "top_right": (0.82, 0.14),
                "bottom_left": (0.18, 0.86), "bottom_right": (0.82, 0.86),
                "random": (0.5, 0.5),
            }
            px, py = preview_pts.get(pos, (0.5, 0.5))
            x, y = cw * px, ch * py
            c.create_text(x + 2, y + 2, text="Mensagem Subliminar",
                          font=font, fill="#00000066", anchor="center")
            c.create_text(x, y, text="Mensagem Subliminar",
                          font=font, fill=self._text_color, anchor="center")
            c.create_text(cw // 2, ch - 14,
                          text=f"⚡ {self.v_disp.get()}ms   ↔ intervalo {self.v_intv.get()}ms",
                          font=("Segoe UI", 8), fill=DIM, anchor="center")
        except Exception:
            pass

    # ── Tab 4: Monitores ──────────────────────────────────────────────────────
    def _tab_monitors(self, f):
        tk.Label(f, text="Seleção de Monitor", bg=BG, fg=ACC,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(20, 10))

        mf = self._card(f); mf.pack(fill="x", padx=12, pady=6)
        self.v_mon_mode = tk.StringVar(value=self.config.get("monitor_mode", "primary"))
        for val, txt, desc in [
            ("primary", "🖥 Monitor principal",   "Exibe apenas no monitor principal"),
            ("all",     "🖥🖥 Todos os monitores", "Exibe em todos os monitores ao mesmo tempo"),
            ("select",  "☑ Selecionar",           "Escolha quais monitores usar"),
        ]:
            r = tk.Frame(mf, bg=BG3); r.pack(anchor="w", padx=12, pady=3)
            tk.Radiobutton(r, text=txt, variable=self.v_mon_mode, value=val,
                           bg=BG3, fg=FG, selectcolor=BG2, activebackground=BG3,
                           command=self._apply).pack(side="left")
            tk.Label(r, text=desc, bg=BG3, fg=DIM, font=("Segoe UI", 8)).pack(side="left", padx=6)
        tk.Frame(mf, height=8, bg=BG3).pack()

        # Diagrama
        df = self._card(f); df.pack(fill="both", expand=True, padx=12, pady=6)
        tk.Label(df, text="Diagrama — Monitores Detectados", bg=BG3, fg=DIM,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=8, pady=(8, 2))
        self.mon_cv = tk.Canvas(df, bg=BG3, height=180, highlightthickness=0)
        self.mon_cv.pack(fill="x", padx=8, pady=(0, 6))
        self.mon_cv.bind("<Configure>", lambda _: self._draw_monitors())

        self._btn(f, "🔄 Redetectar monitores", self._redetect_monitors, ACC2, 8)\
            .pack(pady=6)

        self.root.after(400, self._draw_monitors)

    def _draw_monitors(self):
        c = self.mon_cv; c.delete("all")
        c.update_idletasks()
        cw = max(c.winfo_width(), 300); ch = 170
        if not self.monitors: return
        min_x = min(m["x"] for m in self.monitors)
        min_y = min(m["y"] for m in self.monitors)
        rng_x = max(m["x"] + m["w"] for m in self.monitors) - min_x or 1
        rng_y = max(m["y"] + m["h"] for m in self.monitors) - min_y or 1
        pad = 24
        scale = min((cw - pad*2) / rng_x, (ch - pad*2) / rng_y) * 0.85
        sel = self.config.get("selected_monitors", [0])
        for i, m in enumerate(self.monitors):
            rx = pad + (m["x"] - min_x) * scale
            ry = pad + (m["y"] - min_y) * scale
            rw = m["w"] * scale; rh = m["h"] * scale
            col = ACC if m.get("primary") else ACC2
            if i in sel and self.v_mon_mode.get() == "select":
                col = GREEN
            c.create_rectangle(rx, ry, rx+rw, ry+rh, fill=BG2, outline=col, width=2)
            name = f"Monitor {i+1}" + (" ★" if m.get("primary") else "")
            c.create_text(rx+rw/2, ry+rh/2-8, text=name, font=("Segoe UI", 8, "bold"),
                          fill=FG, anchor="center")
            c.create_text(rx+rw/2, ry+rh/2+8, text=f"{m['w']}×{m['h']}",
                          font=("Segoe UI", 7), fill=DIM, anchor="center")

    def _redetect_monitors(self):
        self.monitors = get_monitors(self.root)
        self._draw_monitors()
        detalhes = "\n".join(
            f"#{i+1}: {m['w']}x{m['h']} em ({m['x']},{m['y']})" + (" — principal" if m.get("primary") else "")
            for i, m in enumerate(self.monitors))
        messagebox.showinfo("Monitores",
            f"{len(self.monitors)} monitor(es) detectado(s).\n\n{detalhes}")

    # ── Tab 5: Estatísticas ───────────────────────────────────────────────────
    def _tab_stats(self, f):
        tk.Label(f, text="Painel de Estatísticas", bg=BG, fg=ACC,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(20, 8))

        # Filtro de período
        ff = tk.Frame(f, bg=BG); ff.pack(fill="x", padx=12, pady=4)
        tk.Label(ff, text="Período:", bg=BG, fg=FG).pack(side="left", padx=(0, 6))
        self.v_period = tk.StringVar(value="week")
        for val, txt in [("today","Hoje"),("week","7 dias"),("month","30 dias"),("all","Tudo")]:
            tk.Radiobutton(ff, text=txt, variable=self.v_period, value=val,
                           bg=BG, fg=FG, selectcolor=BG2, activebackground=BG,
                           command=self._refresh_stats).pack(side="left", padx=4)
        self._btn(ff, "🔄", self._refresh_stats, ACC2, 8).pack(side="right")
        self._btn(ff, "⬇ Exportar CSV", self._export_stats, GREEN, 8).pack(side="right", padx=4)

        # Cards de resumo
        cf = tk.Frame(f, bg=BG); cf.pack(fill="x", padx=12, pady=4)
        self._stat_lbls = {}
        for key, title in [("total","Total de Flashes"),("today","Hoje"),("top","Categoria Top")]:
            card = tk.Frame(cf, bg=BG3, padx=12, pady=8)
            card.pack(side="left", fill="both", expand=True, padx=4)
            tk.Label(card, text=title, bg=BG3, fg=DIM, font=("Segoe UI", 8)).pack()
            lbl = tk.Label(card, text="—", bg=BG3, fg=ACC, font=("Segoe UI", 20, "bold"))
            lbl.pack()
            self._stat_lbls[key] = lbl

        # Gráficos
        gf = tk.Frame(f, bg=BG); gf.pack(fill="both", expand=True, padx=12, pady=4)

        lc = self._card(gf); lc.pack(side="left", fill="both", expand=True, padx=(0, 4))
        tk.Label(lc, text="Por categoria", bg=BG3, fg=ACC,
                 font=("Segoe UI", 9, "bold")).pack(pady=(6, 2))
        self.cv_cat = tk.Canvas(lc, bg=BG3, highlightthickness=0)
        self.cv_cat.pack(fill="both", expand=True, padx=4, pady=(0, 6))

        rc = self._card(gf); rc.pack(side="left", fill="both", expand=True, padx=(4, 0))
        tk.Label(rc, text="Linha do tempo", bg=BG3, fg=ACC,
                 font=("Segoe UI", 9, "bold")).pack(pady=(6, 2))
        self.cv_line = tk.Canvas(rc, bg=BG3, highlightthickness=0)
        self.cv_line.pack(fill="both", expand=True, padx=4, pady=(0, 6))

        # Top mensagens
        tf = self._card(f); tf.pack(fill="x", padx=12, pady=(0, 8))
        tk.Label(tf, text="Top 5 Mensagens", bg=BG3, fg=ACC,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=8, pady=(6, 2))
        self.top_f = tk.Frame(tf, bg=BG3)
        self.top_f.pack(fill="x", padx=8, pady=(0, 6))

        f.after(600, self._refresh_stats)

    def _export_stats(self):
        rows = self.db.all_rows(self.v_period.get())
        if not rows:
            messagebox.showinfo("Exportar CSV", "Nenhum dado para exportar neste período.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")],
            initialfile="subliminal_stats.csv", title="Exportar estatísticas")
        if not path: return
        with open(path, "w", newline="", encoding="utf-8") as fp:
            w = csv.writer(fp)
            w.writerow(["data_hora", "mensagem", "categoria"])
            w.writerows(rows)
        messagebox.showinfo("Exportar CSV", f"{len(rows)} registros exportados para:\n{path}")

    def _refresh_stats(self):
        p = self.v_period.get()
        total = self.db.total(p)
        today = self.db.total("today")
        cats  = self.db.by_category(p)
        top_cat = cats[0][0][:16] if cats else "—"

        self._stat_lbls["total"].config(text=str(total))
        self._stat_lbls["today"].config(text=str(today))
        self._stat_lbls["top"].config(text=top_cat)

        self._draw_cat_chart(cats)
        self._draw_timeline(self.db.timeline(p))

        for w in self.top_f.winfo_children(): w.destroy()
        top = self.db.top_messages(p, 5)
        if not top:
            tk.Label(self.top_f, text="Nenhum dado registrado ainda.",
                     bg=BG3, fg=DIM).pack()
        COLORS = [ACC, ACC2, GREEN, YELL, RED]
        for i, (msg, cat, cnt) in enumerate(top):
            row = tk.Frame(self.top_f, bg=BG2 if i%2==0 else BG3)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=f"#{i+1}", bg=row["bg"], fg=COLORS[i],
                     font=("Segoe UI", 8, "bold"), width=3).pack(side="left", padx=4)
            tk.Label(row, text=msg[:50], bg=row["bg"], fg=FG,
                     font=("Segoe UI", 8)).pack(side="left", fill="x", expand=True)
            tk.Label(row, text=f"{cnt}×", bg=row["bg"], fg=GREEN,
                     font=("Segoe UI", 8, "bold"), width=5).pack(side="right", padx=6)

    def _draw_cat_chart(self, data):
        c = self.cv_cat; c.delete("all")
        c.update_idletasks()
        cw = max(c.winfo_width(), 160); ch = max(c.winfo_height(), 80)
        if not data: return
        max_v = max(v for _, v in data) or 1
        COLS  = [ACC, ACC2, GREEN, YELL, RED, "#ec4899", "#f97316"]
        bar_h = max(12, (ch - 24) // min(len(data), 8) - 4)
        for i, (cat, cnt) in enumerate(data[:8]):
            y = 10 + i * (bar_h + 5)
            bw = int((cnt / max_v) * (cw - 90))
            color = COLS[i % len(COLS)]
            c.create_rectangle(4, y, 4 + bw, y + bar_h, fill=color, outline="")
            name = cat[:16]
            c.create_text(cw - 4, y + bar_h // 2,
                          text=f"{name} ({cnt})", font=("Segoe UI", 7),
                          fill=FG, anchor="e")

    def _draw_timeline(self, data):
        c = self.cv_line; c.delete("all")
        c.update_idletasks()
        cw = max(c.winfo_width(), 160); ch = max(c.winfo_height(), 80)
        if not data or len(data) < 2:
            c.create_text(cw//2, ch//2, text="Dados insuficientes",
                          fill=DIM, font=("Segoe UI", 9))
            return
        pad = 18
        vals = [v for _, v in data]
        max_v = max(vals) or 1
        n = len(vals)
        step = (cw - pad*2) / max(n - 1, 1)
        for i in range(3):
            gy = pad + (ch - pad*2) * i // 2
            c.create_line(pad, gy, cw - pad, gy, fill=BOR, dash=(2, 4))
        pts = [(pad + i * step, ch - pad - (v / max_v) * (ch - pad*2))
               for i, v in enumerate(vals)]
        # Fill area
        area = [pad, ch - pad]
        for x, y in pts: area += [x, y]
        area += [pts[-1][0], ch - pad]
        c.create_polygon(area, fill=ACC + "33", outline="")
        for i in range(len(pts) - 1):
            c.create_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1],
                          fill=ACC, width=2)
        for x, y in pts:
            c.create_oval(x-3, y-3, x+3, y+3, fill=ACC, outline="")
        c.create_text(cw - pad, pad, text=str(max_v),
                      fill=DIM, font=("Segoe UI", 7), anchor="ne")

    # ── Tab 6: Metas ──────────────────────────────────────────────────────────
    def _tab_goals(self, f):
        tk.Label(f, text="Minhas Metas", bg=BG, fg=ACC,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(20, 8))
        tk.Label(f,
                 text="Metas ativas são incluídas automaticamente como mensagens subliminares.",
                 bg=BG, fg=DIM, font=("Segoe UI", 9, "italic"))\
            .pack(anchor="w", padx=14, pady=(0, 4))

        self.goal_summary = tk.Label(f, text="", bg=BG, fg=GREEN,
                                      font=("Segoe UI", 9, "bold"))
        self.goal_summary.pack(anchor="w", padx=14)

        # Scroll area
        gf = self._card(f); gf.pack(fill="both", expand=True, padx=12, pady=6)
        sb = tk.Scrollbar(gf); sb.pack(side="right", fill="y")
        self.goal_cv = tk.Canvas(gf, bg=BG3, yscrollcommand=sb.set,
                                  highlightthickness=0)
        self.goal_cv.pack(fill="both", expand=True)
        sb.config(command=self.goal_cv.yview)
        self.goal_inner = tk.Frame(self.goal_cv, bg=BG3)
        self.goal_cv.create_window((0, 0), window=self.goal_inner, anchor="nw")
        self.goal_inner.bind("<Configure>",
            lambda e: self.goal_cv.configure(scrollregion=self.goal_cv.bbox("all")))

        # Entrada
        af = tk.Frame(f, bg=BG); af.pack(fill="x", padx=12, pady=4)
        self.goal_ent = tk.Entry(af, bg=BG2, fg=FG, insertbackground=FG,
                                  font=("Segoe UI", 10), relief="flat")
        self.goal_ent.pack(side="left", fill="x", expand=True, ipady=5)
        self.goal_ent.insert(0, "Descreva sua meta aqui...")
        self.goal_ent.bind("<FocusIn>", lambda e: self.goal_ent.delete(0, "end")
                           if "Descreva" in self.goal_ent.get() else None)
        self.goal_ent.bind("<Return>", lambda _: self._add_goal())

        self._btn(af, "➕ Adicionar", self._add_goal, GREEN).pack(side="left", padx=6)
        self._btn(af, "🗑 Limpar concluídas",
                  self._clear_done_goals, DIM, 8).pack(side="left")

        self._refresh_goals()

    def _refresh_goals(self):
        for w in self.goal_inner.winfo_children(): w.destroy()
        goals = self.config.get("goals", [])
        done  = sum(1 for g in goals if g.get("done"))
        self.goal_summary.config(
            text=f"✅ {done}/{len(goals)} concluídas" if goals else "Nenhuma meta ainda.")
        for i, g in enumerate(goals):
            self._goal_row(i, g)

    def _goal_row(self, idx, goal):
        bg = BG2 if idx % 2 == 0 else BG3
        row = tk.Frame(self.goal_inner, bg=bg, pady=5)
        row.pack(fill="x", padx=4, pady=2)

        var = tk.BooleanVar(value=goal.get("done", False))
        def toggle(i=idx, v=var):
            self.config["goals"][i]["done"] = v.get()
            self._refresh_goals()
        ToggleSwitch(row, var, command=toggle, bg=bg).pack(side="left", padx=6)

        done  = goal.get("done", False)
        color = DIM if done else FG
        font  = ("Segoe UI", 10, "overstrike") if done else ("Segoe UI", 10)
        tk.Label(row, text=goal.get("text", ""), bg=bg, fg=color,
                 font=font, anchor="w").pack(side="left", fill="x", expand=True)

        tk.Button(row, text="✕", command=lambda i=idx: self._remove_goal(i),
                  bg=bg, fg=DIM, relief="flat", bd=0, cursor="hand2",
                  font=("Segoe UI", 9, "bold"), activebackground=bg, activeforeground=RED)\
            .pack(side="right", padx=6)

        if goal.get("priority") == "alta":
            tk.Label(row, text="🔥", bg=bg, fg=RED).pack(side="right", padx=4)

    def _remove_goal(self, idx):
        goals = self.config.get("goals", [])
        if 0 <= idx < len(goals):
            del goals[idx]
            self._refresh_goals()

    def _add_goal(self):
        text = self.goal_ent.get().strip()
        if not text or "Descreva" in text: return
        prio = messagebox.askquestion("Prioridade", "Meta de alta prioridade?")
        self.config["goals"].append({
            "text": text, "done": False,
            "created": datetime.now().isoformat(),
            "priority": "alta" if prio == "yes" else "normal"
        })
        self.goal_ent.delete(0, "end")
        self._refresh_goals()

    def _clear_done_goals(self):
        self.config["goals"] = [g for g in self.config.get("goals", [])
                                 if not g.get("done")]
        self._refresh_goals()

    def _get_goal_messages(self):
        return [(f"🎯 {g['text']}", "🎯 Metas")
                for g in self.config.get("goals", []) if not g.get("done")]

    # ── Barra inferior ────────────────────────────────────────────────────────
    def _build_bar(self):
        bar = tk.Frame(self.root, bg="#08080f", pady=5)
        bar.pack(side="bottom", fill="x")
        self.lbl_status = tk.Label(bar, text="⏸ Parado", bg="#08080f",
                                    fg=RED, font=("Segoe UI", 10, "bold"))
        self.lbl_status.pack(side="left", padx=14)
        self.lbl_count  = tk.Label(bar, text="0 flashes", bg="#08080f",
                                    fg=DIM, font=("Segoe UI", 9))
        self.lbl_count.pack(side="left", padx=20)
        # Atalhos globais
        self.lbl_hotkeys = tk.Label(bar, text=self._hotkey_hint(),
                 bg="#08080f", fg="#444466", font=("Segoe UI", 7))
        self.lbl_hotkeys.pack(side="left", padx=10)
        self.lbl_last = tk.Label(bar, text="", bg="#08080f", fg="#8888aa",
                                  font=("Segoe UI", 8))
        self.lbl_last.pack(side="left", padx=10)
        self._btn(bar, "💾 Salvar", self._save_cfg, ACC2, 9).pack(side="right", padx=6)
        self.btn_tog = self._btn(bar, "▶  Iniciar", self._toggle, GREEN, 10)
        self.btn_tog.pack(side="right", padx=8)

    # ── Lógica principal ──────────────────────────────────────────────────────
    def _hotkey_hint(self):
        p = self.config.get("hotkey_pause", "P")
        s = self.config.get("hotkey_stop", "S")
        return f"Ctrl+Shift+{p}: pausar | Ctrl+Shift+{s}: parar"

    def _apply(self):
        self._collect()
        if self.overlay:
            self.overlay.rebuild(self.config, self.monitors)
        try: self._draw_preview()
        except: pass
        try: self.lbl_hotkeys.config(text=self._hotkey_hint())
        except Exception: pass

    def _toggle(self):
        if self.running: self._stop()
        else: self._start()

    def _pool(self):
        items, weights = [], []
        for cat, data in self.config.get("library", {}).items():
            if not data.get("active", True): continue
            cw = data.get("weight", 10)
            for m in data.get("messages", []):
                items.append((m["text"], cat, m.get("image")))
                weights.append(cw * m.get("weight", 10))
        for txt, cat in self._get_goal_messages():
            items.append((txt, cat, None)); weights.append(80)
        return items, weights

    def _start(self):
        self._collect()
        items, weights = self._pool()
        if not items:
            messagebox.showwarning("Aviso", "Nenhuma mensagem ativa! Ative categorias.")
            return
        active_cats = [cat for cat, data in self.config.get("library", {}).items()
                       if data.get("active", True) and data.get("messages")]
        if active_cats:
            messagebox.showinfo("Categorias ativas",
                "As frases dessas categorias vão entrar no rodízio:\n\n"
                + "\n".join(f"• {c}" for c in active_cats))
        self.running = True
        self._stop_evt = threading.Event()
        self.overlay = Overlay(self.root, self.config, self.monitors)
        self.btn_tog.config(text="⏹  Parar", bg=RED)
        self.lbl_status.config(text="▶ Rodando", fg=GREEN)
        threading.Thread(target=self._loop, args=(self._stop_evt,), daemon=True).start()

    def _stop(self):
        self.running = False
        self._stop_evt.set()
        if self.overlay:
            self.root.after(0, self.overlay.destroy)
            self.overlay = None
        self.btn_tog.config(text="▶  Iniciar", bg=GREEN)
        self.lbl_status.config(text="⏸ Parado", fg=RED)
        self.tray.tip("Subliminal Pro — Parado")

    def _in_schedule(self):
        if not self.config.get("schedule_enabled"): return True
        try:
            start = datetime.strptime(self.config.get("schedule_start", "09:00"), "%H:%M").time()
            end   = datetime.strptime(self.config.get("schedule_end", "18:00"), "%H:%M").time()
        except ValueError:
            return True
        now = datetime.now().time()
        if start <= end:
            return start <= now <= end
        return now >= start or now <= end  # faixa que cruza a meia-noite

    def _should_pause(self):
        if not self._in_schedule():
            return True
        now = time.time()
        if now - self._last_proc > 10:
            self._last_proc = now
            pause = False
            if self.config.get("auto_pause_loom")    and is_loom_active():    pause = True
            if self.config.get("auto_pause_meeting") and is_meeting_active(): pause = True
            self._proc_pause = pause
        if self.config.get("auto_pause_ps") and is_printscreen():
            return True
        return self._proc_pause

    def _loop(self, stop_evt):
        # Recebe o próprio evento de parada como argumento (em vez de ler
        # self._stop_evt) de propósito: se o usuário parar e iniciar rápido
        # demais, um novo Event() é criado a cada _start(). Assim, uma thread
        # antiga que ainda não notou o sinal de parada nunca é "ressuscitada"
        # por um clear() feito pra uma execução mais nova — ela só observa o
        # Event que era o atual quando ELA foi criada.
        order = self.config.get("order", "random")
        seq_idx = 0
        while not stop_evt.is_set():
            items, weights = self._pool()
            if items and not self._should_pause():
                if order == "weighted_random":
                    msg, cat, img = random.choices(items, weights=weights)[0]
                elif order == "random":
                    msg, cat, img = random.choice(items)
                else:
                    msg, cat, img = items[seq_idx % len(items)]
                    seq_idx += 1
                self.root.after(0, lambda m=msg, c=cat, i=img: self._fire(m, c, i))
            stop_evt.wait(self.config["interval"] / 1000)

    def _fire(self, msg, cat, image_path=None):
        if not self.running or not self.overlay: return
        self.overlay.flash(msg, image_path)
        self.db.log(msg, cat)
        self._flash_cnt += 1
        self.lbl_count.config(text=f"{self._flash_cnt} flashes")
        self.lbl_last.config(text=f"Última: [{cat}] {msg[:40]}" + (" 🖼" if image_path else ""))

    def _hide_to_tray(self):
        """Chamado ao clicar no X da janela. Só esconde na bandeja; para
        encerrar de fato, use "Sair" no menu da bandeja."""
        if HAS_TRAY and self.tray.icon:
            self.root.withdraw()
            self.tray.tip("Subliminal Pro — minimizado na bandeja")
        else:
            # Sem bandeja disponível, não há como reabrir a janela depois
            # de escondida — nesse caso o X precisa encerrar o app mesmo.
            self.on_close()

    def _on_minimize(self, event):
        """Intercepta o minimizar da barra de título e some da barra de
        tarefas também, deixando só o ícone na bandeja."""
        if event.widget is self.root and self.root.state() == "iconic" \
                and HAS_TRAY and self.tray.icon:
            self.root.withdraw()

    def on_close(self):
        self._stop()
        self._save_cfg()
        self.db.close()
        self.tray.stop()
        try:
            unregister_global_hotkeys()
        except:
            pass
        self.root.destroy()

# ── Trava de instância única ──────────────────────────────────────────────────
# Como minimizar/fechar agora só esconde na bandeja, é fácil acumular
# instâncias escondidas sem perceber (cada uma rodando seu próprio sorteio de
# mensagens). Este mutex nomeado do Windows garante que só uma rode por vez.
_ERROR_ALREADY_EXISTS = 183

def _acquire_single_instance_lock():
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "SubliminalProSingleInstanceMutex")
    if ctypes.windll.kernel32.GetLastError() == _ERROR_ALREADY_EXISTS:
        return None
    return mutex

# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    _lock = _acquire_single_instance_lock()
    if _lock is None:
        tmp = tk.Tk(); tmp.withdraw()
        messagebox.showinfo("Subliminal Pro",
            "O Subliminal Pro já está rodando.\nConfira o ícone dele na bandeja do sistema.")
        tmp.destroy()
        return

    root = tk.Tk()
    root.configure(bg=BG)
    root.minsize(760, 640)
    try:
        root.state("zoomed")  # abre maximizada dentro da área útil da tela
    except Exception:
        pass                  # se o WM não suportar "zoomed", mantém o tamanho padrão
    app = App(root)  # já registra seu próprio protocolo de fechar (esconde na bandeja)
    root.mainloop()

if __name__ == "__main__":
    main()
