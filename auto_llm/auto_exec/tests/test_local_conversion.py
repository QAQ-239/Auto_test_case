import unittest

class TestLocalConversion(unittest.TestCase):

    def convert_text_format(self, text, format_type):
        if format_type == "MD":
            return {"result": f"{text}.md"}
        elif format_type == "JSON":
            return {"result": f'{{"text": "{text}"}}'}
        else:
            return {"error": "unsupported format"}

    def test_convert_text_format_md(self):
        result = self.convert_text_format("Hello World", "MD")
        self.assertEqual(result, {"result": "Hello World.md"})

    def test_convert_text_format_json(self):
        result = self.convert_text_format("Hello World", "JSON")
        self.assertEqual(result, {"result": '{"text": "Hello World"}'})

    def test_convert_text_format_unsupported(self):
        result = self.convert_text_format("Hello World", "PDF")
        self.assertEqual(result, {"error": "unsupported format"})

if __name__ == "__main__":
    unittest.main()