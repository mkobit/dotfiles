from src.dotfiles.git.config.section import Section


from typing import List, final
from dataclasses import dataclass, field


@dataclass(frozen=True)
@final
class RemoteSetting:
    name: str
    url: str | None
    pushurl: str | None
    proxy: str | None
    proxyAuthMethod: str | None
    fetch: str | None
    push: str | None
    mirror: bool | None
    skipDefaultUpdate: bool | None
    skipFetchAll: bool | None
    receivepack: str | None
    uploadpack: str | None
    tagOpt: str | None
    vcs: str | None
    prune: bool | str | None
    pruneTags: bool | None
    promisor: bool | None
    partialclonefilter: str | None


@dataclass(frozen=True)
@final
class Remote(Section):
    names: List[RemoteSetting] = field(default_factory=list)
