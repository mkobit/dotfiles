"""_summary_
See [Git documentation](https://git-scm.com/docs/git-config).
"""

from .alias import Alias
from .branch import Branch
from .color import Color
from .column import Column
from .commit import Commit
from .core import Core
from .diff import Diff
from .fetch import Fetch
from .gpg import Gpg
from .help import Help
from .init import Init
from .interactive import Interactive
from .merge import Merge
from .pager import Pager
from .pull import Pull
from .push import Push
from .rebase import Rebase
from .receive import Receive
from .remote import Remote
from .rerere import Rerere
from .stash import Stash
from .status import Status
from .tag import Tag
from .user import User

from .serialization import dumps

__all__ = [
    'dumps',
    'Alias',
    'Branch',
    'Color',
    'Column',
    'Commit',
    'Core',
    'Diff',
    'Fetch',
    'Gpg',
    'Help',
    'Init',
    'Interactive',
    'Merge',
    'Pager',
    'Pull',
    'Push',
    'Rebase',
    'Receive',
    'Remote',
    'Rerere',
    'Stash',
    'Status',
    'Tag',
    'User'
]
