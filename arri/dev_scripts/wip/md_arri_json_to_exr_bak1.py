import os
import json
import OpenEXR
import sqlite3

class MetadataProcessor:
    """Handles loading, processing, and flattening metadata."""
    def __init__(self, metadata_path):
        self.metadata_path = metadata_path
        self.metadata = self._load_metadata()

    def _load_metadata(self):
        """Loads metadata from a JSON file with error handling."""
        try:
            with open(self.metadata_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading metadata: {e}")
            return {}

    def flatten_dict(self, d, parent_key='', sep='.'):  
        """Recursively flattens a dictionary using dot notation."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, elem in enumerate(v):
                    if isinstance(elem, dict):
                        items.extend(self.flatten_dict(elem, f"{new_key}[{i}]", sep=sep).items())
                    else:
                        items.append((f"{new_key}[{i}]", elem))
            else:
                items.append((new_key, v))
        return dict(items)

    def process_metadata(self):
        """Processes metadata according to required transformations."""
        processed_metadata = {"file_path": self.metadata_path}
        clip_metadata = []

        for entry in self.metadata.get("clipBasedMetadataSets", []):
            if entry.get("metadataSetName") in ["Texture", "Audio"]:
                continue
            entry.pop("metadataSetSchemaUri", None)
            if "lut3D" in entry.get("metadataSetPayload", {}):
                for lut in entry["metadataSetPayload"]["lut3D"]:
                    lut["lut3DData"] = "lut3d data as base64"
            clip_metadata.append(entry)
        processed_metadata["clipBasedMetadataSets"] = clip_metadata

        processed_metadata["descriptiveMetadataSets"] = [
            {k: v for k, v in entry.items() if k != "metadataSetSchemaUri"}
            for entry in self.metadata.get("descriptiveMetadataSets", [])
        ]

        if "frameBasedMetadata" in self.metadata:
            frame_metadata = self.metadata["frameBasedMetadata"]
            for frame in frame_metadata.get("frames", []):
                for metadata_set in frame.get("frameBasedMetadataSets", {}).values():
                    metadata_set.pop("metadataSetSchemaUri", None)
            processed_metadata["frameBasedMetadata"] = frame_metadata

        return self.flatten_dict(processed_metadata)


class EXRMetadataProcessor:
    """Handles embedding metadata into an EXR file."""
    def __init__(self, flattened_metadata):
        self.flattened_metadata = flattened_metadata

    def format_metadata_to_exr_header(self):
        """Creates an EXR header and injects metadata."""
        width = int(self.flattened_metadata.get("clipBasedMetadataSets[1].metadataSetPayload.acquisitionRect.width", 4096))
        height = int(self.flattened_metadata.get("clipBasedMetadataSets[1].metadataSetPayload.acquisitionRect.height", 2160))
        exr_header = OpenEXR.Header(width, height)
        
        for key, value in self.flattened_metadata.items():
            if isinstance(value, str):
                exr_header[key] = value.encode()
            elif isinstance(value, (int, float)):
                exr_header[key] = value
        
        return exr_header


class MetadataDatabase:
    """Handles SQLite database storage for metadata."""
    def __init__(self, sqlite3_db_path):
        self.sqlite3_db_path = sqlite3_db_path
        self._initialize_database()

    def _initialize_database(self):
        """Creates metadata table if it doesn't exist."""
        with sqlite3.connect(self.sqlite3_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    value TEXT
                )
            """)

    def store_metadata(self, flattened_metadata):
        """Stores metadata in the SQLite database."""
        try:
            with sqlite3.connect(self.sqlite3_db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    "INSERT INTO metadata (key, value) VALUES (?, ?)",
                    [(key, str(value)) for key, value in flattened_metadata.items()]
                )
            print(f"Metadata successfully stored in {self.sqlite3_db_path}")
        except sqlite3.Error as e:
            print(f"Error storing metadata in database: {e}")


class MetadataExporter:
    """Handles printing and exporting metadata in different formats."""
    def __init__(self, text_output_file, html_output_file):
        self.text_output_file = text_output_file
        self.html_output_file = html_output_file

    def print_colored_exr_metadata(self, exr_header):
        """Prints EXR metadata keys with color-coded levels using ANSI escape codes."""
        # colors = ["\033[92m",  "\033[94m", "\033[91m", "\033[93m",  "\033[95m", "\033[96m", "\033[97m"]
        colors = ["\033[92m",  "\033[94m", "\033[91m", "\033[93m",  "\033[95m", "\033[93m", "\033[97m"]
        reset_color = "\033[0m"
        
        for key, value in exr_header.items():
            parts = key.split(".")
            colored_key = "".join(f"{colors[i % len(colors)]}{part}{reset_color}." for i, part in enumerate(parts))[:-1]
            print(f"{colored_key}: {value}")

    def save_colored_exr_metadata_txt(self, exr_header):
        """Saves EXR metadata keys with color-coded levels using ANSI escape codes to a file."""
        with open(text_output_file, "w") as f:
            for key, value in exr_header.items():
                f.write(f"{key}: {value}\n")
        print(f"Metadata saved to {text_output_file}")

    def save_colored_html_exr_metadata(self, exr_header):
        """Saves EXR metadata keys with color-coded levels as an HTML file."""
        
        html_content = """<html><head><style>
        body { background-color: #333; color: #ddd; font-family: Arial, sans-serif; }
        
        .level0 { color: MediumSeaGreen; }
        .level1 { color: DodgerBlue; }
        .level2 { color: orange; }
        .level3 { color: yellow; }
        .level4 { color: violet; }
        .level5 { color: yellow; }
        .level6 { color: black; }
        </style></head><body>
        <h1>EXR Metadata</h1>
        <ul>"""
        
        for key, value in exr_header.items():
            parts = key.split(".")
            colored_parts = [f'<span class="level{i}">{part}</span>' for i, part in enumerate(parts)]
            colored_key = " . ".join(colored_parts)
            html_content += f"<li>{colored_key}: <strong>{value}</strong></li>"
        
        html_content += "</ul></body></html>"
        
        with open(html_output_file, "w") as f:
            f.write(html_content)
        print(f"Metadata saved to {html_output_file}")

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    metadata_path = "/Users/stefan/Documents/easy_paths/metadata_easy_path/arri/dev_scripts/A_0001C016_220824_063330_p12SQ_metadata_export_shortlut.json"
    sqlite3_db_path = os.path.join(script_dir, "ocf_metadata.db")
    text_output_file = os.path.join(script_dir, "ocf_metadata.txt")
    html_output_file = os.path.join(script_dir, "ocf_metadata.html")
    
    processor = MetadataProcessor(metadata_path)
    flattened_metadata = processor.process_metadata()
    
    injector = EXRMetadataProcessor(flattened_metadata)
    exr_header = injector.format_metadata_to_exr_header()

    db = MetadataDatabase(sqlite3_db_path)
    db.store_metadata(flattened_metadata)
    
    metadata_exporter = MetadataExporter(text_output_file, html_output_file)
    metadata_exporter.print_colored_exr_metadata(exr_header)
    metadata_exporter.save_colored_exr_metadata_txt(exr_header)
    metadata_exporter.save_colored_html_exr_metadata(exr_header)
