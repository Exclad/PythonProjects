import os
import shutil
import cv2
import numpy as np
import easyocr
import threading
import time
import customtkinter as ctk
from tkinter import filedialog, messagebox

# --- Core Image Processing Logic ---

def preprocess_image(image_path):
    """
    Reads and preprocesses an image to improve OCR accuracy.
    Returns a list of processed image versions (e.g., grayscale, binary).
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            return []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 11, 2)
        return [gray, binary]
    except Exception:
        return []

def contains_keywords(image_path, reader, keywords_to_find, confidence_threshold=0.1):
    """
    Checks if an image contains any of the specified keywords using OCR.
    """
    try:
        preprocessed_images = preprocess_image(image_path)
        if not preprocessed_images:
            return False

        for preprocessed_image in preprocessed_images:
            # Use easyocr to read text from the processed image
            results = reader.readtext(preprocessed_image)
            for (bbox, text, prob) in results:
                for keyword in keywords_to_find:
                    if keyword in text.lower() and prob > confidence_threshold:
                        return True
        return False
    except Exception:
        return False

# --- Main Application GUI Class ---

class ImageSorterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Configuration ---
        self.title("Image Sorter Pro")
        self.geometry("600x650")
        ctk.set_appearance_mode("System")  # Can be "Dark", "Light"
        ctk.set_default_color_theme("blue")

        # --- State Variables ---
        self.source_folder = ""
        self.destination_folder = ""
        self.processing_thread = None
        self.stop_event = threading.Event()

        # --- UI Widget Creation ---
        self.create_widgets()

    def create_widgets(self):
        """Create and layout all the GUI widgets."""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # --- Folder Selection ---
        folder_frame = ctk.CTkFrame(main_frame)
        folder_frame.pack(pady=10, padx=10, fill="x")

        self.source_button = ctk.CTkButton(folder_frame, text="Select Source Folder", command=self.select_source_folder)
        self.source_button.pack(pady=10, fill="x")
        self.source_label = ctk.CTkLabel(folder_frame, text="No source folder selected", text_color="gray")
        self.source_label.pack()

        self.dest_button = ctk.CTkButton(folder_frame, text="Select Destination Folder", command=self.select_dest_folder)
        self.dest_button.pack(pady=10, fill="x")
        self.dest_label = ctk.CTkLabel(folder_frame, text="No destination folder selected", text_color="gray")
        self.dest_label.pack()

        # --- Keyword Selection ---
        keyword_frame = ctk.CTkFrame(main_frame)
        keyword_frame.pack(pady=10, padx=10, fill="x")
        keyword_label = ctk.CTkLabel(keyword_frame, text="Select Keywords to Filter:", font=ctk.CTkFont(weight="bold"))
        keyword_label.pack(pady=(5, 10))

        self.keywords = ["good morning", "good evening", "good afternoon", "good night", "have a nice day"]
        self.keyword_vars = {}
        for keyword in self.keywords:
            self.keyword_vars[keyword] = ctk.StringVar(value="off")
            cb = ctk.CTkCheckBox(keyword_frame, text=keyword.title(), variable=self.keyword_vars[keyword], onvalue="on", offvalue="off")
            cb.pack(anchor="w", padx=20)
        
        # --- Control Buttons ---
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(pady=20, padx=10, fill="x")

        self.start_button = ctk.CTkButton(control_frame, text="Start Processing", command=self.start_processing)
        self.start_button.pack(side="left", expand=True, padx=5)

        self.stop_button = ctk.CTkButton(control_frame, text="Stop", command=self.stop_processing, state="disabled", fg_color="red")
        self.stop_button.pack(side="right", expand=True, padx=5)
        
        # --- Progress & Status Display ---
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(pady=10, padx=10, fill="x", expand=True)
        
        self.status_label = ctk.CTkLabel(progress_frame, text="Ready to start.")
        self.status_label.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10, fill="x")
        
        self.time_label = ctk.CTkLabel(progress_frame, text="Estimated time remaining: N/A")
        self.time_label.pack(pady=5)

    # --- UI Event Handlers ---

    def select_source_folder(self):
        self.source_folder = filedialog.askdirectory(title="Select Source Folder")
        if self.source_folder:
            self.source_label.configure(text=self.source_folder)
        else:
            self.source_label.configure(text="No source folder selected")

    def select_dest_folder(self):
        self.destination_folder = filedialog.askdirectory(title="Select Destination Folder")
        if self.destination_folder:
            self.dest_label.configure(text=self.destination_folder)
        else:
            self.dest_label.configure(text="No destination folder selected")

    def start_processing(self):
        # Validate inputs
        if not self.source_folder or not self.destination_folder:
            messagebox.showerror("Error", "Please select both source and destination folders.")
            return

        selected_keywords = [kw for kw, var in self.keyword_vars.items() if var.get() == "on"]
        if not selected_keywords:
            messagebox.showerror("Error", "Please select at least one keyword to filter.")
            return
            
        # UI state updates
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.progress_bar.set(0)
        self.status_label.configure(text="Starting...")
        self.time_label.configure(text="Estimating time...")
        self.stop_event.clear()

        # Start the processing in a separate thread
        self.processing_thread = threading.Thread(
            target=self._run_processing_task,
            args=(self.source_folder, self.destination_folder, selected_keywords)
        )
        self.processing_thread.start()

    def stop_processing(self):
        if self.processing_thread and self.processing_thread.is_alive():
            self.stop_event.set()
            self.status_label.configure(text="Stopping...")
            self.stop_button.configure(state="disabled")

    # --- Worker Thread Logic ---

    def _run_processing_task(self, source, dest, keywords):
        try:
            # Initialize EasyOCR - trying for GPU first
            try:
                reader = easyocr.Reader(['en'], gpu=True)
                print("SUCCESS: EasyOCR is running on GPU.")
                self.status_label.configure(text="Initializing OCR on GPU...")
            except Exception as e:
                print(f"GPU initialization failed: {e}. Falling back to CPU.")
                self.status_label.configure(text="GPU not found. Initializing OCR on CPU...")
                reader = easyocr.Reader(['en'], gpu=False)

            # Get list of images to process
            image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
            filenames = [f for f in os.listdir(source) if f.lower().endswith(image_extensions)]
            total_files = len(filenames)
            
            start_time = time.time()
            
            for i, filename in enumerate(filenames):
                # Check if the stop button was pressed
                if self.stop_event.is_set():
                    self.after(0, self.processing_finished, "Process stopped by user.")
                    return

                # Process a single image
                file_path = os.path.join(source, filename)
                if contains_keywords(file_path, reader, keywords):
                    shutil.move(file_path, os.path.join(dest, filename))
                
                # Update progress
                self.after(0, self.update_progress, i + 1, total_files, start_time)

            self.after(0, self.processing_finished, "Processing complete.")
        except Exception as e:
            self.after(0, self.processing_finished, f"An error occurred: {e}")

    # --- Safe GUI Updates from Worker Thread ---

    def update_progress(self, current, total, start_time):
        """Safely updates the GUI with progress information."""
        progress = current / total
        self.progress_bar.set(progress)
        
        # Calculate estimated time remaining
        elapsed_time = time.time() - start_time
        avg_time_per_file = elapsed_time / current if current > 0 else 0
        remaining_files = total - current
        eta_seconds = remaining_files * avg_time_per_file
        
        if eta_seconds > 60:
            eta_str = f"{eta_seconds / 60:.1f} minutes"
        else:
            eta_str = f"{eta_seconds:.0f} seconds"
        
        self.status_label.configure(text=f"Processing: {current}/{total}")
        self.time_label.configure(text=f"Estimated time remaining: {eta_str}")

    def processing_finished(self, message):
        """Called when processing is done or stopped."""
        self.status_label.configure(text=message)
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.time_label.configure(text="")
        if "error" in message.lower():
            messagebox.showerror("Error", message)
        else:
            messagebox.showinfo("Done", message)


if __name__ == "__main__":
    app = ImageSorterApp()
    app.mainloop()