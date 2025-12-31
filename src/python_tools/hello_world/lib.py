from pydantic import BaseModel

class Greeting(BaseModel):
    message: str
    name: str

    def format(self) -> str:
        return f"{self.message}, {self.name}!"
