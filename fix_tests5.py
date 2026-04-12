import re

with open('src/python/claude_statusline/tests/test_main.py', 'r') as f:
    content = f.read()

# Fix mock return for git info in test_main
content = content.replace(
"""        with patch("claude_statusline.main.generate_git_segment") as mock_get_git_info:
            mock_get_git_info.return_value = []""",
"""        with patch("claude_statusline.main.generate_git_segment") as mock_get_git_info:
            from claude_statusline.models import SegmentGenerationResult, Segment
            mock_get_git_info.return_value = [SegmentGenerationResult(segment=Segment(text="main"), generator="internal.git", line=3)]"""
)

# test_main_full_payload
content = content.replace(
"""        with patch("claude_statusline.main.generate_git_segment") as mock_get_git_info:
            from claude_statusline.models import SegmentGenerationResult, Segment
            mock_get_git_info.return_value = [SegmentGenerationResult(segment=Segment(text="main"), generator="internal.git", line=3)]""",
"""        with patch("claude_statusline.main.generate_git_segment") as mock_get_git_info:
            mock_get_git_info.return_value = []"""
) # Wait this is replacing BOTH since I used [] in my script above. Let me do this properly.
