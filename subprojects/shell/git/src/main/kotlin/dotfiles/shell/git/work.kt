package dotfiles.shell.git

import com.typesafe.config.Config
import com.typesafe.config.ConfigException
import io.mkobit.git.config.Commit
import io.mkobit.git.config.Section
import io.mkobit.git.config.User

internal fun workGitConfig(config: Config): List<Section> {
  return try {
    val workSettings = config.getConfig("git.configurations.work")
    val userSettings = workSettings.getConfig("user")
    val signingKey = if (userSettings.hasPath("signingKey")) {
      userSettings.getString("signingKey") }
    else {
      null
    }
    val user = User(
      email = userSettings.getString("email"),
      userName = userSettings.getString("email"),
      signingKey = signingKey
    )
    val commit = if (signingKey != null) {
      Commit(gpgSign = true)
    } else {
      null
    }

    listOfNotNull(user, commit)
  } catch (missing: ConfigException.Missing) {
    emptyList()
  }
}
