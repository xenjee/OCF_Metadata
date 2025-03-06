import os
import OpenImageIO as oiio
import exiftool
import subprocess
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

    # ----------------- OIIO -----------------
    @staticmethod
    def get_oiio_formats():
        """Retrieve supported image formats from OpenImageIO (OIIO)."""
        oiio_formats = oiio.get_string_attribute("format_list")
        return [fmt.strip().lower() for fmt in oiio_formats.split(",")] if oiio_formats else []

    # ----------------- EXIFTOOL -----------------
    @staticmethod
    def get_exiftool_formats():
        """Retrieve supported file formats from ExifTool."""
        with exiftool.ExifTool() as et:
            supported_formats = et.execute("-listf")

            if isinstance(supported_formats, bytes):
                supported_formats = supported_formats.decode("utf-8")

            exiftool_formats_list = []
            capture = False  # Flag to start capturing formats

            for line in supported_formats.split("\n"):
                line = line.strip()

                if line.startswith("Supported file extensions:"):
                    capture = True
                    continue

                if capture and line:
                    exiftool_formats_list.extend(line.split())

            return sorted(set(fmt.strip().lower() for fmt in exiftool_formats_list))

    # ----------------- FFMPEG -----------------
    @staticmethod
    def get_ffmpeg_formats():
        """Retrieve supported file formats from FFmpeg."""
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

    # ----------------- HEIC Metadata Extraction -----------------
    def extract_heic_metadata(self):
        """Extract metadata from the HEIC file."""
        with exiftool.ExifTool() as et:
            metadata_list = et.execute_json(self.file_path)

        if not metadata_list:
            return {"Error": "No metadata found"}

        metadata = metadata_list[0]  # Extract the first dictionary

        print("\n---- HEIC RAW METADATA OUTPUT ----")
        for key, value in metadata.items():
            print(f"{key}: {value}")

        extracted_data = {
            "File Name": metadata.get("File:FileName", "N/A"),
            "Directory": metadata.get("File:Directory", "N/A"),
            "File Size (bytes)": metadata.get("File:FileSize", "N/A"),
            "File Type": metadata.get("File:FileType", "N/A"),
            "MIME Type": metadata.get("File:MIMEType", "N/A"),
            "Image Width": metadata.get(
                "EXIF:ImageWidth",
                metadata.get("QuickTime:ImageSpatialExtent", metadata.get("File:ImageWidth", "N/A"))
            ),
            "Image Height": metadata.get(
                "EXIF:ImageHeight",
                metadata.get("QuickTime:ImageSpatialExtent", metadata.get("File:ImageHeight", "N/A"))
            ),
            "Camera Make": metadata.get(
                "EXIF:Make",
                metadata.get("QuickTime:Make", "N/A")
            ),
            "Camera Model": metadata.get(
                "EXIF:Model",
                metadata.get("QuickTime:Model", "N/A")
            ),
            "Date Taken": metadata.get(
                "EXIF:DateTimeOriginal",
                metadata.get("QuickTime:CreateDate", "N/A")
            ),
            "GPS Latitude": metadata.get(
                "EXIF:GPSLatitude",
                metadata.get("QuickTime:GPSLatitude", "N/A")
            ),
            "GPS Longitude": metadata.get(
                "EXIF:GPSLongitude",
                metadata.get("QuickTime:GPSLongitude", "N/A")
            ),
            "Composite Image Size": metadata.get("Composite:ImageSize", "N/A"),
            "Megapixels": metadata.get("Composite:Megapixels", "N/A"),
        }

        return extracted_data

    # ----------------- Display Supported Formats -----------------
    def display_supported_formats(self):
        """Display the supported formats from OIIO, ExifTool, and FFmpeg."""
        print(f"\n{'-' * 15} OIIO {'-' * 15}")
        print(f"OIIO Supported Formats List:\n {self.oiio_formats_list}")

        print(f"\n{'-' * 15} EXIFTOOL {'-' * 15}")
        print(f"ExifTool Supported Formats List:\n {self.exiftool_formats_list}")

        print(f"\n{'-' * 15} FFMPEG {'-' * 15}")
        print(f"FFmpeg Supported Formats List:\n {self.ffmpeg_formats_list}")

        print(f"\n{'-' * 15} COMMON FORMATS (OIIO & ExifTool) {'-' * 15}")
        print(f"Formats supported by BOTH OIIO and ExifTool: \n{self.common_formats_oiio_exiftool}\n")

        print(f"\n{'-' * 15} COMMON FORMATS (ExifTool & FFMPEG) {'-' * 15}")
        print(f"Formats supported by BOTH ExifTool and FFmpeg: \n{self.common_formats_exiftool_ffmpeg}\n")

# ----------------- Start the process -----------------
# Pass the file path to MetadataExtractor when initializing the class
# this part replaces the call that would happen from another script
path01 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample1.heic"
path02 = "/Users/stefan/Documents/easy_paths/image_formats_samples/A_0001C026_220824_064815_a12SQ.mxf"
path03 = "/Users/stefan/Documents/easy_paths/image_formats_samples/alexa-35-awg4-logc4-data.tiff"
path04 = "/Users/stefan/WORK/SOURCE_MEDIA/Camera_samples/5D_with_ML/20201205/dng/M01-0028_C0000/M01-0028_C0000_00000.dng"
path05 = "/Users/stefan/WORK/SOURCE_MEDIA/Images_elements/Logik_Logo.png"
path06 = "/Users/stefan/WORK/SOURCE_MEDIA/PROCESS_SCREEN/GREENSCREEN/green_key_004.mov"
file_path = path01

# Clear the terminal
os.system('cls' if os.name == 'nt' else 'clear')


extractor = MetadataExtractor(file_path)

# Display Supported Formats
extractor.display_supported_formats()

# Extract HEIC Metadata and Print
metadata = extractor.extract_heic_metadata()
print(f"\n{'-' * 15} HEIC SELECTED METADATA {'-' * 15}")
for key, value in metadata.items():
    print(f"{key}: {value}")


"""
to chatgpt:
while keeping all functionalities from the attached script, add the following functionalities:
- ability to extract the metadata of passed files (of various formats) as dictionaries, using the 3 different tools  (oiio, ffmpeg, exiftool) when they support the file extension.
- print the retrieved data per tool
- ability to extract and print a selection of metadata, using the 3 different tools  (oiio, ffmpeg, exiftool) when they support the file extension
"""