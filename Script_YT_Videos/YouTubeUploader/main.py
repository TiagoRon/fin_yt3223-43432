import os
import threading
import time
import customtkinter as ctk
from tkinter import filedialog
from utils import extract_rar, parse_metadata
from uploader import get_driver, upload_video_selenium

# Set appearance mode and default color theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Auto-Uploader (Selenium)")
        self.geometry("600x500")


        #Center
        
        ancho_ventana =self.winfo_reqwidth()
        alto_ventana = self.winfo_reqheight()
        x = (self.winfo_screenwidth() // 2) - (ancho_ventana // 2 + 200) 
        y = (self.winfo_screenheight() // 2) - (alto_ventana // 2 + 200) 
        self.geometry(f'+{x}+{y}')
        self.resizable(0,0)



        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Title Label
        self.label = ctk.CTkLabel(self, text="YouTube Auto-Uploader", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Folder Info Label
        # Use directory of the script file, not CWD
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.uploads_dir = os.path.join(self.script_dir, "Uploads")
        
        if not os.path.exists(self.uploads_dir):
            os.makedirs(self.uploads_dir)
            
        print(f"DEBUG: Looking for files in: {self.uploads_dir}") # Debug print
        self.folder_label = ctk.CTkLabel(self, text=f"Watching Folder: {self.uploads_dir}", text_color="gray")
        self.folder_label.grid(row=1, column=0, padx=20, pady=(0, 10))

        # Log Text Box
        self.log_box = ctk.CTkTextbox(self, width=500, height=300)
        self.log_box.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.log_box.configure(state="disabled")

        # Start Button
        self.start_button = ctk.CTkButton(self, text="Start Execution", command=self.start_execution)
        self.start_button.grid(row=3, column=0, padx=20, pady=20)

    def log(self, message):
        self.after(0, self._log_internal, message)

    def _log_internal(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def start_execution(self):
        # Start processing in a separate thread
        thread = threading.Thread(target=self.process_videos)
        thread.start()

    def process_videos(self):
        self.start_button.configure(state="disabled")
        driver = None
        
        try:
            self.log(f"Checking for archives in: {self.uploads_dir}")
            
            # Check for RAR and ZIP files
            archive_files = [f for f in os.listdir(self.uploads_dir) if f.lower().endswith(('.rar', '.zip'))]
            
            if not archive_files:
                self.log("No .rar or .zip files found in 'Uploads' folder.")
                self.log("Please put your archive files there and try again.")
                return

            self.log(f"Found {len(archive_files)} archive files. Initializing Browser...")
            driver = get_driver()

            # --- SCHEDULING LOGIC START ---
            import datetime
            from datetime import timedelta
            
            SCHEDULE_SLOTS = [11, 13, 16, 18, 20, 22] # Hours
            
            now = datetime.datetime.now()
            current_schedule_date = now.date()
            current_slot_index = 0
            
            # Find the next available slot for TODAY
            found_slot_today = False
            for i, slot_hour in enumerate(SCHEDULE_SLOTS):
                if now.hour < slot_hour:
                    current_slot_index = i
                    found_slot_today = True
                    break
            
            if not found_slot_today:
                # If no slots left today, start tomorrow at first slot
                current_schedule_date = current_schedule_date + timedelta(days=1)
                current_slot_index = 0
                
            self.log(f"Starting schedule from: {current_schedule_date} at {SCHEDULE_SLOTS[current_slot_index]}:00")
            # --- SCHEDULING LOGIC END ---

            for archive_file in archive_files:
                archive_path = os.path.join(self.uploads_dir, archive_file)
                self.log(f"--- Processing: {archive_file} ---")

                extract_dir = os.path.join(self.uploads_dir, "temp_extracted")
                self.log("Extracting...")
                extracted_files = extract_rar(archive_path, extract_dir)
                
                if extracted_files:
                    video_files = []
                    text_file = None
                    
                    # FIRST PASS: Collect all videos and finding the text file
                    for root, dirs, files in os.walk(extract_dir):
                        for file in files:
                            if file.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                                video_files.append(os.path.join(root, file))
                            elif file.lower().endswith('.txt'):
                                text_file = os.path.join(root, file)
                    
                    if video_files and text_file:
                        self.log(f"Found {len(video_files)} Videos in archive.")
                        metadata = parse_metadata(text_file)
                        
                        for i, video_file in enumerate(video_files):
                            self.log(f"Uploading Video {i+1}/{len(video_files)}: {os.path.basename(video_file)}")
                            
                            # Prepare Schedule Time
                            scheduled_hour = SCHEDULE_SLOTS[current_slot_index]
                            schedule_time_str = f"{scheduled_hour:02d}:00"
                            schedule_date_str = current_schedule_date.strftime("%d/%m/%Y") # DD/MM/YYYY format usually
                            
                            self.log(f"Scheduled for: {schedule_date_str} at {schedule_time_str}")
                            
                            self.log("Uploading via Selenium...")
                            success = upload_video_selenium(
                                driver, 
                                video_file, 
                                metadata.get("title", "Untitled"), 
                                metadata.get("description", "No description"), 
                                metadata.get("tags", []),
                                privacy_status="schedule", # Changed to schedule
                                schedule_date=schedule_date_str,
                                schedule_time=schedule_time_str
                            )
                            
                            if success:
                                self.log("Upload scheduled successfully!")
                            else:
                                self.log("Upload failed.")
                            
                            # Advance Schedule Slot
                            current_slot_index += 1
                            if current_slot_index >= len(SCHEDULE_SLOTS):
                                current_slot_index = 0
                                current_schedule_date = current_schedule_date + timedelta(days=1)
                                self.log(f"Moving schedule to next day: {current_schedule_date}")

                    else:
                        self.log("Missing video or text file inside archive.")
                        if not video_files: self.log("- No video files found.")
                        if not text_file: self.log("- No text file found.")
                    
                    # Optional: Cleanup
                    # import shutil
                    # shutil.rmtree(extract_dir)
                else:
                    self.log("Extraction failed.")

            self.log("--- All tasks completed ---")

        except Exception as e:
            self.log(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if driver:
                # Do we close the driver? Maybe keep it open for user to see?
                # For now, let's keep it open or close it?
                # Usually we close it, but if user wants to check...
                # let's leave it open for a bit or ask user.
                # driver.quit() 
                self.log("Browser session remains open.")
            
            self.start_button.configure(state="normal")

if __name__ == "__main__":
    app = App()
    app.mainloop()
