from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread


@contextmanager
def serve_directory(directory, handler=SimpleHTTPRequestHandler):
    """Serve a local directory for the lifetime of the context."""
    with ThreadingHTTPServer(("127.0.0.1", 0), partial(handler, directory=str(directory))) as server:
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()
