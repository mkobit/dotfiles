package dotfilesbuild.intellij

import dotfilesbuild.io.file.EditFile
import dotfilesbuild.io.file.content.SetContent

plugins {
  base
}

val taskGroup = "IntelliJ"

val intellij = extensions.create(
  "intellij",
  IntelliJExtension::class,
  objects.property<String>(),
  objects.property<Distribution>().apply {
    set(Distribution.COMMUNITY)
  }
)

val intellijDirectory = layout.buildDirectory.dir("intellij")
val versionDirectory = intellijDirectory.flatMap {
  it.dir(
    intellij.intellijVersion.flatMap { version ->
      intellij.distributionType.map { distribution ->
        "IntelliJ-$distribution-$version"
      }
    }
  )
}
val installDirectory = versionDirectory.map { it.dir("installation") }

val bin by configurations.creating {
  isCanBeConsumed = true
  isCanBeResolved = false
  attributes {
    attribute(Usage.USAGE_ATTRIBUTE, objects.named(Usage::class, "bin"))
  }
}

val dependencyHandler = dependencies
// dependency similar to https://github.com/JetBrains/gradle-intellij-plugin/blob/5499f90e0a033a11990cf834d3e43b7604b1e9d9/src/main/groovy/org/jetbrains/intellij/dependency/IdeaDependencyManager.groovy
val idea by configurations.creating {
  isCanBeResolved = true
  isCanBeConsumed = false
  withDependencies {
    repositories {
      maven {
        url = uri("https://cache-redirector.jetbrains.com/www.jetbrains.com/intellij-repository/releases")
        name = "IntelliJ Repository"
      }
    }
    val dependencyNotation = intellij.intellijVersion.flatMap { version ->
      intellij.distributionType.map { type ->
        val dependencyName = when (type) {
          Distribution.COMMUNITY -> "ideaIC"
          Distribution.ULTIMATE -> "ideaIU"
        }
        "com.jetbrains.intellij.idea:$dependencyName:$version"
      }
    }.get()
    dependencyHandler.add(this@creating.name, dependencyNotation)
  }
}

tasks {
  // unused since dependency resolution is utilized
  //  val downloadIntellijZip by registering(Download::class) {
  //    description = "Downloads the IntelliJ ZIP distribution"
  //    group = taskGroup
  //    url.set(intellij.intellijVersion.flatMap { version ->
  //      intellij.distributionType.map { type ->
  //        "https://download.jetbrains.com/idea/idea${type.code}-$version.tar.gz"
  //      }
  //    })

  //  destination.set(
  //    versionDirectory.flatMap { directory ->
  //      intellij.intellijVersion.flatMap { version ->
  //        intellij.distributionType.map { type ->
  //          directory.file("idea${type.code}-$version.tar.gz")
  //        }
  //      }
  //    }
  //  )
  // }

  val extractIntellijZip by registering(Copy::class) {
    description = "Extracts the IntelliJ ZIP distribution"
    group = taskGroup
    from(
      Callable {
        zipTree(idea.singleFile)
      }
    )
    into(installDirectory)
  }

  val generateIntelliJExecutable by registering(EditFile::class) {
    description = "Generate executable file that runs KeePass using mono"
    group = taskGroup
    editActions.add(
      SetContent {
        """
          #!/usr/bin/env bash
          set -euo pipefail
          nohup "${installDirectory.map { "$it/bin/idea.sh" }.get()}" > ${versionDirectory.map { it.file("output.log") }.get()} 2>&1 & disown
        """.trimIndent()
      }
    )
    file.set(versionDirectory.map { it.file("generated-bin/intellij") })
    executable.set(true)
  }

  bin.outgoing.artifact(generateIntelliJExecutable.flatMap { task -> task.output.map { it.asFile.parentFile } }) {
    builtBy(extractIntellijZip, generateIntelliJExecutable)
  }
}
