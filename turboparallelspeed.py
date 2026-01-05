import customtkinter as ctk
import os
import subprocess
import time
from tkinter import filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor

# --- Config ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class TurboCompressor(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Insta Reel Turbo Compressor (Parallel Mode 🚀)")
        self.geometry("750x650")
        self.resizable(False, False)

        self.files_to_process = []
        self.total_input_size = 0
        self.completed_files = 0
        self.is_running = False

        self.setup_ui()

    def setup_ui(self):
        # Header
        self.frame_header = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_header.pack(pady=20, padx=20, fill="x")
        ctk.CTkLabel(self.frame_header, text="Turbo Reel Compressor 🚀", font=("Roboto", 24, "bold")).pack(side="left")
        
        # File Selection
        self.frame_select = ctk.CTkFrame(self)
        self.frame_select.pack(pady=10, padx=20, fill="x")
        self.btn_folder = ctk.CTkButton(self.frame_select, text="+ Add Whole Folder", command=self.add_folder, height=45, fg_color="#333", border_width=1, border_color="#555")
        self.btn_folder.pack(side="right", padx=10, pady=15, expand=True, fill="x")
        self.btn_files = ctk.CTkButton(self.frame_select, text="+ Add Specific Files", command=self.add_files, height=45)
        self.btn_files.pack(side="left", padx=10, pady=15, expand=True, fill="x")

        # Stats
        self.frame_stats = ctk.CTkFrame(self, fg_color="#222")
        self.frame_stats.pack(pady=10, padx=20, fill="x")
        self.lbl_count = ctk.CTkLabel(self.frame_stats, text="Files: 0", font=("Arial", 14, "bold"))
        self.lbl_count.pack(side="left", padx=20, pady=15)
        self.lbl_status = ctk.CTkLabel(self.frame_stats, text="Status: Idle", font=("Arial", 14), text_color="#F1C40F")
        self.lbl_status.pack(side="right", padx=20, pady=15)

        # Quality Slider
        self.lbl_slider = ctk.CTkLabel(self, text="Compression Strength: Balanced (CRF 26)")
        self.lbl_slider.pack(pady=(10, 5))
        # Default 26: A bit higher compression to compensate for speed
        self.slider = ctk.CTkSlider(self, from_=20, to=32, number_of_steps=12, command=self.update_label)
        self.slider.set(26) 
        self.slider.pack(padx=40, fill="x")

        # Start Button
        self.btn_start = ctk.CTkButton(self, text="START TURBO MODE (3x Speed)", height=60, fg_color="#d63031", hover_color="#b71540", font=("Roboto", 18, "bold"), command=self.start_parallel_processing)
        self.btn_start.pack(pady=20, padx=20, fill="x")

        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.pack(padx=20, fill="x")

        # Log
        self.log_box = ctk.CTkTextbox(self, height=120, font=("Consolas", 11))
        self.log_box.pack(pady=10, padx=20, fill="x")
        self.log("Turbo Mode Ready. This will compress 3 videos at once.")

    def add_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Video", "*.mp4 *.mov *.mkv")])
        if files: self.update_list(files)

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            found = [os.path.join(r, f) for r, _, fs in os.walk(folder) for f in fs if f.lower().endswith(('.mp4', '.mov', '.mkv'))]
            self.update_list(found)

    def update_list(self, new_files):
        self.files_to_process = list(set(self.files_to_process + list(new_files)))
        self.lbl_count.configure(text=f"Files: {len(self.files_to_process)}")
        self.log(f"Queue updated. Total files: {len(self.files_to_process)}")

    def update_label(self, val):
        self.lbl_slider.configure(text=f"Compression Strength: CRF {int(val)}")

    def log(self, msg):
        self.log_box.insert("end", f"> {msg}\n")
        self.log_box.see("end")

    def start_parallel_processing(self):
        if not self.files_to_process: return
        self.is_running = True
        self.btn_start.configure(state="disabled", text="Running Turbo Compression...")
        self.completed_files = 0
        self.log("--- STARTING PARALLEL COMPRESSION ---")
        
        # Run the manager in a separate thread so UI doesn't freeze
        import threading
        threading.Thread(target=self.run_thread_pool, daemon=True).start()

    def run_thread_pool(self):
        # WORKERS = 3 (Adjust if your laptop freezes, but 3 is safe for most)
        with ThreadPoolExecutor(max_workers=3) as executor:
            list(executor.map(self.compress_single_video, self.files_to_process))
        
        self.log("--- ALL DONE ---")
        self.btn_start.configure(state="normal", text="START TURBO MODE (3x Speed)")
        self.lbl_status.configure(text="Status: Finished")
        messagebox.showinfo("Done", "Turbo Compression Complete!")

    def compress_single_video(self, fpath):
        fname = os.path.basename(fpath)
        crf = int(self.slider.get())
        
        out_folder = os.path.join(os.path.dirname(fpath), "Turbo_Reels")
        if not os.path.exists(out_folder): os.makedirs(out_folder, exist_ok=True)
        out_path = os.path.join(out_folder, f"turbo_{fname}")

        # THE FASTEST SETTINGS:
        # -preset ultrafast (Least CPU usage per frame)
        # -c:a copy (Instant audio, 0 CPU usage)
        cmd = [
            'ffmpeg', '-y', '-i', fpath,
            '-vcodec', 'libx264', 
            '-crf', str(crf), 
            '-preset', 'ultrafast', 
            '-c:a', 'copy', 
            out_path
        ]
        
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
            
            self.completed_files += 1
            progress = self.completed_files / len(self.files_to_process)
            self.progress.set(progress)
            
            # Calculate savings
            orig = os.path.getsize(fpath) / (1024*1024)
            new = os.path.getsize(out_path) / (1024*1024)
            self.log(f"✔ Done: {fname} ({orig:.1f}MB -> {new:.1f}MB)")
            
            # Update status text periodically
            self.lbl_status.configure(text=f"Status: {self.completed_files}/{len(self.files_to_process)}")
            
        except Exception as e:
            self.log(f"❌ Error on {fname}")

if __name__ == "__main__":
    app = TurboCompressor()
    app.mainloop()