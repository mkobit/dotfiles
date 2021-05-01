package dotfiles.shell.ssh

import java.nio.file.Path
import kotlin.io.path.ExperimentalPathApi
import kotlin.io.path.Path

@ExperimentalPathApi
internal fun homeDir(): Path = Path(System.getProperty("user.home"))
