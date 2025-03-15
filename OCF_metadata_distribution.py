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

# trying to fix automator not running the processing files action
# Add the conda environment's bin directory to PATH ==> doesn't work
# conda_bin = "/opt/miniconda3/envs/ocf_metadata_wep_app/bin"
# os.environ["PATH"] = conda_bin + os.pathsep + os.environ.get("PATH", "")

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

# trying to fix automator not running the processing files action ==> doesn't work this way
# tool_paths = {
#     'ARRI': "/Users/stefan/WORK/DEV/metadata/art-cmd_0.3.0_macos_universal/bin/art-cmd",
#     'RED': "/Applications/REDCINE-X PRO/REDCINE-X PRO.app/Contents/MacOS/REDline",
#     'SONY': "/Applications/RAW Viewer.app/Contents/MacOS/rawexporter/rawexporter"
# }


# ---------------- Custom Canvas-Based Button ----------------
class CustomButton(tk.Canvas):
    def __init__(self, master, text, command=None, width=120, height=30,
                 bg="#0d6efd", fg="#c8c8c8", activebg="#0b5ed7", activefg="#c8c8c8",
                 font=("Arial", 14), **kwargs):
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
        return "break"  # Prevent further event propagation.

    def on_enter(self, event):
        self.itemconfig(self.rect, fill=self.activebg, outline=self.activebg)
        self.itemconfig(self.label, fill=self.activefg)

    def on_leave(self, event):
        self.itemconfig(self.rect, fill=self.bg, outline=self.bg)
        self.itemconfig(self.label, fill=self.fg)

# ---------------- Custom Canvas-Based Dropdown ----------------
class CustomDropdown(tk.Canvas):
    def __init__(self, master, options, command=None, width=150, height=30,
                 bg="#364561", fg="#bbbbbb", activebg="#0b5ed7", font=("Arial", 14),
                 **kwargs):
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
        self.rect = self.create_rectangle(0, 0, width, height, fill=bg, outline=bg)
        self.text_item = self.create_text(width/2, height/2, anchor="center", text=self.current_value,
                                          fill=fg, font=font)
        # Bind click and hover events to the main dropdown canvas
        self.bind("<Button-1>", self.toggle_dropdown)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.dropdown_window = None

    def on_enter(self, event):
        # Change background color when hovering over the dropdown "button"
        self.itemconfig(self.rect, fill=self.activebg, outline=self.activebg)

    def on_leave(self, event):
        # Revert background color when not hovering
        self.itemconfig(self.rect, fill=self.bg, outline=self.bg)

    def toggle_dropdown(self, event):
        if self.dropdown_window:
            self.close_dropdown()
        else:
            self.open_dropdown()

    def open_dropdown(self):
        self.dropdown_window = tk.Toplevel(self)
        self.dropdown_window.wm_overrideredirect(True)
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.height
        self.dropdown_window.geometry(f"{self.width}x{len(self.options)*self.height}+{x}+{y}")
        for index, option in enumerate(self.options):
            lbl = tk.Label(self.dropdown_window, text=option, bg=self.bg, fg=self.fg, font=self.font)
            lbl.place(x=0, y=index*self.height, width=self.width, height=self.height)
            lbl.bind("<Button-1>", lambda e, opt=option: self.select_option(opt))
            lbl.bind("<Enter>", lambda e, widget=lbl: widget.config(bg=self.activebg))
            lbl.bind("<Leave>", lambda e, widget=lbl: widget.config(bg=self.bg))
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

# ---------------- Custom Canvas-Based Scrollbar ----------------
class CustomScrollbar(tk.Canvas):
    def __init__(self, master, target, width=15, **kwargs):
        super().__init__(master, width=width, highlightthickness=0, bd=0, **kwargs)
        self.target = target  # The widget that will be scrolled.
        self._drag_offset = 0  # Offset when dragging the thumb.
        # Save pack options for re-packing when needed.
        self.pack_options = {"side": tk.RIGHT, "fill": tk.Y}
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<Configure>", lambda e: self.update_thumb())
        # Override the target widget's yscrollcommand.
        self.target.config(yscrollcommand=self.on_target_scroll)
        self.first = 0.0
        self.last = 1.0

    def on_target_scroll(self, first, last):
        self.first = float(first)
        self.last = float(last)
        # Show scrollbar only if scrolling is needed.
        if self.first == 0.0 and self.last == 1.0:
            self.pack_forget()
        else:
            if not self.winfo_ismapped():
                self.pack(**self.pack_options)
        self.update_thumb()

    def update_thumb(self):
        self.delete("thumb")
        height = self.winfo_height()
        if height <= 0:
            return
        thumb_start = self.first * height
        thumb_end = self.last * height
        self.create_rectangle(0, thumb_start, self.winfo_width(), thumb_end,
                              fill="#555555", outline="#555555", tags="thumb")

    def on_click(self, event):
        thumb_coords = self.bbox("thumb")
        if thumb_coords and thumb_coords[1] <= event.y <= thumb_coords[3]:
            self._drag_offset = event.y - thumb_coords[1]
        else:
            self.target.yview_moveto(event.y / self.winfo_height())

    def on_drag(self, event):
        height = self.winfo_height()
        new_top = event.y - self._drag_offset
        fraction = new_top / height
        self.target.yview_moveto(fraction)

# ---------------- UI Functions ----------------
def browse_folder(entry):
    folder = filedialog.askdirectory()
    if folder:
        entry.delete(0, tk.END)
        entry.insert(0, folder)
        update_found_files()

def update_extensions_display(new_value=None):
    camera = custom_dropdown.get()
    exts = allowed_extensions.get(camera, [])
    extensions_value_label.config(text=", ".join(exts))
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
    # Force update of scrollbar visibility.
    found_files_text.yview_moveto(found_files_text.yview()[0])

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

# ---------------- Helper Function for Copying Text ---------------- => not needed
def copy_selection(event):
    try:
        # Temporarily enable the widget to retrieve the selection.
        event.widget.config(state=tk.NORMAL)
        selected_text = event.widget.get("sel.first", "sel.last")
        event.widget.clipboard_clear()
        event.widget.clipboard_append(selected_text)
    except tk.TclError:
        pass
    finally:
        # Re-disable the widget to keep it write-only.
        event.widget.config(state=tk.DISABLED)
    return "break"

# ---------------- Build the UI ----------------
root = tk.Tk()
root.title("OCF Metadata JSON Generator")
window_width = 1200
window_height = 550
root.geometry(f"{window_width}x{window_height}")
root.update_idletasks()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width // 2) - (window_width // 2)
y = (screen_height // 2) - (window_height // 2)
root.geometry(f"{window_width}x{window_height}+{x}+{y}")
root.configure(bg="#3A4450")
root.option_add("*Font", "Arial 14")

container = tk.Frame(root, padx=30, pady=30, bg="#3A4450")
container.pack(fill="both", expand=True)

tk.Label(container, text="Source Folder (camera files):", bg="#3A4450", fg="#dddddd").grid(row=0, column=0, padx=5, pady=5, sticky="w")
source_entry = tk.Entry(container, width=100, fg="#bbbbbb",  bg="#2D2F32", highlightbackground="#2D2F32", relief="flat", borderwidth=2, highlightthickness=2)
source_entry.grid(row=0, column=1, padx=5, pady=5)
browse_source_btn = CustomButton(container, text="Browse", command=lambda: browse_folder(source_entry), width=80, height=30, bg="#334A73")
browse_source_btn.grid(row=0, column=2, sticky="e", padx=5, pady=5)

tk.Label(container, text="Destination Folder (JSON files):", bg="#3A4450", fg="#dddddd").grid(row=1, column=0, padx=5, pady=5, sticky="w")
dest_entry = tk.Entry(container, width=100, fg="#bbbbbb",  bg="#2D2F32", highlightbackground="#2D2F32", relief="flat", borderwidth=2, highlightthickness=2)
dest_entry.grid(row=1, column=1, padx=5, pady=5)
browse_dest_btn = CustomButton(container, text="Browse", command=lambda: browse_folder(dest_entry), width=80, height=30, bg="#334A73")
browse_dest_btn.grid(row=1, column=2, sticky="e", padx=5, pady=5)

tk.Label(container, text="Choose Camera Brand:", bg="#3A4450", fg="#dddddd").grid(row=2, column=0, padx=5, pady=5, sticky="w")
custom_dropdown = CustomDropdown(container, options=list(allowed_extensions.keys()), width=80, height=30,
                                 bg="#334A73", fg="#bbbbbb", activebg="#0b5ed7", font=("Arial", 14))
custom_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky="w")

def dropdown_callback(selected):
    update_extensions_display()
custom_dropdown.command = dropdown_callback

allowed_text_label = tk.Label(container, text="Allowed Extensions:", bg="#3A4450", fg="#dddddd")
allowed_text_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")

extensions_value_label = tk.Label(container, text=", ".join(allowed_extensions[custom_dropdown.get()]),
                                  bg="#3A4450", fg="#bbbbbb", font=("Arial", 14))
extensions_value_label.grid(row=3, column=1, padx=5, pady=5, sticky="w")

files_frame = tk.Frame(container)
files_frame.grid(row=4, column=0, columnspan=3, padx=5, pady=35, sticky="nsew")
found_files_text = tk.Text(files_frame, height=10, bg="#282828", fg="#999999",
                           highlightbackground="#282828", relief="flat", borderwidth=2, highlightthickness=2)
found_files_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
# Bind Ctrl+C to allow copying selected text even though the widget is write-only. => not needed
#found_files_text.bind("<Control-c>", copy_selection)
custom_scrollbar = CustomScrollbar(files_frame, found_files_text, width=15, bg="#282828")
custom_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

process_btn = CustomButton(container, text="Process Files", command=process_files, width=100, height=30, bg="#32599C")
process_btn.grid(row=5, column=2, sticky="e", padx=5, pady=20)

container.grid_rowconfigure(5, weight=1)
container.grid_columnconfigure(1, weight=1)

if len(sys.argv) > 1:
    arg_path = sys.argv[1].strip()
    if os.path.isdir(arg_path):
        source_entry.delete(0, tk.END)
        source_entry.insert(0, arg_path)

update_found_files()
root.mainloop()
