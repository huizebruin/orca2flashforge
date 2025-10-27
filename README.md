# OrcaSlicer to FlashForge G-code Converter

Post-processing script for OrcaSlicer that converts G-code to the Orca-FlashForge format, enabling proper metadata display on FlashForge printers.

## What It Does

This script restructures G-code files from OrcaSlicer to match the format expected by FlashForge printers and their API. Without this conversion, FlashForge printers fail to display critical print information.

### Restored Display Information

The conversion ensures FlashForge printers properly display:

- **Estimated Print Time (ETA)** - Time remaining and total print duration
- **Filament Usage** - Amount used in mm, cm³, grams, and cost
- **Layer Count** - Total layers and current layer progress
- **Print Settings** - Infill percentage, print speeds, layer height
- **Temperature Settings** - Nozzle and bed temperatures
- **Printer Configuration** - All slicer settings and parameters

## Why It's Needed

OrcaSlicer outputs G-code with metadata in a specific order. FlashForge printers require a different metadata structure (Orca-FlashForge format) to parse and display this information. This script reorders the G-code blocks to match FlashForge's expected format:

1. Header Block
2. Metadata (filament usage, ETA, layer count)
3. Config Block (all slicer settings)
4. Thumbnail Block
5. Executable G-code

## Installation

1. Clone or download this repository
2. Ensure Python 3.6+ is installed

## Usage

### As OrcaSlicer Post-Processing Script

1. In OrcaSlicer, go to **Printer Settings** → **Post-processing scripts**
2. Add the full path to `convert.py`:
   ```
   python /path/to/convert.py
   ```
3. Save settings. The script will automatically run after every slice.

### Manual Conversion

```bash
python convert.py <gcode_file>
```

The script creates a `.backup` file before modifying the original.

## Testing

Run the test suite to verify the conversion works correctly:

```bash
python tests/test_convert.py
```

All tests should pass, validating:
- Correct block ordering
- Metadata field presence and placement
- Header and config block structure
- Thumbnail block integrity
- No data loss during conversion

## Compatibility

- **Tested with:** OrcaSlicer 2.0+
- **Printer Models:** FlashForge Adventurer 5M Pro, and other Orca-FlashForge compatible models
- **Python:** 3.6+
