import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ftplib
import threading
import os
import time

# ─── Configurações ───────────────────────────────────────────────────────────
FTP_HOST = "ftp2.datasus.gov.br"
FTP_BASE = "/pub/sistemas/tup/downloads/"


ARQUIVOS = [
    {
        "nome": "SIGTAP Setup (.jar)",
        "arquivo": "sigtap-setup-1.4.1703301403.jar",
        "descricao": "Para máquinas com Java instalado",
        "tamanho_est": "23 MB"
    },
    {
        "nome": "SIGTAP Setup + Java (.exe)",
        "arquivo": "sigtap-setup-com-java-1.4.1703301403.exe",
        "descricao": "Para máquinas Windows sem Java",
        "tamanho_est": "37 MB"
    },
    {
        "nome": "SIGTAP Setup Windows (.exe)",
        "arquivo": "sigtap-setup-1.4.1703301403.exe",
        "descricao": "Para máquinas Windows com Java instalado",
        "tamanho_est": "23 MB"
    },
    {
        "nome": "Competência - 03/2026 (.zip)",
        "arquivo": "TabelaUnificada_202603_v2603111027.zip",
        "descricao": "Para máquinas Windows com Java instalado",
        "tamanho_est": "4 gb"
    },
]

# ─── Aplicação ────────────────────────────────────────────────────────────────
class SigtapDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("SIGTAP Downloader")
        self.root.geometry("620x620")
        self.root.resizable(True, True)
        self.root.minsize(620, 580)
        self.root.configure(bg="#0d1b2a")

        self.pasta_destino = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.selecionados = []
        self.cancelar = False
        self.ftp = None

        self._build_ui()

    def _build_ui(self):
        # ── Título ──
        header = tk.Frame(self.root, bg="#0d1b2a")
        header.pack(fill="x", padx=24, pady=(10, 0))

        tk.Label(header, text="SIGTAP", font=("Courier New", 28, "bold"),
                 fg="#00d4ff", bg="#0d1b2a").pack(anchor="w")
        tk.Label(header, text="Downloader de Tabelas do SUS",
                 font=("Courier New", 11), fg="#4a7fa5", bg="#0d1b2a").pack(anchor="w")

        sep = tk.Frame(self.root, bg="#00d4ff", height=1)
        sep.pack(fill="x", padx=24, pady=12)

        # ── Pasta destino ──
        pasta_frame = tk.Frame(self.root, bg="#0d1b2a")
        pasta_frame.pack(fill="x", padx=24, pady=(0, 16))

        tk.Label(pasta_frame, text="📁  Pasta de destino:", font=("Courier New", 10),
                 fg="#8ab4d4", bg="#0d1b2a").pack(anchor="w")

        row = tk.Frame(pasta_frame, bg="#0d1b2a")
        row.pack(fill="x", pady=4)

        self.entry_pasta = tk.Entry(row, textvariable=self.pasta_destino,
                                    font=("Courier New", 10), bg="#132435",
                                    fg="#e0f0ff", insertbackground="#00d4ff",
                                    relief="flat", bd=6)
        self.entry_pasta.pack(side="left", fill="x", expand=True)

        tk.Button(row, text="Alterar", font=("Courier New", 9, "bold"),
                  bg="#00d4ff", fg="#0d1b2a", relief="flat", cursor="hand2",
                  command=self._escolher_pasta, padx=10).pack(side="left", padx=(8, 0))

        # ── Lista de arquivos ──
        tk.Label(self.root, text="Selecione os arquivos para baixar:",
                 font=("Courier New", 10), fg="#8ab4d4", bg="#0d1b2a").pack(anchor="w", padx=24)

        self.checks = []
        self.vars = []
        for arq in ARQUIVOS:
            var = tk.BooleanVar(value=True)
            self.vars.append(var)

            card = tk.Frame(self.root, bg="#132435", pady=6, padx=14,
                            highlightbackground="#1e3a52", highlightthickness=1)
            card.pack(fill="x", padx=24, pady=3)

            top = tk.Frame(card, bg="#132435")
            top.pack(fill="x")

            cb = tk.Checkbutton(top, variable=var, bg="#132435",
                                activebackground="#132435", selectcolor="#0d1b2a",
                                fg="#00d4ff", cursor="hand2")
            cb.pack(side="left")
            self.checks.append(cb)

            tk.Label(top, text=arq["nome"], font=("Courier New", 11, "bold"),
                     fg="#e0f0ff", bg="#132435").pack(side="left")

            tk.Label(top, text=f"  [{arq['tamanho_est']}]",
                     font=("Courier New", 9), fg="#4a7fa5", bg="#132435").pack(side="left")

            tk.Label(card, text=arq["descricao"], font=("Courier New", 9),
                     fg="#4a7fa5", bg="#132435").pack(anchor="w", padx=22)

        # ── Barra de progresso ──
        prog_frame = tk.Frame(self.root, bg="#0d1b2a")
        prog_frame.pack(fill="x", padx=24, pady=(10, 4))

        self.label_status = tk.Label(prog_frame, text="Aguardando...",
                                      font=("Courier New", 9), fg="#4a7fa5", bg="#0d1b2a")
        self.label_status.pack(anchor="w")

        self.progressbar = ttk.Progressbar(prog_frame, mode="determinate", length=570)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TProgressbar", troughcolor="#132435",
                         background="#00d4ff", thickness=12)
        self.progressbar.pack(fill="x", pady=4)

        self.label_velocidade = tk.Label(prog_frame, text="",
                                          font=("Courier New", 9), fg="#4a7fa5", bg="#0d1b2a")
        self.label_velocidade.pack(anchor="w")

        # ── Botões ──
        btn_frame = tk.Frame(self.root, bg="#0d1b2a")
        btn_frame.pack(pady=12)

        self.btn_baixar = tk.Button(btn_frame, text="⬇  BAIXAR",
                                     font=("Courier New", 11, "bold"),
                                     bg="#00d4ff", fg="#0d1b2a", relief="flat",
                                     cursor="hand2", padx=24, pady=8,
                                     command=self._iniciar_download)
        self.btn_baixar.pack(side="left", padx=8)

        self.btn_cancelar = tk.Button(btn_frame, text="✕  CANCELAR",
                                       font=("Courier New", 11, "bold"),
                                       bg="#ff4444", fg="white", relief="flat",
                                       cursor="hand2", padx=24, pady=8,
                                       state="disabled", command=self._cancelar)
        self.btn_cancelar.pack(side="left", padx=8)

    def _escolher_pasta(self):
        pasta = filedialog.askdirectory(initialdir=self.pasta_destino.get())
        if pasta:
            self.pasta_destino.set(pasta)

    def _iniciar_download(self):
        selecionados = [ARQUIVOS[i] for i, v in enumerate(self.vars) if v.get()]
        if not selecionados:
            messagebox.showwarning("Atenção", "Selecione pelo menos um arquivo.")
            return

        pasta = self.pasta_destino.get()
        if not os.path.exists(pasta):
            messagebox.showerror("Erro", f"Pasta não encontrada:\n{pasta}")
            return

        self.cancelar = False
        self.btn_baixar.config(state="disabled")
        self.btn_cancelar.config(state="normal")

        thread = threading.Thread(target=self._baixar, args=(selecionados, pasta), daemon=True)
        thread.start()

    def _cancelar(self):
        self.cancelar = True
        self._status("Cancelando...")
        if self.ftp:
            try:
                self.ftp.abort()
            except:
                pass

    def _status(self, msg):
        self.root.after(0, lambda: self.label_status.config(text=msg))

    def _velocidade(self, msg):
        self.root.after(0, lambda: self.label_velocidade.config(text=msg))

    def _progresso(self, val):
        self.root.after(0, lambda: self.progressbar.config(value=val))

    def _baixar(self, selecionados, pasta):
        try:
            self._status(f"Conectando ao FTP: {FTP_HOST}...")
            self.ftp = ftplib.FTP(FTP_HOST, timeout=30)
            self.ftp.login()
            self.ftp.cwd(FTP_BASE)
            self._status("Conectado ✓")

            for idx, arq in enumerate(selecionados):
                if self.cancelar:
                    break

                nome_arq = arq["arquivo"]
                destino = os.path.join(pasta, nome_arq)

                # Tamanho total
                try:
                    total = self.ftp.size(nome_arq)
                except:
                    total = None

                self._status(f"Baixando [{idx+1}/{len(selecionados)}]: {nome_arq}")
                self._progresso(0)

                baixado = [0]
                inicio = [time.time()]

                def callback(bloco):
                    if self.cancelar:
                        raise Exception("Cancelado pelo usuário")
                    baixado[0] += len(bloco)
                    f.write(bloco)

                    elapsed = time.time() - inicio[0]
                    if elapsed > 0:
                        vel = baixado[0] / elapsed / 1024
                        vel_str = f"{vel:.1f} KB/s" if vel < 1024 else f"{vel/1024:.1f} MB/s"
                    else:
                        vel_str = ""

                    if total:
                        pct = baixado[0] / total * 100
                        mb_baixado = baixado[0] / 1024 / 1024
                        mb_total = total / 1024 / 1024
                        self._velocidade(f"{mb_baixado:.1f} MB / {mb_total:.1f} MB  —  {vel_str}")
                        self._progresso(pct)
                    else:
                        mb_baixado = baixado[0] / 1024 / 1024
                        self._velocidade(f"{mb_baixado:.1f} MB baixados  —  {vel_str}")

                with open(destino, "wb") as f:
                    self.ftp.retrbinary(f"RETR {nome_arq}", callback, blocksize=8192)

                if not self.cancelar:
                    self._status(f"✓ {nome_arq} salvo em {pasta}")
                    self._progresso(100)

            if not self.cancelar:
                self._status(f"✅ Download(s) concluído(s)! Arquivo(s) em: {pasta}")
                self.root.after(0, lambda: messagebox.showinfo(
                    "Concluído", f"Download(s) finalizado(s)!\n\nArquivos salvos em:\n{pasta}"))
            else:
                self._status("⚠ Download cancelado.")
                self._progresso(0)

        except Exception as e:
            if not self.cancelar:
                self._status(f"❌ Erro: {e}")
                self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha no download:\n{e}"))
        finally:
            try:
                if self.ftp:
                    self.ftp.quit()
            except:
                pass
            self.root.after(0, lambda: self.btn_baixar.config(state="normal"))
            self.root.after(0, lambda: self.btn_cancelar.config(state="disabled"))

# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = SigtapDownloader(root)
    root.mainloop()
