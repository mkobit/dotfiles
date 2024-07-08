from src.dotfiles.git.config.section import Section


from typing import List, final
from dataclasses import dataclass, field


@dataclass(frozen=True, kw_only=True)
@final
class RemoteSetting:
    name: str
    url: str | None = None
    pushurl: str | None = None
    proxy: str | None = None
    proxy_auth_method: str | None = None
    fetch: str | None = None
    push: str | None = None
    mirror: bool | None = None
    skip_default_update: bool | None = None
    skip_fetch_all: bool | None = None
    receivepack: str | None = None
    uploadpack: str | None = None
    tag_opt: str | None = None
    vcs: str | None = None
    prune: bool | str | None = None
    prune_tags: bool | None = None
    promisor: bool | None = None
    partialclonefilter: str | None = None


@dataclass(frozen=True, kw_only=True)
@final
class Remote(Section):
    names: List[RemoteSetting] = field(default_factory=list)
