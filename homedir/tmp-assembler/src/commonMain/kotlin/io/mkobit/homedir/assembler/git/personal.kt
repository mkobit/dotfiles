package io.mkobit.homedir.assembler.git

import io.mkobit.git.model.Commit
import io.mkobit.git.model.Gpg
import io.mkobit.git.model.Section
import io.mkobit.git.model.User

internal fun personalGitConfig(): List<Section> = buildList {
  add(
    Commit(
      gpgSign = true
    )
  )
  add(
    Gpg(
      program = "gpg"
    )
  )
  add(
    User(
      email = "mkobit@gmail.com",
      userName = "Mike Kobit",
      signingKey = "1698254E135D7ADE!"
    )
  )
}
