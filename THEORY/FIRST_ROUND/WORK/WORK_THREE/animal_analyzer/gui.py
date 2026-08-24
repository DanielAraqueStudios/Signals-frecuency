"""customtkinter desktop GUI for the animal-sound spectral study (item 8).

Loads up to three category recordings (Gato/Perro/Gallo), analyzes each
one's first `ANALYSIS_WINDOW_S` seconds (waveform, FFT, mean, std) via
`animal_analyzer.core`, and reports a pairwise statistical-separability
summary across whichever categories have been analyzed.
"""

from __future__ import annotations

from tkinter import filedialog, messagebox

import customtkinter as ctk
import matplotlib

matplotlib.use("TkAgg")

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .core import ANALYSIS_WINDOW_S, analyze_audio, compare_categories, load_audio

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CATEGORIES = ["Gato", "Perro", "Gallo"]
EMOJIS = {"Gato": "🐱", "Perro": "🐶", "Gallo": "🐓"}

BG = "#101216"
PANEL = "#181B21"
PANEL2 = "#20242C"
TEXT = "#F5F5F5"
TEXT_SECONDARY = "#A9AFBA"
SUCCESS = "#22C55E"


class AnalizadorAnimales(ctk.CTk):
    """Main window: per-category loading, analysis, and a summary tab."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Analizador Espectral de Sonidos - Gato | Perro | Gallo")
        self.geometry("1450x900")
        self.minsize(1200, 750)
        self.configure(fg_color=BG)

        # category -> {"path", "signal", "fs", "result", widgets...}
        self.audios: dict[str, dict] = {name: {"path": None, "signal": None, "fs": None, "result": None} for name in CATEGORIES}

        self._build_ui()

    # ------------------------------------------------------------------
    # UI assembly
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self._build_header()

        main = ctk.CTkFrame(self, fg_color=BG)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        self._build_controls(main)

        self.tabs = ctk.CTkTabview(main, corner_radius=15, fg_color=PANEL)
        self.tabs.pack(fill="both", expand=True)

        for name in CATEGORIES:
            self.tabs.add(f"{EMOJIS[name]} {name}")
            self._build_category_tab(name)

        self.tabs.add("📊 Resumen")
        self._build_summary_tab()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="ANALIZADOR ESPECTRAL DE SONIDOS",
            font=ctk.CTkFont(family="Arial", size=28, weight="bold"),
            text_color=TEXT,
        ).pack(pady=(20, 2))

        ctk.CTkLabel(
            header,
            text=(
                "Media, desviación estándar y FFT sobre los primeros "
                f"{ANALYSIS_WINDOW_S:.0f} s de cada grabación"
            ),
            font=ctk.CTkFont(family="Arial", size=14),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(0, 20))

    def _build_controls(self, parent: ctk.CTkFrame) -> None:
        control = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=15)
        control.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            control, text="🎧 CARGA DE AUDIOS", font=ctk.CTkFont(size=17, weight="bold"), text_color=TEXT
        ).pack(anchor="w", padx=20, pady=(15, 10))

        botones = ctk.CTkFrame(control, fg_color="transparent")
        botones.pack(fill="x", padx=20, pady=(0, 15))

        for name in CATEGORIES:
            ctk.CTkButton(
                botones,
                text=f"{EMOJIS[name]}  Cargar {name}",
                height=40,
                corner_radius=10,
                command=lambda n=name: self.cargar_audio(n),
            ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            botones,
            text="⚡  Analizar Audios",
            height=40,
            corner_radius=10,
            fg_color=SUCCESS,
            hover_color="#16A34A",
            text_color="white",
            font=ctk.CTkFont(weight="bold"),
            command=self.analizar_todos,
        ).pack(side="right", padx=10)

    def _build_category_tab(self, name: str) -> None:
        tab = self.tabs.tab(f"{EMOJIS[name]} {name}")

        info = ctk.CTkFrame(tab, fg_color=PANEL2, corner_radius=12)
        info.pack(fill="x", padx=15, pady=15)

        self.audios[name]["info_label"] = ctk.CTkLabel(
            info,
            text=f"{EMOJIS[name]} {name}: no se ha cargado ningún audio.",
            font=ctk.CTkFont(size=14),
            text_color=TEXT_SECONDARY,
        )
        self.audios[name]["info_label"].pack(side="left", padx=15, pady=12)

        self.audios[name]["stats_label"] = ctk.CTkLabel(
            info,
            text="Dominante: -- Hz   |   media: --   |   std: --",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=SUCCESS,
        )
        self.audios[name]["stats_label"].pack(side="right", padx=15)

        frame_grafica = ctk.CTkFrame(tab, fg_color=PANEL2, corner_radius=12)
        frame_grafica.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        figura = Figure(figsize=(12, 8), dpi=100, facecolor=PANEL2)
        ax1 = figura.add_subplot(211)
        ax2 = figura.add_subplot(212)
        for ax in (ax1, ax2):
            self._style_axes(ax)

        ax1.set_title(f"Señal (primeros {ANALYSIS_WINDOW_S:.0f} s)", color="white", fontsize=12, fontweight="bold")
        ax1.set_xlabel("Tiempo [s]", color="white")
        ax1.set_ylabel("Amplitud", color="white")

        ax2.set_title("FFT", color="white", fontsize=12, fontweight="bold")
        ax2.set_xlabel("Frecuencia [Hz]", color="white")
        ax2.set_ylabel("Magnitud", color="white")

        figura.tight_layout()

        canvas = FigureCanvasTkAgg(figura, master=frame_grafica)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        self.audios[name].update(figura=figura, canvas=canvas, ax1=ax1, ax2=ax2)

    def _build_summary_tab(self) -> None:
        tab = self.tabs.tab("📊 Resumen")
        self.summary_text = ctk.CTkTextbox(tab, fg_color=PANEL2, text_color=TEXT, font=ctk.CTkFont(family="Consolas", size=13))
        self.summary_text.pack(fill="both", expand=True, padx=15, pady=15)
        self.summary_text.insert(
            "1.0",
            "Carga y analiza al menos dos categorías para ver aquí el resumen "
            "comparativo (media, desviación estándar, frecuencia dominante y "
            "separabilidad estadística estimada).",
        )
        self.summary_text.configure(state="disabled")

    @staticmethod
    def _style_axes(ax) -> None:
        ax.set_facecolor("#14171C")
        ax.tick_params(colors="white", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#3A3F48")
        ax.grid(True, alpha=0.15)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def cargar_audio(self, name: str) -> None:
        path = filedialog.askopenfilename(
            title=f"Seleccionar audio del {name}",
            filetypes=[
                ("Archivos de audio", "*.wav *.mp3 *.flac *.ogg *.m4a"),
                ("WAV", "*.wav"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not path:
            return

        try:
            signal, fs = load_audio(path)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user via dialog
            messagebox.showerror("Error", f"No se pudo cargar el audio:\n\n{exc}")
            return

        entry = self.audios[name]
        entry["path"], entry["signal"], entry["fs"] = path, signal, fs
        duration = len(signal) / fs
        entry["info_label"].configure(
            text=f"{EMOJIS[name]} {path.split('/')[-1]}   |   Fs = {fs} Hz   |   Duración total = {duration:.2f} s",
            text_color=TEXT,
        )

    def analizar_todos(self) -> None:
        analyzed = [name for name in CATEGORIES if self.audios[name]["signal"] is not None]
        if not analyzed:
            messagebox.showwarning("Sin audios", "Primero debes cargar al menos un audio.")
            return

        for name in analyzed:
            self._procesar_audio(name)

        self._actualizar_resumen(analyzed)
        messagebox.showinfo("Análisis terminado", f"Se analizaron {len(analyzed)} audio(s) correctamente.")

    def _procesar_audio(self, name: str) -> None:
        entry = self.audios[name]
        result = analyze_audio(entry["signal"], entry["fs"])
        entry["result"] = result

        windowed = result["windowed_signal"]
        t = [i / result["sample_rate"] for i in range(len(windowed))]
        limit = min(10_000, result["sample_rate"] / 2)
        mask = result["frequencies"] <= limit

        ax1, ax2 = entry["ax1"], entry["ax2"]
        ax1.clear()
        ax2.clear()
        self._style_axes(ax1)
        self._style_axes(ax2)

        ax1.plot(t, windowed, linewidth=0.8)
        ax1.set_title(f"Señal (primeros {ANALYSIS_WINDOW_S:.0f} s)", color="white", fontsize=12, fontweight="bold")
        ax1.set_xlabel("Tiempo [s]", color="white")
        ax1.set_ylabel("Amplitud", color="white")

        ax2.plot(result["frequencies"][mask], result["magnitude"][mask], linewidth=1)
        ax2.axvline(result["dominant_frequency_hz"], linestyle="--", linewidth=1.5, label=f"Dominante: {result['dominant_frequency_hz']:.1f} Hz")
        ax2.set_title("FFT", color="white", fontsize=12, fontweight="bold")
        ax2.set_xlabel("Frecuencia [Hz]", color="white")
        ax2.set_ylabel("Magnitud", color="white")
        ax2.legend(facecolor=PANEL2, labelcolor="white")

        entry["stats_label"].configure(
            text=(
                f"Dominante: {result['dominant_frequency_hz']:.2f} Hz   |   "
                f"media: {result['mean']:.4f}   |   std: {result['std']:.4f}"
            )
        )

        entry["figura"].tight_layout()
        entry["canvas"].draw()

    def _actualizar_resumen(self, analyzed: list[str]) -> None:
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")

        if len(analyzed) < 2:
            self.summary_text.insert("1.0", "Carga y analiza al menos dos categorías para calcular separabilidad.")
        else:
            results = {name: self.audios[name]["result"] for name in analyzed}
            self.summary_text.insert("1.0", compare_categories(results))

        self.summary_text.configure(state="disabled")


def main() -> None:
    """Launch the animal-sound analyzer window."""
    app = AnalizadorAnimales()
    app.mainloop()
