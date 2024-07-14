from typing import List
from src.dotfiles.git.config.commit import Commit
from src.dotfiles.git.config.gpg import Gpg
from src.dotfiles.git.config.section import Section
from src.dotfiles.git.config.user import User


def personal_git_config() -> List[Section]:
    personal = [
        Commit(gpg_sign=True),
        Gpg(program="gpg"),
        User(
            email="mkobit@gmail.com",
            user_name="Mike Kobit",
            signing_key="1698254E135D7ADE!",
        ),
    ]
    return personal
