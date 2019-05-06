rootProject.name = "dotfiles"

include("chrome-debug-protocol")
include("chrome-debug-protocol-generator")
include("contest-entry")
include("kotlin-script-experiment")
include("java-platform")
include("sidekick-service")

buildCache {
  local(DirectoryBuildCache::class) {
    isEnabled = true
    setDirectory(file(".gradle-build-cache"))
  }
}

fun String.toKebabCase(): String = split("-").toList().let {
  val suffix = it.drop(1).joinToString("") { "${it[0].toUpperCase()}${it.substring(1)}" }
  "${it.first()}$suffix"
}

rootProject.children.forEach { project ->
  val replacedName = project.name.toKebabCase()
  project.projectDir = file("subprojects/${project.name}")
  project.buildFileName = "$replacedName.gradle.kts"
}
