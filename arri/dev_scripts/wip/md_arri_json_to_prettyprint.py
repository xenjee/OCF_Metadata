import json

# Load the JSON file
file_path = "/Users/stefan/Documents/easy_paths/metadata_easy_path/arri/dev_scripts/A_0001C016_220824_063330_p12SQ_metadata_export_shortlut.json"

with open(file_path, "r") as file:
    data = json.load(file)

# Function to recursively remove specified keys from a dictionary
def remove_keys(d, keys):
    if isinstance(d, dict):
        return {k: remove_keys(v, keys) for k, v in d.items() if k not in keys}
    elif isinstance(d, list):
        return [remove_keys(i, keys) for i in d]
    else:
        return d

# Keys to remove
keys_to_remove = {"nativeSoundEssenceDescriptorList", "nativePictureEssenceProcessingSubdescriptor"}

# Remove unwanted keys from the data
filtered_data = remove_keys(data, keys_to_remove)

# Function to filter out unwanted metadata sets
def filter_metadata_sets(metadata_sets, ignore_list):
    return {
        entry["metadataSetName"]: entry["metadataSetPayload"]
        for entry in metadata_sets
        if "metadataSetName" in entry and "metadataSetPayload" in entry and entry["metadataSetName"] not in ignore_list
    }

# Define sections to ignore
ignore_sections = {"Audio", "Texture", "Checksum"}

# Extract and filter 'descriptiveMetadataSets' and 'clipBasedMetadataSets'
descriptive_metadata_sets = filtered_data.get("descriptiveMetadataSets", [])
clip_based_metadata_sets = filtered_data.get("clipBasedMetadataSets", [])

filtered_clip_based_metadata = filter_metadata_sets(clip_based_metadata_sets, ignore_sections)
filtered_descriptive_metadata = filter_metadata_sets(descriptive_metadata_sets, ignore_sections)

# Extract 'frameBasedMetadata' section and filter only 'frameId': 0
frame_metadata = filtered_data.get("frameBasedMetadata", {}).get("frames", [])
frame_0_metadata = next((frame for frame in frame_metadata if frame.get("frameId") == 0), None)
frame_based_metadata_sets = frame_0_metadata.get("frameBasedMetadataSets", {}) if frame_0_metadata else {}

# Remove LUT 3D binary data and format LUT 3D metadata in a human-friendly way
def clean_lut_3d(metadata):
    if "Color" in metadata and "lut3D" in metadata["Color"]:
        lut_entries = metadata["Color"]["lut3D"]
        metadata["Color"]["lut3D"] = {
            f"LUT {i+1}": (
                f"LUT ID: {entry['lut3DID']}, Mesh Points: {entry['lut3DMeshPoints']}, Scaling Factor: {entry['lut3DScalingFactor']}, "
                f"Normalization (Gain: {entry['lut3DNormalization']['gain']}, Offset: {entry['lut3DNormalization']['offset']}), "
                f"Source Color Space: {entry['lut3DSourceColorSpace']['primaries']} - {entry['lut3DSourceColorSpace']['transferCurve']} ({entry['lut3DSourceColorSpace']['whitePoint']}), "
                f"Target Color Space: {entry['lut3DTargetColorSpace']['primaries']} - {entry['lut3DTargetColorSpace']['transferCurve']} ({entry['lut3DTargetColorSpace']['whitePoint']})"
            ) for i, entry in enumerate(lut_entries)
        }
    return metadata

# Format MXF Generic Data
if "MXF Generic Data" in filtered_data:
    mxf_data = filtered_data["MXF Generic Data"]
    if "nativeIdentificationList" in mxf_data:
        identification_entry = mxf_data["nativeIdentificationList"][0]
        mxf_data["nativeIdentificationList"] = {
            "Company Name": identification_entry.get("companyName", ""),
            "Modification Date": identification_entry.get("modificationDate", ""),
            "Product Name": identification_entry.get("productName", ""),
            "Product UID": identification_entry.get("productUid", ""),
            "This Generation UID": identification_entry.get("thisGenerationUid", ""),
            "Toolkit Version": identification_entry.get("toolkitVersion", ""),
            "Version String": identification_entry.get("versionString", "")
        }
    if "nativeLutThreeDList" in mxf_data:
        mxf_data["nativeLutThreeDList"] = {
            f"LUT {i+1}": f"Identifier: {entry['lutThreeDIdentifier']}, Layout: {entry['lut3dDataLayout']}"
            for i, entry in enumerate(mxf_data["nativeLutThreeDList"])
        }
    filtered_data["MXF Generic Data"] = mxf_data

filtered_clip_based_metadata = clean_lut_3d(filtered_clip_based_metadata)
filtered_frame_based_metadata = clean_lut_3d(frame_based_metadata_sets)

# Function to format dictionaries in a human-readable way
def format_dict(d, indent=0):
    formatted_str = ""
    for key, value in d.items():
        if isinstance(value, dict):
            formatted_str += f"{'  ' * indent}{key}:\n{format_dict(value, indent + 1)}"
        elif isinstance(value, list):
            formatted_str += f"{'  ' * indent}{key}:\n"
            for item in value:
                if isinstance(item, dict):
                    formatted_str += f"{format_dict(item, indent + 1)}"
                else:
                    formatted_str += f"{'  ' * (indent + 1)}- {item}\n"
        else:
            formatted_str += f"{'  ' * indent}{key}: {value}\n"
    return formatted_str

# Print all extracted metadata sections in a human-readable format
output_str = "Extracted Metadata Dictionary:\n"

# Clip-Based Metadata
output_str += "\nClip-Based Metadata:\n"
for k, v in filtered_clip_based_metadata.items():
    output_str += f"\n{k}:\n"
    output_str += format_dict(v, indent=1)

# Descriptive Metadata
output_str += "\nDescriptive Metadata:\n"
for k, v in filtered_descriptive_metadata.items():
    output_str += f"\n{k}:\n"
    output_str += format_dict(v, indent=1)

# Frame-Based Metadata (Frame ID: 0)
output_str += "\nFrame-Based Metadata (Frame ID: 0):\n"
for k, v in filtered_frame_based_metadata.items():
    output_str += f"\n{k}:\n"
    output_str += format_dict(v, indent=1)

# MXF Generic Data
output_str += "\nMXF Generic Data:\n"
output_str += format_dict(filtered_data.get("MXF Generic Data", {}), indent=1)

# Display the formatted output
print(output_str)
