import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
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

def browse_folder(entry):
    folder = filedialog.askdirectory()
    if folder:
        entry.delete(0, tk.END)
        entry.insert(0, folder)
        update_found_files()

def update_extensions_display(*args):
    camera = camera_var.get()
    exts = allowed_extensions.get(camera, [])
    exts_str = ", ".join(exts)
    extensions_label.config(text=f"Allowed Extensions: {exts_str}")
    update_found_files()

def update_found_files():
    """Recursively update the text area listing the files in the source folder that match allowed extensions."""
    source_folder = source_entry.get().strip()
    camera = camera_var.get()
    files_found = []
    
    if os.path.isdir(source_folder) and camera in allowed_extensions:
        allowed = [ext.lower() for ext in allowed_extensions[camera]]
        for dirpath, dirnames, filenames in os.walk(source_folder):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                ext = os.path.splitext(filename)[1].lower()
                if ext in allowed:
                    # Include relative path for clarity.
                    rel_path = os.path.relpath(file_path, source_folder)
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
    camera_type = camera_var.get()

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
    
    for dirpath, dirnames, filenames in os.walk(source_folder):
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in allowed:
                continue

            file_path = os.path.join(dirpath, filename)
            base, _ = os.path.splitext(filename)
            
            # For RED and SONY, we create both a raw text output and a JSON file.
            raw_output_file = os.path.join(dest_folder, base + "_metadata_export.txt")
            json_output_file = os.path.join(dest_folder, base + "_metadata_export.json")

            if camera_type == 'ARRI':
                # ARRI command: uses 'export' and writes output directly to JSON file.
                command = [tool_paths['ARRI'], "export", file_path, "--output", json_output_file]
                try:
                    subprocess.run(command, capture_output=True, text=True, check=True)
                    if os.path.exists(json_output_file):
                        print(f"Processed {file_path} -> {json_output_file}")
                    else:
                        print(f"Error: Output file not created for {file_path}.")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
            elif camera_type == 'RED':
                # REDline command: uses --i and --printMeta 1; capture stdout.
                command = [tool_paths['RED'], "--i", file_path, "--printMeta", "1"]
                result = subprocess.run(command, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"REDline returned exit code {result.returncode} for {file_path}")
                    print(f"Stderr: {result.stderr}")
                raw_output = result.stdout
                # Write raw output to text file.
                try:
                    with open(raw_output_file, "w") as f:
                        f.write(raw_output)
                    print(f"Wrote raw output for {file_path} -> {raw_output_file}")
                except Exception as e:
                    print(f"Error writing raw output for {file_path}: {e}")
                # Parse raw output into a dictionary.
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
                # SONY command: uses rawexporter with --metalist and --input.
                command = [tool_paths['SONY'], "--metalist", "--input", file_path]
                try:
                    result = subprocess.run(command, capture_output=True, text=True, check=True)
                    raw_output = result.stdout
                    # Write raw output to text file.
                    try:
                        with open(raw_output_file, "w") as f:
                            f.write(raw_output)
                        print(f"Wrote raw output for {file_path} -> {raw_output_file}")
                    except Exception as e:
                        print(f"Error writing raw output for {file_path}: {e}")
                    # Parse the raw output into a dictionary.
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
                    print(f"Error processing {file_path}: {e}")
    messagebox.showinfo("Completed", "Metadata extraction completed.")
    update_found_files()

# Create the main Tkinter window.
root = tk.Tk()
root.title("Camera Metadata Extraction Tool")

# --- Source Folder Input ---
tk.Label(root, text="Source Folder (camera files):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
source_entry = tk.Entry(root, width=75)
source_entry.grid(row=0, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=lambda: browse_folder(source_entry)).grid(row=0, column=2, padx=5, pady=5)

# --- Destination Folder Input ---
tk.Label(root, text="Destination Folder (JSON files):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
dest_entry = tk.Entry(root, width=75)
dest_entry.grid(row=1, column=1, padx=5, pady=5)
tk.Button(root, text="Browse", command=lambda: browse_folder(dest_entry)).grid(row=1, column=2, padx=5, pady=5)

# --- Camera Type Drop-Down ---
tk.Label(root, text="Camera Type:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
camera_var = tk.StringVar()
camera_options = ttk.Combobox(root, textvariable=camera_var, values=list(allowed_extensions.keys()), state="readonly")
camera_options.grid(row=2, column=1, padx=5, pady=5)
camera_options.current(0)
camera_options.bind("<<ComboboxSelected>>", update_extensions_display)

# --- Allowed Extensions Display ---
extensions_label = tk.Label(root, text="Allowed Extensions: " + ", ".join(allowed_extensions[camera_options.get()]))
extensions_label.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="w")

# --- Start Processing Button ---
tk.Button(root, text="Start Processing", command=process_files).grid(row=4, column=1, padx=5, pady=20)

# --- Found Files List (Scrollable Text Area) ---
files_frame = tk.Frame(root)
files_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
found_files_text = tk.Text(files_frame, height=10, wrap=tk.NONE)
found_files_text.config(state=tk.DISABLED)
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
        source_entry.insert(0, arg_path)

update_found_files()
root.mainloop()
