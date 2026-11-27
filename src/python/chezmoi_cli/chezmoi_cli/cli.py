"""Strongly typed model for building and running chezmoi CLI commands."""

from __future__ import annotations

import asyncio
import json
import shlex
import subprocess
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

type ConfigFormat = Literal["json", "toml", "yaml"]
type DataFormat = Literal["json", "yaml"]
type RefreshExternals = Literal["always", "auto", "never"]
type PathStyle = Literal["all", "relative", "source-relative", "source-absolute", "absolute"]
type OverrideData = Mapping[str, object] | str


def _optional_option(flag: str, value: Path | str | None) -> tuple[str, ...]:
    return (flag, str(value)) if value is not None else ()


def _optional_flag(flag: str, *, enabled: bool) -> tuple[str, ...]:
    return (flag,) if enabled else ()


def _optional_equals(flag: str, value: str | None) -> tuple[str, ...]:
    return (f"{flag}={value}",) if value is not None else ()


def _comma_option(flag: str, value: tuple[str, ...] | str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    joined = value if isinstance(value, str) else ",".join(value)
    return (f"{flag}={joined}",) if joined else ()


def _override_data_args(override_data: OverrideData | None) -> tuple[str, ...]:
    if override_data is None:
        return ()
    serialized = override_data if isinstance(override_data, str) else json.dumps(override_data)
    return ("--override-data", serialized)


@dataclass(frozen=True, slots=True)
class Apply:
    """Model for ``chezmoi apply``."""

    targets: tuple[Path | str, ...] = ()
    force: bool = False
    exclude: tuple[str, ...] | str | None = None
    refresh_externals: RefreshExternals | None = None

    def to_args(self) -> tuple[str, ...]:
        """Serialize this subcommand to CLI arguments."""
        return (
            "apply",
            *_optional_flag("--force", enabled=self.force),
            *_comma_option("--exclude", self.exclude),
            *_optional_equals("--refresh-externals", self.refresh_externals),
            *(str(target) for target in self.targets),
        )


@dataclass(frozen=True, slots=True)
class Cat:
    """Model for ``chezmoi cat``."""

    targets: tuple[Path | str, ...]

    def __post_init__(self) -> None:
        if not self.targets:
            raise ValueError("Cat requires at least one target")

    def to_args(self) -> tuple[str, ...]:
        """Serialize this subcommand to CLI arguments."""
        return ("cat", *(str(target) for target in self.targets))


@dataclass(frozen=True, slots=True)
class Data:
    """Model for ``chezmoi data``."""

    format: DataFormat | None = None

    def to_args(self) -> tuple[str, ...]:
        """Serialize this subcommand to CLI arguments."""
        return ("data", *_optional_equals("--format", self.format))


@dataclass(frozen=True, slots=True)
class Diff:
    """Model for ``chezmoi diff``."""

    targets: tuple[Path | str, ...] = ()
    exclude: tuple[str, ...] | str | None = None

    def to_args(self) -> tuple[str, ...]:
        """Serialize this subcommand to CLI arguments."""
        return (
            "diff",
            *_comma_option("--exclude", self.exclude),
            *(str(target) for target in self.targets),
        )


@dataclass(frozen=True, slots=True)
class ExecuteTemplate:
    """Model for ``chezmoi execute-template``."""

    template: str | None = None
    file: Path | str | None = None
    init: bool = False
    with_stdin: bool = False
    override_data: OverrideData | None = None

    def __post_init__(self) -> None:
        if self.template is not None and self.file is not None:
            raise ValueError("ExecuteTemplate accepts either template or file, not both")

    def to_args(self) -> tuple[str, ...]:
        """Serialize this subcommand to CLI arguments."""
        positional = (
            (str(self.file),) if self.file is not None else ((self.template,) if self.template is not None else ())
        )
        return (
            "execute-template",
            *_optional_flag("--file", enabled=self.file is not None),
            *_optional_flag("--init", enabled=self.init),
            *_optional_flag("--with-stdin", enabled=self.with_stdin),
            *_override_data_args(self.override_data),
            *positional,
        )


@dataclass(frozen=True, slots=True)
class Init:
    """Model for ``chezmoi init``."""

    apply: bool = False
    config_path: Path | str | None = None
    prompt_defaults: bool = False
    no_tty: bool = False

    def to_args(self) -> tuple[str, ...]:
        """Serialize this subcommand to CLI arguments."""
        return (
            "init",
            *_optional_flag("--apply", enabled=self.apply),
            *_optional_option("--config-path", self.config_path),
            *_optional_flag("--promptDefaults", enabled=self.prompt_defaults),
            *_optional_flag("--no-tty", enabled=self.no_tty),
        )


@dataclass(frozen=True, slots=True)
class Managed:
    """Model for ``chezmoi managed``."""

    include: tuple[str, ...] | str | None = None
    format: DataFormat | None = None
    path_style: PathStyle | None = None
    override_data: OverrideData | None = None

    def to_args(self) -> tuple[str, ...]:
        """Serialize this subcommand to CLI arguments."""
        return (
            "managed",
            *_comma_option("--include", self.include),
            *_optional_equals("--format", self.format),
            *_optional_equals("--path-style", self.path_style),
            *_override_data_args(self.override_data),
        )


@dataclass(frozen=True, slots=True)
class SourcePath:
    """Model for ``chezmoi source-path``."""

    targets: tuple[Path | str, ...] = ()

    def to_args(self) -> tuple[str, ...]:
        """Serialize this subcommand to CLI arguments."""
        return ("source-path", *(str(target) for target in self.targets))


@dataclass(frozen=True, slots=True)
class Status:
    """Model for ``chezmoi status``."""

    targets: tuple[Path | str, ...] = ()
    include: tuple[str, ...] | str | None = None

    def to_args(self) -> tuple[str, ...]:
        """Serialize this subcommand to CLI arguments."""
        return (
            "status",
            *_comma_option("--include", self.include),
            *(str(target) for target in self.targets),
        )


@dataclass(frozen=True, slots=True)
class TargetPath:
    """Model for ``chezmoi target-path``."""

    targets: tuple[Path | str, ...] = ()

    def to_args(self) -> tuple[str, ...]:
        """Serialize this subcommand to CLI arguments."""
        return ("target-path", *(str(target) for target in self.targets))


@dataclass(frozen=True, slots=True)
class RawCommand:
    """Fallback model for arbitrary chezmoi subcommand arguments."""

    args: tuple[str, ...]

    def to_args(self) -> tuple[str, ...]:
        """Serialize this subcommand to CLI arguments."""
        return self.args


type ChezmoiSubcommand = (
    Apply | Cat | Data | Diff | ExecuteTemplate | Init | Managed | SourcePath | Status | TargetPath | RawCommand
)


@dataclass(frozen=True, slots=True)
class ChezmoiCli:
    """Canonical configuration for building and executing chezmoi CLI commands."""

    executable: Path | str = "chezmoi"
    source: Path | str | None = None
    cache: Path | str | None = None
    config: Path | str | None = None
    config_format: ConfigFormat | None = None
    destination: Path | str | None = None
    persistent_state: Path | str | None = None
    no_tty: bool = False
    force: bool = False
    refresh_externals: RefreshExternals | None = None

    def global_args(self) -> tuple[str, ...]:
        """Return the executable and global flags."""
        return (
            str(self.executable),
            *_optional_option("--source", self.source),
            *_optional_option("--cache", self.cache),
            *_optional_option("--config", self.config),
            *_optional_option("--config-format", self.config_format),
            *_optional_option("--destination", self.destination),
            *_optional_option("--persistent-state", self.persistent_state),
            *_optional_flag("--no-tty", enabled=self.no_tty),
            *_optional_flag("--force", enabled=self.force),
            *_optional_equals("--refresh-externals", self.refresh_externals),
        )

    def with_options(
        self,
        *,
        executable: Path | str | None = None,
        source: Path | str | None = None,
        cache: Path | str | None = None,
        config: Path | str | None = None,
        config_format: ConfigFormat | None = None,
        destination: Path | str | None = None,
        persistent_state: Path | str | None = None,
        no_tty: bool | None = None,
        force: bool | None = None,
        refresh_externals: RefreshExternals | None = None,
    ) -> ChezmoiCli:
        """Return a new ChezmoiCli with specified fields updated."""
        updates: dict[str, object] = {}
        if executable is not None:
            updates["executable"] = executable
        if source is not None:
            updates["source"] = source
        if cache is not None:
            updates["cache"] = cache
        if config is not None:
            updates["config"] = config
        if config_format is not None:
            updates["config_format"] = config_format
        if destination is not None:
            updates["destination"] = destination
        if persistent_state is not None:
            updates["persistent_state"] = persistent_state
        if no_tty is not None:
            updates["no_tty"] = no_tty
        if force is not None:
            updates["force"] = force
        if refresh_externals is not None:
            updates["refresh_externals"] = refresh_externals
        return replace(self, **updates)  # type: ignore[arg-type]

    def command(self, subcommand: ChezmoiSubcommand) -> ChezmoiInvocation:
        """Bind a subcommand to this CLI configuration."""
        return ChezmoiInvocation(cli=self, subcommand=subcommand)

    def apply(
        self,
        *targets: Path | str,
        force: bool = False,
        exclude: tuple[str, ...] | str | None = None,
        refresh_externals: RefreshExternals | None = None,
    ) -> ChezmoiInvocation:
        """Build an ``apply`` invocation."""
        return self.command(Apply(targets=targets, force=force, exclude=exclude, refresh_externals=refresh_externals))

    def cat(self, *targets: Path | str) -> ChezmoiInvocation:
        """Build a ``cat`` invocation."""
        return self.command(Cat(targets=targets))

    def data(self, *, format: DataFormat | None = None) -> ChezmoiInvocation:
        """Build a ``data`` invocation."""
        return self.command(Data(format=format))

    def diff(
        self,
        *targets: Path | str,
        exclude: tuple[str, ...] | str | None = None,
    ) -> ChezmoiInvocation:
        """Build a ``diff`` invocation."""
        return self.command(Diff(targets=targets, exclude=exclude))

    def execute_template(
        self,
        template: str | None = None,
        *,
        file: Path | str | None = None,
        init: bool = False,
        with_stdin: bool = False,
        override_data: OverrideData | None = None,
    ) -> ChezmoiInvocation:
        """Build an ``execute-template`` invocation."""
        return self.command(
            ExecuteTemplate(
                template=template,
                file=file,
                init=init,
                with_stdin=with_stdin,
                override_data=override_data,
            )
        )

    def init(
        self,
        *,
        apply: bool = False,
        config_path: Path | str | None = None,
        prompt_defaults: bool = False,
        no_tty: bool = False,
    ) -> ChezmoiInvocation:
        """Build an ``init`` invocation."""
        return self.command(
            Init(
                apply=apply,
                config_path=config_path,
                prompt_defaults=prompt_defaults,
                no_tty=no_tty,
            )
        )

    def managed(
        self,
        *,
        include: tuple[str, ...] | str | None = None,
        format: DataFormat | None = None,
        path_style: PathStyle | None = None,
        override_data: OverrideData | None = None,
    ) -> ChezmoiInvocation:
        """Build a ``managed`` invocation."""
        return self.command(
            Managed(
                include=include,
                format=format,
                path_style=path_style,
                override_data=override_data,
            )
        )

    def source_path(self, *targets: Path | str) -> ChezmoiInvocation:
        """Build a ``source-path`` invocation."""
        return self.command(SourcePath(targets=targets))

    def status(
        self,
        *targets: Path | str,
        include: tuple[str, ...] | str | None = None,
    ) -> ChezmoiInvocation:
        """Build a ``status`` invocation."""
        return self.command(Status(targets=targets, include=include))

    def target_path(self, *targets: Path | str) -> ChezmoiInvocation:
        """Build a ``target-path`` invocation."""
        return self.command(TargetPath(targets=targets))

    def raw(self, *args: str) -> ChezmoiInvocation:
        """Build a raw subcommand invocation."""
        return self.command(RawCommand(args=args))


@dataclass(frozen=True, slots=True)
class ChezmoiInvocation:
    """A fully specified chezmoi CLI invocation ready to render or execute."""

    cli: ChezmoiCli
    subcommand: ChezmoiSubcommand

    @property
    def argv(self) -> tuple[str, ...]:
        """Return the complete argument vector."""
        return build_argv(self.cli, self.subcommand)

    @property
    def shell(self) -> str:
        """Return the shell-quoted command string."""
        return format_command(self.cli, self.subcommand)

    def run(
        self,
        *,
        input: str | None = None,
        env: Mapping[str, str] | None = None,
        cwd: Path | str | None = None,
        check: bool = False,
        timeout: float | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Run this chezmoi invocation synchronously and capture text output."""
        return subprocess.run(
            self.argv,
            input=input,
            env=env,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check,
            timeout=timeout,
        )

    async def run_async(
        self,
        *,
        input: str | None = None,
        env: Mapping[str, str] | None = None,
        cwd: Path | str | None = None,
        timeout: float = 30,
    ) -> subprocess.CompletedProcess[str]:
        """Run this chezmoi invocation asynchronously and capture text output."""
        process = await asyncio.create_subprocess_exec(
            *self.argv,
            stdin=asyncio.subprocess.PIPE if input is not None else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=cwd,
        )
        encoded_input = input.encode() if input is not None else None
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(encoded_input), timeout=timeout)
        finally:
            if process.returncode is None:
                with suppress(ProcessLookupError):
                    process.kill()
                await process.communicate()
        return subprocess.CompletedProcess(
            self.argv,
            await process.wait(),
            stdout.decode(errors="replace"),
            stderr.decode(errors="replace"),
        )


def build_argv(cli: ChezmoiCli, subcommand: ChezmoiSubcommand) -> tuple[str, ...]:
    """Build the complete argument vector for a chezmoi CLI invocation."""
    return (*cli.global_args(), *subcommand.to_args())


def format_command(cli: ChezmoiCli, subcommand: ChezmoiSubcommand) -> str:
    """Format a chezmoi CLI invocation as a shell-escaped string."""
    return shlex.join(build_argv(cli, subcommand))
