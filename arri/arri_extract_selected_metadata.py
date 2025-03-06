import json

# Load the JSON file
file_path = "/Users/stefan/Documents/easy_paths/metadata_easy_path/arri/arri_mxf_library/A_0001C016_220824_063330_p12SQ_metadata_export_stripped.json"

with open(file_path, "r") as file:
    data = json.load(file)

# Extract 'descriptiveMetadataSets' and 'clipBasedMetadataSets'
descriptive_metadata_sets = data.get("descriptiveMetadataSets", [])
clip_based_metadata_sets = data.get("clipBasedMetadataSets", [])

# Process 'clipBasedMetadataSets' without 'metadataSetSchemaUri'
filtered_clip_based_metadata = {
    entry["metadataSetName"]: entry["metadataSetPayload"]
    for entry in clip_based_metadata_sets if "metadataSetName" in entry and "metadataSetPayload" in entry
}

# Process 'descriptiveMetadataSets' without 'metadataSetSchemaUri'
filtered_descriptive_metadata = {
    entry["metadataSetName"]: entry["metadataSetPayload"]
    for entry in descriptive_metadata_sets if "metadataSetName" in entry and "metadataSetPayload" in entry
}

# Extract 'frameBasedMetadata' section and filter only 'frameId': 0
frame_metadata = data.get("frameBasedMetadata", {}).get("frames", [])
frame_0_metadata = next((frame for frame in frame_metadata if frame.get("frameId") == 0), None)
frame_based_metadata_sets = frame_0_metadata.get("frameBasedMetadataSets", {}) if frame_0_metadata else {}


def format_dict(d, indent=0):
    """
    Recursively formats a dictionary in a human-friendly way with proper indentation.
    - Nested dictionaries increase indentation for readability.
    """
    formatted_str = ""
    for key, value in d.items():
        if isinstance(value, dict):
            formatted_str += f"{'  ' * indent}{key}:\n{format_dict(value, indent + 1)}"
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
for k, v in frame_based_metadata_sets.items():
    output_str += f"\n{k}:\n"
    output_str += format_dict(v, indent=1)

# Display the formatted output
print(output_str)
