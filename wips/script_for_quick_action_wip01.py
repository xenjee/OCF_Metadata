import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import json

# Add REDCINE-X PRO and SONY RAWexporter paths to the PATH environment variable.
os.environ['PATH'] = (
    "/Applications/REDCINE-X PRO/REDCINE-X PRO.app/Contents/MacOS:"
    "/Applications/RAW Viewer.app/Contents/MacOS/rawexporter:" +
    os.environ.get('PATH', '')
)

# Allowed file extensions mapping.
allowed_extensions = {
    'ARRI': ['.mxf', '.mov'],
    'RED': ['.r3d'],
    'SONY': ['.mxf']
}

# Tool paths for the different camera types.
tool_paths = {
    'ARRI': "/Users/stefan/WORK/DEV/metadata/art-cmd_0.3.0_macos_universal/bin/art-cmd",
    'RED': "REDline",     # Resolved via PATH.
    'SONY': "rawexporter" # Resolved via PATH.
}

# ---------------- Custom Canvas-Based Button ----------------
class CustomButton(tk.Canvas):
    def __init__(self, master, text, command=None, width=120, height=30,
                 bg="#0d6efd", fg="#c8c8c8", activebg="#0b5ed7", activefg="#c8c8c8",
                 font=("Arial", 12, "bold"), **kwargs):
        super().__init__(master, width=width, height=height, highlightthickness=0, bd=0, bg=bg, **kwargs)
        self.command = command
        self.bg = bg
        self.fg = fg
        self.activebg = activebg
        self.activefg = activefg
        self.font = font
        self.text = text
        self.rect = self.create_rectangle(0, 0, width, height, fill=bg, outline=bg)
        self.label = self.create_text(width/2, height/2, text=text, fill=fg, font=font)
        self.bind("<Button-1>", self.on_click)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.tag_bind(self.rect, "<Button-1>", self.on_click)
        self.tag_bind(self.label, "<Button-1>", self.on_click)
        self.tag_bind(self.rect, "<Enter>", self.on_enter)
        self.tag_bind(self.label, "<Enter>", self.on_enter)
        self.tag_bind(self.rect, "<Leave>", self.on_leave)
        self.tag_bind(self.label, "<Leave>", self.on_leave)

    def on_click(self, event):
        if self.command:
            self.command()

    def on_enter(self, event):
        self.itemconfig(self.rect, fill=self.activebg, outline=self.activebg)
        self.itemconfig(self.label, fill=self.activefg)

    def on_leave(self, event):
        self.itemconfig(self.rect, fill=self.bg, outline=self.bg)
        self.itemconfig(self.label, fill=self.fg)

# ---------------- Custom Canvas-Based Dropdown ----------------
class CustomDropdown(tk.Canvas):
    def __init__(self, master, options, command=None, width=150, height=30,
                 bg="#404040", fg="#d9d9d9", activebg="#646464", font=("Arial", 12),
                 **kwargs):
        # Initialize canvas
        super().__init__(master, width=width, height=height, highlightthickness=0, bd=0, bg=bg, **kwargs)
        self.options = options
        self.command = command  # Callback when selection changes
        self.width = width
        self.height = height
        self.bg = bg
        self.fg = fg
        self.activebg = activebg
        self.font = font
        self.current_value = options[0] if options else ""
        # Draw rectangle background
        self.rect = self.create_rectangle(0, 0, width, height, fill=bg, outline=bg)
        # Draw current selection text
        self.text_item = self.create_text(5, height/2, anchor="w", text=self.current_value,
                                          fill=fg, font=font)
        # Bind click event
        self.bind("<Button-1>", self.toggle_dropdown)
        self.dropdown_window = None

    def toggle_dropdown(self, event):
        if self.dropdown_window:
            self.close_dropdown()
        else:
            self.open_dropdown()

    def open_dropdown(self):
        # Create a Toplevel window that appears below the widget
        self.dropdown_window = tk.Toplevel(self)
        self.dropdown_window.wm_overrideredirect(True)  # Remove window decorations
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.height
        self.dropdown_window.geometry(f"{self.width}x{len(self.options)*self.height}+{x}+{y}")
        # Create option buttons inside the dropdown window
        for index, option in enumerate(self.options):
            # Using a simple Label for each option
            lbl = tk.Label(self.dropdown_window, text=option, bg=self.bg, fg=self.fg, font=self.font)
            lbl.place(x=0, y=index*self.height, width=self.width, height=self.height)
            lbl.bind("<Button-1>", lambda e, opt=option: self.select_option(opt))
            lbl.bind("<Enter>", lambda e, widget=lbl: widget.config(bg=self.activebg))
            lbl.bind("<Leave>", lambda e, widget=lbl: widget.config(bg=self.bg))
        # Bind click outside to close dropdown
        self.dropdown_window.bind("<FocusOut>", lambda e: self.close_dropdown())
        self.dropdown_window.focus_set()

    def close_dropdown(self):
        if self.dropdown_window:
            self.dropdown_window.destroy()
            self.dropdown_window = None

    def select_option(self, option):
        self.current_value = option
        self.itemconfig(self.text_item, text=option)
        self.close_dropdown()
        if self.command:
            self.command(option)

    def get(self):
        return self.current_value

# ---------------- UI Functions (Same as original) ----------------
def browse_folder(entry):
    folder = filedialog.askdirectory()
    if folder:
        entry.delete(0, tk.END)
        entry.insert(0, folder)
        update_found_files()

def update_extensions_display(new_value=None):
    camera = custom_dropdown.get()
    exts = allowed_extensions.get(camera, [])
    extensions_label.config(text="Allowed Extensions: " + ", ".join(exts))
    update_found_files()

def update_found_files():
    source_folder = source_entry.get().strip()
    camera = custom_dropdown.get()
    files_found = []
    if os.path.isdir(source_folder) and camera in allowed_extensions:
        allowed = [ext.lower() for ext in allowed_extensions[camera]]
        for dirpath, _, filenames in os.walk(source_folder):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in allowed:
                    rel_path = os.path.relpath(os.path.join(dirpath, filename), source_folder)
                    files_found.append(rel_path)
    found_files_text.config(state=tk.NORMAL)
    found_files_text.delete("1.0", tk.END)
    if files_found:
        found_files_text.insert(tk.END, "\n".join(files_found))
    else:
        found_files_text.insert(tk.END, "No matching files found.")
    found_files_text.config(state=tk.DISABLED)

def process_files():
    source_folder = source_entry.get().strip()
    dest_folder = dest_entry.get().strip()
    camera_type = custom_dropdown.get()

    if not os.path.isdir(source_folder):
        messagebox.showerror("Error", "The source folder path is invalid.")
        return
    if not os.path.isdir(dest_folder):
        messagebox.showerror("Error", "The destination folder path is invalid.")
        return
    if camera_type not in allowed_extensions:
        messagebox.showerror("Error", "Please select a valid camera type.")
        return

    allowed = [ext.lower() for ext in allowed_extensions[camera_type]]
    for dirpath, _, filenames in os.walk(source_folder):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in allowed:
                continue
            file_path = os.path.join(dirpath, filename)
            base, _ = os.path.splitext(filename)
            raw_output_file = os.path.join(dest_folder, base + "_metadata_export.txt")
            json_output_file = os.path.join(dest_folder, base + "_metadata_export.json")
            if camera_type == 'ARRI':
                command = [tool_paths['ARRI'], "export", file_path, "--output", json_output_file]
                try:
                    subprocess.run(command, capture_output=True, text=True, check=True)
                    print(f"Processed {file_path} -> {json_output_file}")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
            elif camera_type == 'RED':
                command = [tool_paths['RED'], "--i", file_path, "--printMeta", "1"]
                result = subprocess.run(command, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"REDline error for {file_path}: {result.stderr}")
                raw_output = result.stdout
                try:
                    with open(raw_output_file, "w") as f:
                        f.write(raw_output)
                    print(f"Wrote raw output for {file_path} -> {raw_output_file}")
                except Exception as e:
                    print(f"Error writing raw output for {file_path}: {e}")
                metadata = {}
                for line in raw_output.strip().splitlines():
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip()] = value.strip()
                try:
                    with open(json_output_file, "w") as f:
                        json.dump(metadata, f, indent=4)
                    print(f"Wrote JSON output for {file_path} -> {json_output_file}")
                except Exception as e:
                    print(f"Error writing JSON output for {file_path}: {e}")
            elif camera_type == 'SONY':
                command = [tool_paths['SONY'], "--metalist", "--input", file_path]
                try:
                    result = subprocess.run(command, capture_output=True, text=True, check=True)
                    raw_output = result.stdout
                    try:
                        with open(raw_output_file, "w") as f:
                            f.write(raw_output)
                        print(f"Wrote raw output for {file_path} -> {raw_output_file}")
                    except Exception as e:
                        print(f"Error writing raw output for {file_path}: {e}")
                    metadata = {}
                    for line in raw_output.strip().splitlines():
                        if ":" in line:
                            key, value = line.split(":", 1)
                            metadata[key.strip()] = value.strip()
                    try:
                        with open(json_output_file, "w") as f:
                            json.dump(metadata, f, indent=4)
                        print(f"Wrote JSON output for {file_path} -> {json_output_file}")
                    except Exception as e:
                        print(f"Error writing JSON output for {file_path}: {e}")
                except subprocess.CalledProcessError as e:
                    print(f"SONY rawexporter error for {file_path}: {e}")
    messagebox.showinfo("Completed", "Metadata extraction completed.")
    update_found_files()

# ---------------- Build the UI ----------------
root = tk.Tk()
root.title("OCF Metadata JSON Generator")

# Source Folder Input.
tk.Label(root, text="Source Folder (camera files):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
source_entry = tk.Entry(root, width=50)
source_entry.grid(row=0, column=1, padx=5, pady=5)
browse_source_btn = CustomButton(root, text="Browse", command=lambda: browse_folder(source_entry), width=80, height=30)
browse_source_btn.grid(row=0, column=2, padx=5, pady=5)

# Destination Folder Input.
tk.Label(root, text="Destination Folder (JSON files):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
dest_entry = tk.Entry(root, width=50)
dest_entry.grid(row=1, column=1, padx=5, pady=5)
browse_dest_btn = CustomButton(root, text="Browse", command=lambda: browse_folder(dest_entry), width=80, height=30)
browse_dest_btn.grid(row=1, column=2, padx=5, pady=5)

# Camera Brand Dropdown using CustomDropdown.
tk.Label(root, text="Camera Brand:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
custom_dropdown = CustomDropdown(root, options=list(allowed_extensions.keys()), width=150, height=30,
                                 bg="#404040", fg="#d9d9d9", activebg="#646464", font=("Arial", 12))
custom_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="w")
# Set callback to update extensions display when selection changes.
def dropdown_callback(selected):
    update_extensions_display()
custom_dropdown.command = dropdown_callback

# Allowed Extensions Display.
extensions_label = tk.Label(root, text="Allowed Extensions: " + ", ".join(allowed_extensions[custom_dropdown.get()]))
extensions_label.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="w")

# Process Files Button.
process_btn = CustomButton(root, text="Search & Process Files", command=process_files, width=160, height=30)
process_btn.grid(row=4, column=1, padx=5, pady=20)

# Found Files List (Scrollable Text Area).
files_frame = tk.Frame(root)
files_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
found_files_text = tk.Text(files_frame, height=10)
found_files_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar = tk.Scrollbar(files_frame, command=found_files_text.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
found_files_text.config(yscrollcommand=scrollbar.set)

root.grid_rowconfigure(5, weight=1)
root.grid_columnconfigure(1, weight=1)

# Pre-fill source folder if provided as a command-line argument.
if len(sys.argv) > 1:
    arg_path = sys.argv[1].strip()
    if os.path.isdir(arg_path):
        source_entry.delete(0, tk.END)
        source_entry.insert(0, arg_path)

update_found_files()
root.mainloop()
