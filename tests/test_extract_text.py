# tests/test_extract_text.py

import unittest
from unittest.mock import patch, MagicMock
from app.oop.extract_text import ExtractText

class TestExtractText(unittest.TestCase):

    @patch('app.oop.extract_text.ExtractText.format_raw_ocr_string')
    @patch('app.oop.extract_text.pytesseract.image_to_string')
    @patch('app.oop.extract_text.cv2.VideoCapture')
    def test_extract_code_without_openai(self, mock_videocap, mock_ocr, mock_format):
            '''
                Verify ‘whether the app logic is working correctly even when the OpenAI API
                is disabled or unavailable.

                mock_videocap: cv2.VideoCapture
                mock_ocr: pytesseract.image_to_string
                mock_format: ExtractText.format_raw_ocr_string
            '''
            # Video mock
            #Mock behaviour when a video is opened and read() is performed.
            mock_videocap.return_value.read.return_value = (True, 'dummy_frame')
            # Assume that the video has been opened successfully.
            mock_videocap.return_value.isOpened.return_value = True

            # OCR mock returns raw OCR result
            mock_ocr.return_value = 'raw ocr text'

            # Bypass OpenAI formatting, just return OCR result
            mock_format.return_value = 'raw ocr text'

            # Create an instance of the actual processing target class ExtractText
            extractor = ExtractText()

            # Call the method under test
            result = extractor.extract_code_at_timestamp('dummy.mp4', 5)

            # We expect the unformatted OCR result since OpenAI is skipped
            self.assertEqual(result, 'raw ocr text')



if __name__ == '__main__':
    unittest.main()