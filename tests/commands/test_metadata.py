from media_management_scripts.main import build_argparse, ArgParseException
import argparse

parser = build_argparse()

FILENAME = "file.mkv"

import unittest


class MetadataCommandTestCase(unittest.TestCase):
    def test_basic(self):
        ns = parser.parse_args(["metadata", FILENAME])
        self.assertEqual(FILENAME, ns.input)
        self.assertEqual(False, ns.popup)
        self.assertEqual(False, ns.json)
        self.assertEqual("none", ns.interlace)

    def test_popup(self):
        ns = parser.parse_args(["metadata", FILENAME, "--popup"])
        self.assertEqual(FILENAME, ns.input)
        self.assertEqual(True, ns.popup)
        self.assertEqual(False, ns.json)
        self.assertEqual("none", ns.interlace)

    def test_order(self):
        ns = parser.parse_args(["metadata", "--popup", FILENAME])
        self.assertEqual(FILENAME, ns.input)
        self.assertEqual(True, ns.popup)
        self.assertEqual(False, ns.json)
        self.assertEqual("none", ns.interlace)

    def test_json(self):
        ns = parser.parse_args(["metadata", FILENAME, "--json"])
        self.assertEqual(FILENAME, ns.input)
        self.assertEqual(False, ns.popup)
        self.assertEqual(True, ns.json)
        self.assertEqual("none", ns.interlace)

    def test_interlace(self):
        ns = parser.parse_args(["metadata", FILENAME, "--interlace", "summary"])
        self.assertEqual(FILENAME, ns.input)
        self.assertEqual(False, ns.popup)
        self.assertEqual(False, ns.json)
        self.assertEqual("summary", ns.interlace)

        ns = parser.parse_args(["metadata", FILENAME, "--interlace", "report"])
        self.assertEqual(FILENAME, ns.input)
        self.assertEqual(False, ns.popup)
        self.assertEqual(False, ns.json)
        self.assertEqual("report", ns.interlace)

    def test_interlace_onvalid(self):
        with self.assertRaises(ArgParseException):
            parser.parse_args(["metadata", FILENAME, "--interlace", "qwerty"])
