import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
from click.testing import CliRunner

from src.transcriber.main import transcribe

class TestTranscribe(unittest.TestCase):

    @patch('faster_whisper.WhisperModel')
    def test_transcribe_cli(self, mock_whisper_cls):
        # Mock the WhisperModel instance and its transcribe method
        mock_instance = mock_whisper_cls.return_value

        # Mocking the info object returned by transcribe
        mock_info = MagicMock()
        mock_info.duration = 10.0

        # Mocking the segments iterator
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 10.0
        mock_segment.text = "Hello world"

        # transcribe returns (segments_generator, info)
        mock_instance.transcribe.return_value = ([mock_segment], mock_info)

        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('test_audio.mp3', 'w') as f:
                f.write('fake audio content')

            result = runner.invoke(transcribe, ['test_audio.mp3'])

            if result.exit_code != 0:
                print(result.output)
                print(result.exception)

            self.assertEqual(result.exit_code, 0)
            self.assertIn("Hello world", result.output)

            # Verify WhisperModel was called with default args
            mock_whisper_cls.assert_called_with('base', device='auto', compute_type='default')

    @patch('faster_whisper.WhisperModel')
    def test_transcribe_with_template(self, mock_whisper_cls):
        mock_instance = mock_whisper_cls.return_value
        mock_info = MagicMock()
        mock_info.duration = 10.0
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 10.0
        mock_segment.text = "Hello world"
        mock_instance.transcribe.return_value = ([mock_segment], mock_info)

        template_content = "Summary: {{ text }}"

        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('test_audio.mp3', 'w') as f:
                f.write('fake audio')
            with open('template.j2', 'w') as f:
                f.write(template_content)

            result = runner.invoke(transcribe, ['test_audio.mp3', '--template', 'template.j2'])

            if result.exit_code != 0:
                print(result.output)
                print(result.exception)

            self.assertEqual(result.exit_code, 0)
            self.assertIn("Summary: Hello world", result.output)

if __name__ == '__main__':
    unittest.main()
