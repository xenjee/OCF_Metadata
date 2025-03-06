import os
import OpenImageIO as oiio
import exiftool
import subprocess
import json
import re

class MetadataExtractor:
    def __init__(self, file_path):
        """Initialize MetadataExtractor with a specific file path."""
        self.file_path = file_path
        self.oiio_formats_list = self.get_oiio_formats()
        self.exiftool_formats_list = self.get_exiftool_formats()
        self.ffmpeg_formats_list = self.get_ffmpeg_formats()
        self.common_formats_oiio_exiftool = sorted(set(self.oiio_formats_list) & set(self.exiftool_formats_list))
        self.common_formats_exiftool_ffmpeg = sorted(set(self.exiftool_formats_list) & set(self.ffmpeg_formats_list))

    @staticmethod
    def get_oiio_formats():
        oiio_formats = oiio.get_string_attribute("format_list")
        return [fmt.strip().lower() for fmt in oiio_formats.split(",")] if oiio_formats else []

    @staticmethod
    def get_exiftool_formats():
        with exiftool.ExifTool() as et:
            supported_formats = et.execute("-listf")
            if isinstance(supported_formats, bytes):
                supported_formats = supported_formats.decode("utf-8")

            exiftool_formats_list = []
            capture = False
            for line in supported_formats.split("\n"):
                line = line.strip()
                if line.startswith("Supported file extensions:"):
                    capture = True
                    continue
                if capture and line:
                    exiftool_formats_list.extend(line.split())

            return sorted(set(fmt.strip().lower() for fmt in exiftool_formats_list))

    @staticmethod
    def get_ffmpeg_formats():
        try:
            ffmpeg_output = subprocess.run(["ffmpeg", "-formats"], capture_output=True, text=True)
            ffmpeg_formats_list = []
            for line in ffmpeg_output.stdout.split("\n"):
                line = line.strip()
                match = re.match(r"^\s*[DE]\s+([\w,]+)", line)
                if match:
                    formats = match.group(1).split(",")
                    ffmpeg_formats_list.extend([fmt.lower().strip() for fmt in formats])
            return sorted(set(ffmpeg_formats_list))
        except Exception as e:
            print("\nError retrieving FFmpeg formats:", str(e))
            return []

    # ----------------- Display Supported Formats -----------------
    def display_supported_formats(self):
        """Display the supported formats from OIIO, ExifTool, and FFmpeg."""
        print(f"\n{'-'*10}")
        print(f"🔹 **OIIO**")
        print(f"OIIO Supported Formats List:\n {self.oiio_formats_list}")

        print(f"\n{'-'*10}")
        print(f"🔹 **EXIFTOOL**")
        print(f"ExifTool Supported Formats List:\n {self.exiftool_formats_list}")

        print(f"\n{'-'*10}")
        print(f"🔹 **FFMPEG**")
        print(f"FFmpeg Supported Formats List:\n {self.ffmpeg_formats_list}")

        print(f"\n{'-'*10}")
        print(f"🔹 **COMMON FORMATS (OIIO & ExifTool)**")
        print(f"Formats supported by BOTH OIIO and ExifTool: \n{self.common_formats_oiio_exiftool}\n")

        print(f"\n{'-'*10}")
        print(f"🔹 **COMMON FORMATS (ExifTool & FFMPEG)**")
        print(f"Formats supported by BOTH ExifTool and FFmpeg: \n{self.common_formats_exiftool_ffmpeg}\n")


    def extract_metadata(self):
        file_extension = os.path.splitext(self.file_path)[1][1:].lower()
        metadata_results = {}

        if file_extension in self.oiio_formats_list:
            image = oiio.ImageInput.open(self.file_path)
            if image:
                spec = image.spec()
                metadata_results['OIIO'] = {str(a.name): str(a.value) for a in spec.extra_attribs}
                image.close()
            else:
                metadata_results['OIIO'] = "OIIO does not support this file format."
        else:
            metadata_results['OIIO'] = "OIIO does not support this file format."

        if file_extension in self.exiftool_formats_list:
            with exiftool.ExifTool() as et:
                metadata_list = et.execute_json(self.file_path)
                metadata_results['ExifTool'] = metadata_list[0] if metadata_list else "ExifTool could not extract metadata."
        else:
            metadata_results['ExifTool'] = "ExifTool does not support this file format."

        if file_extension in self.ffmpeg_formats_list:
            try:
                ffmpeg_output = subprocess.run(["ffprobe", "-show_format", "-show_streams", "-print_format", "json", self.file_path],
                                               capture_output=True, text=True)
                metadata_results['FFmpeg'] = json.loads(ffmpeg_output.stdout) if ffmpeg_output.stdout else {}
            except Exception as e:
                metadata_results['FFmpeg'] = {"Error": str(e)}
        else:
            metadata_results['FFmpeg'] = "FFmpeg does not support this file format."

        return metadata_results

    def print_metadata(self):
        metadata = self.extract_metadata()
        for tool, data in metadata.items():
            print(f"\n{'-'*10}")
            print(f"🔹 **{tool} METADATA**")
            if isinstance(data, str):
                print(data)
            else:
                if tool == 'FFmpeg' and isinstance(data, dict):
                    for section, values in data.items():
                        if isinstance(values, list):
                            for index, entry in enumerate(values):
                                print(f"\n[{section.upper()} #{index}]")
                                for key, value in entry.items():
                                    if isinstance(value, dict):
                                        print(f"{key}:")
                                        for sub_key, sub_value in value.items():
                                            print(f"  {sub_key}: {sub_value}")
                                    else:
                                        print(f"{key}: {value}")
                        elif isinstance(values, dict):
                            print(f"\n[{section.upper()}]")
                            for key, value in values.items():
                                print(f"{key}: {value}")
                else:
                    for key, value in data.items():
                        print(f"{key}: {value}")

    def extract_selected_metadata(self, keys):
        metadata = self.extract_metadata()
        selected_data = {}

        for tool, data in metadata.items():
            selected_data[tool] = {}
            if isinstance(data, dict):
                for key in keys:
                    key_lower = key.replace(" ", "").lower()
                    for existing_key, value in data.items():
                        formatted_key = existing_key.replace(" ", "").lower()
                        if key_lower in formatted_key:
                            selected_data[tool][existing_key] = value

                if tool == 'FFmpeg':
                    if 'streams' in data:
                        for stream in data['streams']:
                            for key in keys:
                                if key in stream:
                                    selected_data[tool][key] = stream[key]
                    if 'format' in data:
                        for key in keys:
                            if key in data['format']:
                                selected_data[tool][key] = data['format'][key]
        return selected_data


# Example Usage
path01 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample1.heic"
path02 = "/Users/stefan/Documents/easy_paths/image_formats_samples/A_0001C026_220824_064815_a12SQ.mxf"
path03 = "/Users/stefan/Documents/easy_paths/image_formats_samples/alexa-35-awg4-logc4-data.tiff"
path04 = "/Users/stefan/WORK/SOURCE_MEDIA/Camera_samples/5D_with_ML/20201205/dng/M01-0028_C0000/M01-0028_C0000_00000.dng"
path05 = "/Users/stefan/WORK/SOURCE_MEDIA/Images_elements/Logik_Logo.png"
path06 = "/Users/stefan/WORK/SOURCE_MEDIA/PROCESS_SCREEN/GREENSCREEN/green_key_004.mov"
path07 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample_640x360.hevc"
path08 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample_640x360.mov"
path09 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample_640x360.mxf"
path10 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample_1280x720_surfing_with_audio.hevc"
path11 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample_640×426_exr.exr"
path12 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample_640×426_hdr.hdr"
path13 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample_640×426_jpeg.jpeg"
path14 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample_640×426_png.png"
path15 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample_640×426_psd.psd"
path16 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample1_cr2.cr2"
path17 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample1_dng.dng"
path18 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample1_heif.heif"
path19 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample_640×426_exr.exr"



file_path = path19 # Change this to choose a different file
os.system('cls' if os.name == 'nt' else 'clear')

extractor = MetadataExtractor(file_path)

print(f"\n{'='*60}")
print("SUPORTED FORMATS")
extractor.display_supported_formats()

print(f"\n{'='*60}")
print("FILE RAW METADATA")
extractor.print_metadata()

selected_metadata = extractor.extract_selected_metadata([
    "File Name", "Image Width", "Image Height", "ChromaFormat", "BitDepthLuma", "Color Space", "color_primaries", "codec_type", "coded_width"
])

print(f"\n{'='*60}")
print(f"FILE SELECTED METADATA")
for tool, data in selected_metadata.items():
    print(f"\n{'-'*10}")
    print(f"🔹 **Requested {tool}**")
    for key, value in data.items():
        print(f"{key}: {value}")
    
