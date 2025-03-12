import os

class ExtractOCFMetadata:
    def __init__(self, filepath=None):
        self.filepath = filepath

    def extract(self):
        """
        Dummy implementation that returns a dict.
        In a real scenario, this would parse the file and extract OCF metadata.
        """
        if not self.filepath:
            return {}
        return {
            "filename": os.path.basename(self.filepath),
            "metadata": "dummy metadata content"
        }
