import os
import shutil
import OpenImageIO as oiio
import subprocess

class VFXMetadataProcessor:
    def __init__(self, path, metadata=None, burn_in=False, apply_aces=False):
        self.path = path
        self.metadata = metadata if metadata else {}
        self.burn_in = burn_in
        self.apply_aces = apply_aces

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
        
        for key, value in self.metadata.items():
            spec.attribute(key, value)
        
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
        ffmpeg_cmd = [
            "ffmpeg", "-framerate", "24", "-i", image_sequence,
            "-c:v", "prores_ks", "-pix_fmt", "yuv422p10le"
        ]
        
        if self.apply_aces:
            ffmpeg_cmd.extend(["-vf", "lut3d=aces_to_rec709.cube"])
        
        if self.burn_in:
            drawtext = "drawtext=text='Shot: {}': x=10: y=10: fontsize=24: fontcolor=white, ".format(self.metadata.get("title", "Unknown"))
            drawtext += "drawtext=text='Artist: {}': x=10: y=50: fontsize=24: fontcolor=white, ".format(self.metadata.get("artist", "Unknown"))
            drawtext += "drawtext=text='Version: {}': x=10: y=90: fontsize=24: fontcolor=white"
            ffmpeg_cmd.extend(["-vf", drawtext])
        
        ffmpeg_cmd.extend([
            "-metadata", f"title={self.metadata.get('title', 'Unknown')}",
            "-metadata", f"artist={self.metadata.get('artist', 'Unknown')}",
            "-metadata", f"comment={self.metadata.get('comment', 'No comments')}",
            "-metadata", f"version={self.metadata.get('version', 'v001')}",
            output_video
        ])
        
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"Processed video: {output_video}")

    def process(self):
        if os.path.isdir(self.path):
            exr_files = sorted([f for f in os.listdir(self.path) if f.endswith(".exr")])
            if not exr_files:
                print("No EXR files found!")
                return

            first_exr = os.path.join(self.path, exr_files[0])
            copied_exr = self.copy_exr_file(first_exr)
            metadata_exr = self.inject_metadata(copied_exr)
            self.print_metadata(metadata_exr)

            exr_sequence = os.path.join(self.path, sorted([f for f in os.listdir(self.path) if f.endswith('.exr')])[0])
            output_video = os.path.join(self.path, f"{self.metadata.get('title', 'output')}_review.mov")

            self.convert_sequence_to_video(exr_sequence, output_video)
        else:
            print("Invalid path provided. Please provide a directory containing EXR files.")

# Example usage
folder_path = "/Users/stefan/Documents/easy_paths/metadata_easy_path/source_images/original/"
metadata = {
    "title": "Sample_Shot",
    "artist": "VFX Artist",
    "comment": "Final composited version",
    "version": "v001"
}
processor = VFXMetadataProcessor(folder_path, metadata, burn_in=True, apply_aces=True)
processor.process()
