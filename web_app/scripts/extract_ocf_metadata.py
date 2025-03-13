import os
import subprocess
import json

class ExtractOCFMetadata:
    def __init__(self, filepath=None, camera_brand=None):
        self.filepath = filepath
        self.camera_brand = camera_brand

    def extract(self):
        if self.camera_brand == "ARRI":
            return self.extract_for_arri()
        elif self.camera_brand == "RED":
            # For RED, extraction is handled in save() via extract_for_red(dest_folder)
            return {}
        elif self.camera_brand == "SONY":
            return self.extract_for_sony()
        else:
            return {"metadata": "No recognized camera brand"}

    def extract_for_arri(self):
        art_cmd_bin = "/Users/stefan/WORK/DEV/metadata/art-cmd_0.3.0_macos_universal/bin/art-cmd"
        file_dir = os.path.dirname(self.filepath)
        base_name = os.path.splitext(os.path.basename(self.filepath))[0]
        tmp_json = os.path.join(file_dir, base_name + "_metadata_export.json")
        cmd = [art_cmd_bin, "export", self.filepath, "--output", tmp_json]
        try:
            completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if completed.stderr:
                print("art-cmd stderr:", completed.stderr)
            if not os.path.isfile(tmp_json):
                print(f"art-cmd reported success, but no file was created at {tmp_json}")
                return {}
            with open(tmp_json, 'r') as f:
                metadata = json.load(f)
            return metadata
        except subprocess.CalledProcessError as e:
            print(f"Error running art-cmd for ARRI: {e}")
            print("stdout:", e.stdout)
            print("stderr:", e.stderr)
            return {}

    def extract_for_red(self, dest_folder):
        """
        Uses REDline to extract metadata using --printMeta 1.
        The command is:
            REDline --i <source_file> --printMeta 1 > <dest_folder>/<base_name>_metadata_export.txt
        This method runs the command with shell redirection so that a text file is created.
        Then it reads and parses that text file (assuming each line is "Key: Value")
        into a dictionary and returns it.
        """
        base_name = os.path.splitext(os.path.basename(self.filepath))[0]
        out_file = os.path.join(dest_folder, base_name + "_metadata_export.txt")
        cmd = f'REDline --i "{self.filepath}" --printMeta 1 > "{out_file}"'
        try:
            # Run command with shell=True to allow redirection
            completed = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            if not os.path.isfile(out_file):
                print(f"REDline reported success, but no file was created at {out_file}")
                return {}
            # Read the text file
            with open(out_file, "r") as f:
                lines = f.readlines()
            metadata = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()
            metadata["method"] = "REDline"
            metadata["filepath"] = self.filepath
            # The text file remains on disk; you can delete it if desired:
            # os.remove(out_file)
            return metadata
        except subprocess.CalledProcessError as e:
            print(f"Error running REDline: {e}")
            print("stderr:", e.stderr)
            return {}

    def extract_for_sony(self):
        # Dummy extraction logic for SONY
        return {"method": "dummy", "filepath": self.filepath, "metadata": "dummy SONY metadata"}
