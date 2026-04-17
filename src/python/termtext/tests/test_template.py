from termtext import bg, blue, fg, link, red, t


def test_t_string_basic():
    res = t(t"hello {1}")
    assert str(res) == "hello 1"


def test_t_string_fg_color():
    res = t(t"hello {fg('yellow', 'world')}")
    assert str(res) == "hello [yellow]world[/yellow]"


def test_t_string_bg_color():
    res = t(t"hello {bg('cyan', 'world')}")
    assert str(res) == "hello [on cyan]world[/on cyan]"


def test_t_string_link():
    res = t(t"click {link('https://example.com', 'here')}")
    assert str(res) == "click [link=https://example.com]here[/link]"


def test_t_string_aliases():
    res = t(t"{red('a')} {blue('b')}")
    assert str(res) == "[red]a[/red] [blue]b[/blue]"


def test_t_string_complex():
    res = t(t"hello {red('world')} click {link('http://example.com', blue('here'))}")
    assert (
        str(res)
        == "hello [red]world[/red] click [link=http://example.com][blue]here[/blue][/link]"
    )
