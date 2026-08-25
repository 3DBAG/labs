import json
import unittest
from pathlib import Path
from unittest.mock import patch

import hooks
from properdocs.exceptions import ProperDocsException


ROOT = Path(__file__).resolve().parents[1]


class LabsContentValidationTests(unittest.TestCase):
    def setUp(self):
        self.records = json.loads((ROOT / "labs-content.json").read_text(encoding="utf-8"))

    def test_catalogue_passes_schema_and_path_validation(self):
        cards = hooks._load_cards()

        self.assertEqual(len(cards), len(self.records))
        self.assertEqual(cards[0]["image"], "assets/images/labs/example-lab.jpg")

    def test_image_has_required_dimensions(self):
        hooks._load_cards()

    def test_image_dimensions_are_rejected(self):
        with patch.object(hooks, "Image") as image_module:
            image = image_module.open.return_value.__enter__.return_value
            image.size = (450, 225)
            with self.assertRaisesRegex(ProperDocsException, "expected exactly 600x350 pixels"):
                hooks._load_cards()

    def test_duplicate_ids_are_rejected_with_record_reference(self):
        self.records.append(dict(self.records[0]))

        with patch.object(hooks, "CATALOGUE") as catalogue:
            catalogue.read_text.return_value = json.dumps(self.records)
            with self.assertRaisesRegex(ProperDocsException, r"record \d+: 'id' 1 duplicates the value from record 1"):
                hooks._load_cards()

    def test_schema_rejects_unknown_fields(self):
        self.records[0]["unexpected"] = True

        with patch.object(hooks, "CATALOGUE") as catalogue:
            catalogue.read_text.return_value = json.dumps(self.records)
            with self.assertRaisesRegex(ProperDocsException, "Additional properties"):
                hooks._load_cards()

    def test_schema_rejects_invalid_link(self):
        self.records[0]["link"] = "not-a-url"

        with patch.object(hooks, "CATALOGUE") as catalogue:
            catalogue.read_text.return_value = json.dumps(self.records)
            with self.assertRaisesRegex(ProperDocsException, "'link'"):
                hooks._load_cards()

    def test_description_is_limited_to_140_words(self):
        self.records[0]["description"] = "word " * 141

        with patch.object(hooks, "CATALOGUE") as catalogue:
            catalogue.read_text.return_value = json.dumps(self.records)
            with self.assertRaisesRegex(ProperDocsException, "140 words"):
                hooks._load_cards()

    def test_image_must_exist_inside_docs(self):
        self.records[0]["image"] = "assets/images/labs/missing.jpg"

        with patch.object(hooks, "CATALOGUE") as catalogue:
            catalogue.read_text.return_value = json.dumps(self.records)
            with self.assertRaisesRegex(ProperDocsException, "image does not exist"):
                hooks._load_cards()

    def test_image_path_traversal_is_rejected(self):
        self.records[0]["image"] = "../outside.jpg"

        with patch.object(hooks, "CATALOGUE") as catalogue:
            catalogue.read_text.return_value = json.dumps(self.records)
            with self.assertRaisesRegex(ProperDocsException, "path traversal"):
                hooks._load_cards()


if __name__ == "__main__":
    unittest.main()
