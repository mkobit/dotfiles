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
    program = "gpg2" // gpg2 might be used on ubuntu/linux if gpg is still the old version
  ),
  User(
    email = "mkobit@gmail.com",
    userName = "Mike Kobit",
    signingKey = "1698254E135D7ADE!"
  )
)
