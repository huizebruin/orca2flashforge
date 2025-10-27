# orca2flashforge

orca2flashforge is a universal post-process script for OrcaSlicer, which restores FlashForge specific metadata

## What It Does

This script restructures G-code files from OrcaSlicer to match the format expected by FlashForge printers and their API. Without this conversion, the printer won't display the information, and it won't populate in the HTTP API

### Restored Information

The conversion ensures the printer correctly recognizes the following info:

- **Estimated Print Time (ETA)** - Time remaining and total print duration
- **Filament Usage** - Amount used in mm, cm³, grams, and cost
- **Layer Count** - Total layers and current layer progress
- **Print Settings** - Infill percentage, print speeds, layer height
- **Temperature Settings** - Nozzle and bed temperatures
- **Printer Configuration** - All slicer settings and parameters

## Installation

1. Clone or download this repository
2. Ensure Python 3.6+ is installed

## Setup
> OrcaSlicer documentation [here](https://github.com/SoftFever/OrcaSlicer/wiki/others_settings_post_processing_scripts)


(path to python) (path to convert.py)

<img width="608" height="582" alt="image" src="https://github.com/user-attachments/assets/9919c016-2519-42c0-8c43-81dd26662fb5" />

Save settings. The script will automatically run after every slice.
