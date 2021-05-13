package dotfiles.shell.git

import io.mkobit.git.config.Commit
import io.mkobit.git.config.Gpg
import io.mkobit.git.config.Section
import io.mkobit.git.config.User

internal fun personalGitConfig(): List<Section> = listOf(
  Commit(
    gpgSign = true
  ),
  Gpg(
    program = "gpg"
  ),
  User(
    email = "mkobit@gmail.com",
    userName = "Mike Kobit",
    signingKey = "1698254E135D7ADE!"
  )
)
