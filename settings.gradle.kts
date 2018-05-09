rootProject.name = "dotfiles"
rootProject.buildFileName = "build.gradle.kts"

include("sidekick-service")
include("contest-entry")
include("ktor-ws")

rootProject.children.forEach { project ->
  val replacedName = project.name.run {
    val parts = split("-").toList()
    val suffix = parts.drop(1).joinToString("") { "${it[0].toUpperCase()}${it.substring(1)}" }
    "${parts[0]}$suffix"
  }
  project.buildFileName = "$replacedName.gradle.kts"
}
