import dotfilesbuild.io.file.EditFile
import dotfilesbuild.io.file.content.SetContent

plugins {
  dotfilesbuild.`dotfiles-lifecycle`
}

val bin by configurations.creating {
  isCanBeConsumed = false
  isCanBeResolved = true
  attributes {
    attribute(Usage.USAGE_ATTRIBUTE, objects.named(Usage::class, "bin"))
  }
}

dependencies {
  bin(project(":shell:take-note"))
  bin(project(":programs:intellij"))
  bin(project(":programs:keepass"))
  bin(project(":programs:kubectl"))
}

tasks {
  val generatePathZshrcFile by registering(EditFile::class) {
    inputs.files(bin)
    description = "Generates a ZSH file than be sourced to expand the path to include "
    file.set(layout.buildDirectory.file("zsh/dotfiles_zsh"))
    editActions.set(
      listOf(
        SetContent {
          """
            #!/usr/bin/env bash
            
            export PATH="${'$'}{PATH}${bin.resolve().sorted().joinToString(separator = ":", prefix = ":")}" # generated by Gradle
          """.trimIndent()
        }
      )
    )
  }

  "dotfiles" {
    dependsOn(generatePathZshrcFile)
  }
}
