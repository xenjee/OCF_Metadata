import os
import sys
sys.path.append(os.path.split(os.path.dirname(os.path.abspath(__file__)))[0])
from get_metadata import MetadataExtractor



# Example Usage
path01 = "/Users/stefan/Documents/easy_paths/image_formats_samples/sample1.heic"
path02 = "/Users/stefan/WORK/SOURCE_MEDIA/Camera_samples/ARRI/logC4/mxf_arriraw/A_0001C026_220824_064815_a12SQ.mxf"
path02b = "/Users/stefan/WORK/SOURCE_MEDIA/Camera_samples/ARRI/logC4/mxf_arriraw/A_0001C019_220824_063814_a12SQ.mxf"
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
path20 = "/Users/stefan/Documents/easy_paths/image_formats_samples/UFO_0090_review.mov"
path21 = "/Users/stefan/WORK/SOURCE_MEDIA/Camera_samples/RED/B004_C010_01232H_a001.R3D"
path22 = "/Users/stefan/WORK/SOURCE_MEDIA/Camera_samples/RED/Komodo_6k/A002_C316_0523F5.RDC/A002_C316_0523F5_001.R3D"
path23 = "/Volumes/CGI/R_n_D/colorManagement/cameraSamples/Sony/Venice2/VENICE_2_8K 1.8x_Anamorphic.mxf"


file_path = path23  # Change this to choose a different file
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

