from src.python_tools.hello_world.lib import Greeting

def test_greeting_format():
    g = Greeting(message="Hi", name="Test")
    assert g.format() == "Hi, Test!"
