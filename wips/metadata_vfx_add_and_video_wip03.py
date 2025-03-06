import os
import shutil
import OpenImageIO as oiio
import subprocess
import re

class VFXMetadataProcessor:
    def __init__(self, path, metadata=None, burn_in=False, apply_aces=False):
        self.path = path
        self.metadata = metadata if metadata else {}
        self.burn_in = burn_in
        self.apply_aces = apply_aces

    def detect_exr_sequence_pattern(self):
        exr_files = sorted([f for f in os.listdir(self.path) if f.endswith('.exr')])
        if not exr_files:
            raise FileNotFoundError("No EXR files found in the directory.")
    
        match = re.search(r"(.*?)[._](\d+)\.exr$", exr_files[0])
        if match:
            base_name, frame_number = match.groups()
            frame_number_length = len(frame_number)
            return f"{base_name}.%0{frame_number_length}d.exr"
        else:
            raise ValueError("Could not determine EXR sequence pattern.")

    def get_exr_metadata(self, image_path):
        img = oiio.ImageInput.open(image_path)
        if not img:
            return {}
        metadata = img.spec().extra_attribs
        img.close()
        return metadata

    def copy_exr_file(self, original_path):
        copy_path = original_path.replace(".exr", "_copy.exr")
        shutil.copy2(original_path, copy_path)
        print(f"Copied EXR file to: {copy_path}")
        return copy_path

    def inject_metadata(self, exr_path):
        img = oiio.ImageInput.open(exr_path)
        if not img:
            print("Error opening EXR file.")
            return
        
        spec = img.spec()
        pixels = img.read_image()
        img.close()
        
        existing_metadata = {param.name: param.value for param in self.get_exr_metadata(exr_path)}
        for key, value in {**existing_metadata, **self.metadata}.items():
            if isinstance(value, (int, float, str)):
                spec.attribute(key, value)
            elif isinstance(value, tuple) and all(isinstance(v, (int, float)) for v in value):
                spec.attribute(key, oiio.TypeDesc('float'), value)
            else:
                print(f"Skipping unsupported metadata key: {key} with value type: {type(value)}")
        
        output_path = exr_path.replace(".exr", "_metadata.exr")
        img_out = oiio.ImageOutput.create(output_path)
        if not img_out:
            print("Error creating output EXR file.")
            return
        
        img_out.open(output_path, spec)
        img_out.write_image(pixels)
        img_out.close()
        print(f"Metadata injected into: {output_path}")
        return output_path
    
    def print_metadata(self, exr_path):
      metadata = self.get_exr_metadata(exr_path)
      print("Extracted Metadata:")
      for param in metadata:
          print(f"{param.name}: {param.value}")

    def convert_sequence_to_video(self, image_sequence, output_video):

        # Extract start frame number
        start_frame = int(sorted([f for f in os.listdir(self.path) if f.endswith('.exr')])[0].split('.')[-2])

        ffmpeg_cmd = [
          "ffmpeg", "-framerate", "24",
          "-start_number", str(start_frame),
          "-i", image_sequence,
          "-c:v", "prores_ks", "-pix_fmt", "yuv422p10le"
        ]
    
        filter_chain = []
        
        if self.apply_aces:
            filter_chain.append("lut3d=aces_to_rec709.cube")
        
        
        if filter_chain:
            ffmpeg_cmd.extend(["-vf", ",".join(filter_chain)])
            ffmpeg_cmd.extend(["-vf", "lut3d=aces_to_rec709.cube"])
        
        if self.burn_in:
            drawtext = "drawtext=text='Shot: {}': x=100: y=100: fontsize=48: fontcolor=white, ".format(self.metadata.get("title", "Unknown"))
            drawtext += "drawtext=text='Artist: {}': x=110: y=200: fontsize=48: fontcolor=white, ".format(self.metadata.get("artist", "Unknown"))
            drawtext += "drawtext=text='Comment: {}': x=110: y=300: fontsize=48: fontcolor=white, ".format(self.metadata.get("comment", "Unknown"))
            drawtext += "drawtext=text='Version: {}': x=110: y=400: fontsize=48: fontcolor=white, ".format(self.metadata.get("version", "Unknown"))
            ffmpeg_cmd.extend(["-vf", drawtext])
        
        ffmpeg_cmd.extend([
            "-metadata", f"title={self.metadata.get('title', 'Unknown')}",
            "-metadata", f"artist={self.metadata.get('artist', 'Unknown')}",
            "-metadata", f"comment={self.metadata.get('comment', 'No comments')}",
            "-metadata", f"version={self.metadata.get('version', 'v001')}",
            output_video
        ])
        
        print('='*20)
        print(" **** Running FFmpeg command:", " ".join(ffmpeg_cmd))
        print(" **** Files in directory:", os.listdir(os.path.dirname(image_sequence)))
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"Processed video: {output_video}")
        
        # Cleanup temporary files
        for temp_file in getattr(self, 'self.copied_files', []):
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"Deleted temporary file: {temp_file}")
        
        # Cleanup temporary files
        for temp_file in self.copied_files:
            if os.path.exists(temp_file):
              os.remove(temp_file)
              print(f"Deleted temporary file: {temp_file}")
        
    def process(self):
        self.copied_files = []
        if os.path.isdir(self.path):
            exr_files = sorted([f for f in os.listdir(self.path) if f.endswith(".exr")])
            if not exr_files:
                print("No EXR files found!")
                return

            first_exr = os.path.join(self.path, exr_files[0])
            copied_exr = self.copy_exr_file(first_exr)
            self.copied_files.append(copied_exr)
            metadata_exr = self.inject_metadata(copied_exr)
            self.copied_files.append(metadata_exr)
            self.print_metadata(metadata_exr)

            exr_sequence = os.path.join(self.path, self.detect_exr_sequence_pattern())
            print(f"Detected EXR sequence pattern: {exr_sequence}")

            output_video = os.path.join(self.path, f"{self.metadata.get('title', 'output')}_review.mov")

            self.convert_sequence_to_video(exr_sequence, output_video)
        else:
            print("Invalid path provided. Please provide a directory containing EXR files.")

# Example usage
path01 = "/Users/stefan/Documents/easy_paths/metadata_easy_path/files_for_testing/original/"
path02 = "/Users/stefan/Documents/easy_paths/metadata_easy_path/files_for_testing/UFO_0090_lgt_v35_char_BTY/"
folder_path = path02
metadata = {
    "title": "UFO_0090",
    "artist": "VFX Artist",
    "comment": "Final composited version",
    "version": "v035"
}

os.system('cls' if os.name == 'nt' else 'clear')

processor = VFXMetadataProcessor(folder_path, metadata, burn_in=True, apply_aces=True)
processor.process()
