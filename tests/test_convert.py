#!/usr/bin/env python3
"""
Test suite for OrcaSlicer to Orca-FlashForge post-processing script.
Validates that the conversion produces correctly structured G-code files.
"""

import unittest
import os
import shutil
import subprocess
import sys
from typing import List, Dict, Optional


class TestOrcaToFlashForgeConversion(unittest.TestCase):
    """Test cases for validating G-code conversion to Orca-FlashForge format."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures and paths."""
        cls.script_dir = os.path.dirname(os.path.abspath(__file__))
        cls.convert_script = os.path.join(os.path.dirname(cls.script_dir), "convert.py")
        cls.test_fixture = os.path.join(cls.script_dir, "test.gcode")

        # Verify required files exist
        if not os.path.exists(cls.convert_script):
            raise FileNotFoundError(f"Convert script not found: {cls.convert_script}")
        if not os.path.exists(cls.test_fixture):
            raise FileNotFoundError(f"Test fixture not found: {cls.test_fixture}")

    def setUp(self):
        """Create a temporary copy of the test fixture for each test."""
        self.temp_gcode = os.path.join(self.script_dir, "temp_test.gcode")
        self.temp_backup = self.temp_gcode + ".backup"

        # Copy test fixture to temp file
        shutil.copy2(self.test_fixture, self.temp_gcode)

        # Run the conversion script
        result = subprocess.run(
            [sys.executable, self.convert_script, self.temp_gcode],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Conversion script failed: {result.stderr}")

        # Read the converted content
        with open(self.temp_gcode, 'r', encoding='utf-8') as f:
            self.converted_content = f.read()

        self.converted_lines = self.converted_content.split('\n')

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_gcode):
            os.remove(self.temp_gcode)
        if os.path.exists(self.temp_backup):
            os.remove(self.temp_backup)

    def _find_line_index(self, search_text: str) -> Optional[int]:
        """Find the index of a line containing the search text."""
        for i, line in enumerate(self.converted_lines):
            if search_text in line:
                return i
        return None

    def _find_all_line_indices(self, search_text: str) -> List[int]:
        """Find all indices of lines containing the search text."""
        indices = []
        for i, line in enumerate(self.converted_lines):
            if search_text in line:
                indices.append(i)
        return indices

    def _get_block_positions(self) -> Dict[str, Optional[int]]:
        """Get the line positions of all major blocks."""
        return {
            'header_start': self._find_line_index('; HEADER_BLOCK_START'),
            'header_end': self._find_line_index('; HEADER_BLOCK_END'),
            'config_start': self._find_line_index('; CONFIG_BLOCK_START'),
            'config_end': self._find_line_index('; CONFIG_BLOCK_END'),
            'thumbnail_start': self._find_line_index('; THUMBNAIL_BLOCK_START'),
            'thumbnail_end': self._find_line_index('; THUMBNAIL_BLOCK_END'),
        }

    # ========== Block Structure Tests ==========

    def test_header_block_exists(self):
        """Test that HEADER_BLOCK_START and HEADER_BLOCK_END exist."""
        positions = self._get_block_positions()

        self.assertIsNotNone(
            positions['header_start'],
            "Missing ; HEADER_BLOCK_START"
        )
        self.assertIsNotNone(
            positions['header_end'],
            "Missing ; HEADER_BLOCK_END"
        )
        self.assertLess(
            positions['header_start'],
            positions['header_end'],
            "HEADER_BLOCK_START should come before HEADER_BLOCK_END"
        )

    def test_config_block_exists(self):
        """Test that CONFIG_BLOCK_START and CONFIG_BLOCK_END exist."""
        positions = self._get_block_positions()

        self.assertIsNotNone(
            positions['config_start'],
            "Missing ; CONFIG_BLOCK_START"
        )
        self.assertIsNotNone(
            positions['config_end'],
            "Missing ; CONFIG_BLOCK_END"
        )
        self.assertLess(
            positions['config_start'],
            positions['config_end'],
            "CONFIG_BLOCK_START should come before CONFIG_BLOCK_END"
        )

    def test_thumbnail_block_exists(self):
        """Test that THUMBNAIL_BLOCK exists and is properly formed."""
        positions = self._get_block_positions()

        # Require thumbnail block to exist
        self.assertIsNotNone(
            positions['thumbnail_start'],
            "Missing ; THUMBNAIL_BLOCK_START"
        )
        self.assertIsNotNone(
            positions['thumbnail_end'],
            "Missing ; THUMBNAIL_BLOCK_END"
        )
        self.assertLess(
            positions['thumbnail_start'],
            positions['thumbnail_end'],
            "THUMBNAIL_BLOCK_START should come before THUMBNAIL_BLOCK_END"
        )

    def test_block_ordering(self):
        """Test that blocks appear in the correct order: Header → Metadata → Config → Thumbnail → Executable."""
        positions = self._get_block_positions()

        # Header should come first
        self.assertIsNotNone(positions['header_start'], "Missing header block")

        # Find first metadata line (should be after header, before config)
        metadata_fields = [
            '; filament used [mm]',
            '; filament used [g]',
            '; total filament used [g]',
            '; estimated printing time (normal mode)'
        ]

        metadata_positions = []
        for field in metadata_fields:
            pos = self._find_line_index(field)
            if pos is not None:
                metadata_positions.append(pos)

        if metadata_positions:
            first_metadata_pos = min(metadata_positions)

            # Metadata should come after header
            self.assertLess(
                positions['header_end'],
                first_metadata_pos,
                "Metadata should come after HEADER_BLOCK_END"
            )

            # Metadata should come before config
            self.assertLess(
                first_metadata_pos,
                positions['config_start'],
                "Metadata should come before CONFIG_BLOCK_START"
            )

        # Config should come before thumbnail (if thumbnail exists)
        if positions['thumbnail_start'] is not None:
            self.assertLess(
                positions['config_end'],
                positions['thumbnail_start'],
                "CONFIG_BLOCK should come before THUMBNAIL_BLOCK"
            )

    # ========== Metadata Validation Tests ==========

    def test_metadata_fields_present(self):
        """Test that critical metadata fields are present."""
        required_fields = [
            '; filament used [mm]',
            '; filament used [g]',
            '; total filament used [g]',
            '; estimated printing time (normal mode)'
        ]

        for field in required_fields:
            with self.subTest(field=field):
                pos = self._find_line_index(field)
                self.assertIsNotNone(
                    pos,
                    f"Missing required metadata field: {field}"
                )

    def test_metadata_before_config(self):
        """Test that all metadata fields appear before CONFIG_BLOCK_START."""
        positions = self._get_block_positions()
        config_start = positions['config_start']

        self.assertIsNotNone(config_start, "Missing CONFIG_BLOCK_START")

        metadata_fields = [
            '; filament used [mm]',
            '; filament used [g]',
            '; total filament used [g]',
            '; estimated printing time (normal mode)'
        ]

        for field in metadata_fields:
            with self.subTest(field=field):
                pos = self._find_line_index(field)
                if pos is not None:
                    self.assertLess(
                        pos,
                        config_start,
                        f"Metadata field '{field}' should appear before CONFIG_BLOCK_START"
                    )

    def test_metadata_after_header(self):
        """Test that all metadata fields appear after HEADER_BLOCK_END."""
        positions = self._get_block_positions()
        header_end = positions['header_end']

        self.assertIsNotNone(header_end, "Missing HEADER_BLOCK_END")

        metadata_fields = [
            '; filament used [mm]',
            '; filament used [g]',
            '; total filament used [g]',
            '; estimated printing time (normal mode)'
        ]

        for field in metadata_fields:
            with self.subTest(field=field):
                pos = self._find_line_index(field)
                if pos is not None:
                    self.assertGreater(
                        pos,
                        header_end,
                        f"Metadata field '{field}' should appear after HEADER_BLOCK_END"
                    )

    # ========== Header Block Tests ==========

    def test_header_contains_generated_by(self):
        """Test that the header block contains a 'generated by' line."""
        positions = self._get_block_positions()
        header_start = positions['header_start']
        header_end = positions['header_end']

        self.assertIsNotNone(header_start, "Missing HEADER_BLOCK_START")
        self.assertIsNotNone(header_end, "Missing HEADER_BLOCK_END")

        # Search within header block
        found_generated_by = False
        for i in range(header_start, header_end + 1):
            if 'generated by' in self.converted_lines[i].lower():
                found_generated_by = True
                break

        self.assertTrue(
            found_generated_by,
            "Header block should contain a 'generated by' line"
        )

    # ========== Content Preservation Tests ==========

    def test_no_data_loss(self):
        """Test that no significant content was lost during conversion."""
        # Read original file
        with open(self.test_fixture, 'r', encoding='utf-8') as f:
            original_content = f.read()

        original_lines = [line.strip() for line in original_content.split('\n') if line.strip()]
        converted_lines = [line.strip() for line in self.converted_content.split('\n') if line.strip()]

        # Allow for minor line count differences due to formatting
        line_diff = abs(len(original_lines) - len(converted_lines))

        self.assertLess(
            line_diff,
            10,
            f"Significant difference in line count: original={len(original_lines)}, converted={len(converted_lines)}"
        )


def run_tests():
    """Run the test suite."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestOrcaToFlashForgeConversion))

    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
