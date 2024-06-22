//pluginManagement {
//  includeBuild("gradle/build-logic")
//  repositories {
//    gradlePluginPortal()
//  }
//}
plugins {
  id("org.gradle.toolchains.foojay-resolver-convention") version ("0.8.0")
//  id("dotfilesbuild.dependencies.catalog")
//  id("dotfilesbuild.version-catalog")
}

includeBuild("gradle/build-logic")

rootProject.name = "dotfiles"

apply(from = file("gradle/shared.settings.gradle.kts"))

shellLibraries {
  subproject("git")
  subproject("ssh")
  subproject("tmux")
  subproject("vim")
  subproject("vscode")
  subproject("zsh")
}

homedir {
  subproject("tmp-assembler")
}

testing {
  subproject("kotest-support")
}

//"shell".let {
//  include("$it:aggregator")
//  include("$it:external-configuration")
//  include("$it:git")
//  include("$it:ssh")
//  include("$it:take-note")
//  include("$it:tmux")
//  include("$it:vim")
//}
//
//"local-libraries".let {
//  include("$it:pico-cli-utils")
//  "$it:git".let { git ->
//    include("$git:git-config-generator")
//    include("$git:git-config-script")
//  }
//  "$it:ssh".let { ssh ->
//    include("$ssh:ssh-config-generator")
//    include("$ssh:ssh-config-script")
//  }
//  "$it:testing".let { testing ->
//    include("$testing:strikt-kotlin-scripting")
//  }
//}
//
//"programs".let {
//  include("$it:jq")
//  include("$it:keepass")
//  include("$it:kubectl")
//}
//
//"experimental".let {
//  include("$it:chrome-debug-protocol")
//  include("$it:chrome-debug-protocol-generator")
//  include("$it:sidekick-service")
//}

fun homedir(configuration: ProjectScope.() -> Unit) {
  ProjectScope("homedir").run(configuration)
}

fun shellLibraries(configuration: ProjectScope.() -> Unit) {
  ProjectScope("shell-model").run(configuration)
}

fun testing(configuration: ProjectScope.() -> Unit) {
  ProjectScope("testing").run(configuration)
}

class ProjectScope(
  private val parentProject: ProjectDescriptor
) {
  constructor(path: String) : this(
    include(path).run {
      project(":$path").apply {
        projectDir = file(path)
      }
    }
  )

  fun subproject(projectName: String) {
    val projectPath = "${parentProject.path}:$projectName"
    include(projectPath)
    project(projectPath).projectDir = parentProject.projectDir.resolve(projectName)
  }
}

//rootProject.children.forEach { project -> configureSubproject(project) }

//fun configureSubproject(projectDescriptor: ProjectDescriptor) {
//  projectDescriptor.projectDir =
//    file("subprojects/${projectDescriptor.path.replace(":", "/")}")
//  projectDescriptor.children.forEach { configureSubproject(it) }
//}

enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")

private operator fun File.div(relative: String) = resolve(relative)
