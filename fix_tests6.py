with open('src/python/claude_statusline/tests/test_main.py', 'r') as f:
    lines = f.readlines()

out = []
in_test_main = False
in_test_full = False
for line in lines:
    if "def test_main(" in line:
        in_test_main = True
        in_test_full = False
    elif "def test_main_full_payload" in line:
        in_test_full = True
        in_test_main = False

    if "mock_get_git_info.return_value = []" in line:
        if in_test_main:
            out.append('            from claude_statusline.models import SegmentGenerationResult, Segment\n')
            out.append('            mock_get_git_info.return_value = [SegmentGenerationResult(segment=Segment(text="main"), generator="internal.git", line=3)]\n')
        elif in_test_full:
            out.append('            from claude_statusline.models import SegmentGenerationResult, Segment\n')
            out.append('            mock_get_git_info.return_value = [SegmentGenerationResult(segment=Segment(text="feature-branch"), generator="internal.git", line=3)]\n')
        else:
            out.append(line)
    else:
        out.append(line)

with open('src/python/claude_statusline/tests/test_main.py', 'w') as f:
    f.writelines(out)
