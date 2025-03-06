import OpenEXR
import Imath
import json
import xml.etree.ElementTree as ET
from pymediainfo import MediaInfo
import os

def extract_metadata_from_mxf(mxf_file):
    """
    Extracts metadata from an ARRI MXF file using pymediainfo.
    Returns a dictionary of relevant metadata.
    pymediainfo or  MediaInfo app don't see much of the mxf metadata: useless
    """
    metadata = {}
    media_info = MediaInfo.parse(mxf_file)

    for track in media_info.tracks:
        if track.track_type == "Video":
            metadata["Color Space"] = track.color_space if track.color_space else "Unknown"
            metadata["Frame Rate"] = track.frame_rate if track.frame_rate else "Unknown"
            metadata["Bit Depth"] = track.bit_depth if track.bit_depth else "Unknown"
            metadata["Width"] = track.width
            metadata["Height"] = track.height

    return metadata

def extract_metadata_from_xml(xml_file):
    """
    Parses ARRI XML metadata for additional details.
    Returns a dictionary of extracted metadata.
    """
    metadata = {}
    tree = ET.parse(xml_file)
    root = tree.getroot()

    for elem in root.iter():
        if elem.tag in ["CameraModel", "ISO", "ExposureIndex", "FocalLength", "ShutterAngle"]:
            metadata[elem.tag] = elem.text

    return metadata

def inject_metadata_into_exr(exr_file, metadata):
    """
    Injects extracted metadata into an EXR file using OpenEXR.
    """
    if not os.path.exists(exr_file):
        print(f"❌ ERROR: EXR file {exr_file} not found!")
        return

    # Read the EXR header
    exr = OpenEXR.InputFile(exr_file)
    header = exr.header()

    # Convert metadata values to strings
    for key, value in metadata.items():
        header[key] = str(value)

    # Write the updated EXR file
    out_exr = OpenEXR.OutputFile(exr_file.replace(".exr", "_with_metadata.exr"), header)
    out_exr.close()
    print(f"✅ Metadata injected into {exr_file.replace('.exr', '_with_metadata.exr')}")

def batch_process_mxf_to_exr(mxf_folder, exr_folder):
    """
    Processes all MXF and corresponding EXR files in given folders.
    Extracts metadata from MXF and injects into EXR files.
    """
    for mxf_file in os.listdir(mxf_folder):
        if mxf_file.endswith(".mxf"):
            mxf_path = os.path.join(mxf_folder, mxf_file)
            exr_filename = os.path.splitext(mxf_file)[0] + ".exr"
            exr_path = os.path.join(exr_folder, exr_filename)

            print(f"📂 Processing {mxf_file} → {exr_filename}...")

            # Extract metadata from MXF
            metadata = extract_metadata_from_mxf(mxf_path)
            print(f"Metadata: {metadata}")

            # Look for corresponding ARRI XML metadata
            xml_filename = os.path.splitext(mxf_file)[0] + ".xml"
            xml_path = os.path.join(mxf_folder, xml_filename)

            if os.path.exists(xml_path):
                metadata.update(extract_metadata_from_xml(xml_path))
                

            # Inject metadata into EXR
            #inject_metadata_into_exr(exr_path, metadata)

# Example usage
mxf_folder = "/Users/stefan/WORK/SOURCE_MEDIA/Camera_samples/ARRI/logC4/mxf_arriraw/"
exr_folder = "/path/to/exr_folder"
batch_process_mxf_to_exr(mxf_folder, exr_folder)
