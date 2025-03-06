import OpenImageIO as oiio
import os

# Load OCIO configuration
ocio_config = oiio.ColorConfig()

# Get available color spaces
available_colorspaces = ocio_config.getColorSpaceNames()

os.system('cls' if os.name == 'nt' else 'clear')
print("Available OCIO color spaces:", available_colorspaces)

