import os
import json
from .extract_ocf_metadata import ExtractOCFMetadata

class SaveJsonMetadata(ExtractOCFMetadata):
    def __init__(self, filepath=None):
        super().__init__(filepath)

    def save(self, dest_folder):
        """
        Dummy save method:
         - Calls self.extract() to get metadata
         - Saves the metadata to a JSON file in dest_folder.
           The output file uses the source file’s basename (without extension) + '.json'
        """
        metadata = self.extract()
        base_name = os.path.splitext(os.path.basename(self.filepath))[0]
        json_file_path = os.path.join(dest_folder, base_name + ".json")
        with open(json_file_path, 'w') as f:
            json.dump(metadata, f, indent=4)
        return json_file_path
