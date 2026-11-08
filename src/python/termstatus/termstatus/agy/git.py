from termstatus.agy.protocol import AgyPayload
from termstatus.git_status import VcsState, probe_git


def fallback_vcs(payload: AgyPayload) -> VcsState | None:
    return (
        VcsState(
            payload.vcs.branch,
            payload.vcs.dirty,
            payload.vcs.is_repo,
            untracked=payload.vcs.untracked,
            commit=payload.vcs.commit,
        )
        if payload.vcs
        else None
    )


async def resolve_vcs(payload: AgyPayload) -> VcsState | None:
    return await probe_git(payload.cwd) or fallback_vcs(payload) if payload.cwd is not None else payload.vcs
