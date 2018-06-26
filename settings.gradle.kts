rootProject.name = "dotfiles"

include("contest-entry")
include("kotlin-script-experiment")
include("sidekick-service")

rootProject.children.forEach { project ->
  val replacedName = project.name.run {
    val parts = split("-").toList()
    val suffix = parts.drop(1).joinToString("") { "${it[0].toUpperCase()}${it.substring(1)}" }
    "${parts[0]}$suffix"
  }
  project.buildFileName = "$replacedName.gradle.kts"
}
