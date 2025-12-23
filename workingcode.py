import customtkinter as ctk
import os
import subprocess
import threading
import time
from tkinter import filedialog, messagebox

# --- Config ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SimpleCompressor(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Insta Reel Compressor (Simple & Fast)")
        self.geometry("700x600")
        self.resizable(False, False)

        # Variables
        self.files_to_process = []
        self.output_dir = ""
        self.total_input_size = 0
        self.is_running = False

        self.setup_ui()

    def setup_ui(self):
        # --- 1. Header & Output Selection ---
        self.frame_header = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_header.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(self.frame_header, text="Reel Compressor", font=("Roboto", 24, "bold")).pack(side="left")
        
        self.btn_dest = ctk.CTkButton(self.frame_header, text="📂 Change Save Location", command=self.change_destination, width=150)
        self.btn_dest.pack(side="right")
        
        self.lbl_dest = ctk.CTkLabel(self, text="Saving to: Default (New Folder inside source)", text_color="gray", font=("Arial", 11))
        self.lbl_dest.pack(padx=20, anchor="e", pady=(0, 10))

        # --- 2. File Selection Buttons ---
        self.frame_select = ctk.CTkFrame(self)
        self.frame_select.pack(pady=10, padx=20, fill="x")

        self.btn_files = ctk.CTkButton(self.frame_select, text="+ Add Specific Files", command=self.add_files, height=40)
        self.btn_files.pack(side="left", padx=10, pady=15, expand=True, fill="x")

        self.btn_folder = ctk.CTkButton(self.frame_select, text="+ Add Whole Folder", command=self.add_folder, height=40, fg_color="#333", border_width=1, border_color="#555")
        self.btn_folder.pack(side="right", padx=10, pady=15, expand=True, fill="x")

        # --- 3. Statistics Panel ---
        self.frame_stats = ctk.CTkFrame(self, fg_color="#222")
        self.frame_stats.pack(pady=10, padx=20, fill="x")

        self.lbl_count = ctk.CTkLabel(self.frame_stats, text="Files: 0", font=("Arial", 14, "bold"))
        self.lbl_count.pack(side="left", padx=20, pady=15)

        self.lbl_size = ctk.CTkLabel(self.frame_stats, text="Input Size: 0 MB", font=("Arial", 14))
        self.lbl_size.pack(side="left", padx=20, pady=15)

        self.lbl_est_save = ctk.CTkLabel(self.frame_stats, text="Est. Saving: --", font=("Arial", 14), text_color="#4cc9f0")
        self.lbl_est_save.pack(side="right", padx=20, pady=15)

        # --- 4. Quality Slider ---
        self.lbl_slider = ctk.CTkLabel(self, text="Compression Level: Balanced (Recommended)")
        self.lbl_slider.pack(pady=(10, 5))
        
        self.slider = ctk.CTkSlider(self, from_=18, to=32, number_of_steps=14, command=self.update_estimates)
        self.slider.set(23)
        self.slider.pack(padx=40, fill="x")

        # --- 5. Action Area ---
        self.btn_start = ctk.CTkButton(self, text="START COMPRESSING", height=50, fg_color="green", font=("Roboto", 16, "bold"), command=self.start_processing)
        self.btn_start.pack(pady=20, padx=20, fill="x")

        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.pack(padx=20, fill="x")
        
        self.lbl_time = ctk.CTkLabel(self, text="Time Remaining: --:--")
        self.lbl_time.pack(pady=5)

        # --- 6. Log ---
        self.log_box = ctk.CTkTextbox(self, height=100)
        self.log_box.pack(pady=10, padx=20, fill="x")
        self.log("Ready. Select files to begin.")

    # --- Functions ---

    def add_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Video", "*.mp4 *.mov *.mkv *.avi")])
        if files:
            self.update_file_list(list(files))

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            found = []
            for root, _, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(('.mp4', '.mov', '.mkv')):
                        found.append(os.path.join(root, f))
            self.update_file_list(found)

    def update_file_list(self, new_files):
        # Add new files avoiding duplicates
        current_set = set(self.files_to_process)
        for f in new_files:
            current_set.add(f)
        self.files_to_process = list(current_set)
        
        # Calculate size
        self.total_input_size = sum(os.path.getsize(f) for f in self.files_to_process)
        
        # Update labels
        mb = self.total_input_size / (1024 * 1024)
        self.lbl_count.configure(text=f"Files: {len(self.files_to_process)}")
        self.lbl_size.configure(text=f"Input Size: {mb:.1f} MB")
        self.log(f"Added {len(new_files)} files. Total list: {len(self.files_to_process)}")
        self.update_estimates(self.slider.get())

    def update_estimates(self, value):
        # Update Slider Label
        val = int(value)
        if val < 21: txt = "High Quality (Big Files)"
        elif val < 26: txt = "Balanced (Recommended)"
        else: txt = "Max Compression (Small Files)"
        self.lbl_slider.configure(text=f"Compression Level: {txt} (CRF {val})")

        # Update Savings Estimate
        if self.total_input_size > 0:
            # Heuristic: CRF 23 ~ 50% savings, CRF 28 ~ 75% savings
            ratio = 1.0 - ((val - 17) * 0.05)
            ratio = max(0.1, min(0.9, ratio)) # Clamp
            saved_mb = (self.total_input_size * (1 - ratio)) / (1024 * 1024)
            self.lbl_est_save.configure(text=f"Est. Saving: ~{saved_mb:.0f} MB")

    def change_destination(self):
        d = filedialog.askdirectory()
        if d:
            self.output_dir = d
            self.lbl_dest.configure(text=f"Saving to: {d}")

    def log(self, msg):
        self.log_box.insert("end", f"> {msg}\n")
        self.log_box.see("end")

    def start_processing(self):
        if not self.files_to_process:
            messagebox.showwarning("No Files", "Please add files first!")
            return
        
        self.is_running = True
        self.btn_start.configure(state="disabled", text="Running...")
        threading.Thread(target=self.run_ffmpeg, daemon=True).start()

    def run_ffmpeg(self):
        start_time = time.time()
        processed_bytes = 0
        total_output_size = 0
        crf = int(self.slider.get())

        for idx, fpath in enumerate(self.files_to_process):
            fname = os.path.basename(fpath)
            
            # Determine output path
            if self.output_dir:
                out_folder = self.output_dir
            else:
                out_folder = os.path.join(os.path.dirname(fpath), "Compressed_Reels")
            
            if not os.path.exists(out_folder):
                os.makedirs(out_folder)
            
            out_path = os.path.join(out_folder, f"comp_{fname}")

            self.log(f"Compressing: {fname}...")
            
            # FFmpeg Command
            cmd = [
                'ffmpeg', '-y', '-i', fpath,
                '-vcodec', 'libx264', '-crf', str(crf), '-preset', 'faster',
                '-acodec', 'aac', '-b:a', '128k',
                out_path
            ]

            try:
                # Windows startup info to hide console
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
                
                # Update Stats
                orig_size = os.path.getsize(fpath)
                new_size = os.path.getsize(out_path)
                processed_bytes += orig_size
                total_output_size += new_size
                
                # Time Calc
                elapsed = time.time() - start_time
                speed = processed_bytes / elapsed # bytes per sec
                remaining = self.total_input_size - processed_bytes
                secs_left = remaining / speed if speed > 0 else 0
                
                mins = int(secs_left // 60)
                secs = int(secs_left % 60)
                self.lbl_time.configure(text=f"Time Remaining: {mins}m {secs}s")
                
                # Progress Bar
                self.progress.set((idx + 1) / len(self.files_to_process))

            except Exception as e:
                self.log(f"ERROR on {fname}: {e}")

        # Finish
        saved_mb = (self.total_input_size - total_output_size) / (1024 * 1024)
        self.log(f"DONE! Total Saved: {saved_mb:.2f} MB")
        self.btn_start.configure(state="normal", text="START COMPRESSING")
        self.lbl_time.configure(text="Finished.")
        messagebox.showinfo("Complete", f"Compression Finished!\nYou saved {saved_mb:.2f} MB.")

if __name__ == "__main__":
    app = SimpleCompressor()
    app.mainloop()