import os
import json
from .extract_ocf_metadata import ExtractOCFMetadata

class SaveJsonMetadata(ExtractOCFMetadata):
    def __init__(self, filepath=None, camera_brand=None):
        super().__init__(filepath, camera_brand)

    def save(self, dest_folder):
        """
        - Ensures dest_folder exists.
        - For RED files, calls extract_for_red(dest_folder) to run REDline and capture its output in a text file.
          For other brands, calls extract().
        - Writes the resulting metadata dictionary to a JSON file in dest_folder.
        - Returns the path to the created JSON file.
        """
        os.makedirs(dest_folder, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(self.filepath))[0]
        
        if self.camera_brand == "RED":
            metadata = self.extract_for_red(dest_folder)
        else:
            metadata = self.extract()
        
        json_file_path = os.path.join(dest_folder, base_name + ".json")
        try:
            with open(json_file_path, 'w') as f:
                json.dump(metadata, f, indent=4)
            return json_file_path
        except Exception as e:
            print(f"Error writing JSON file: {e}")
            return None
