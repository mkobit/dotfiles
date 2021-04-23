package dotfilesbuild.config

import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import com.mkobit.gradle.test.kotlin.testkit.runner.build
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import strikt.api.expectCatching
import strikt.api.expectThat
import strikt.assertions.contains
import strikt.assertions.isSuccess
import strikt.assertions.containsSequence
import strikt.gradle.testkit.output
import testsupport.gradle.newGradleRunner
import java.nio.file.Path

internal class ConfigurationPluginTest {

  private companion object {
    private val CONFIG = """
      a = 0
      subproject1 {
        a = 1
        nestedsubproject {
          a = 2
        }
      }
      subproject2 {
        a = 3
      }
      
    """.trimIndent()
  }

  @Test
  internal fun `error when applied to subproject when not applied to root project`(@TempDir tempDir: Path) {
    val runner = newGradleRunner(tempDir) {
      setupProjectDir {
        "settings.gradle.kts" {
          content = """ 
            include("subproject")
          """.trimIndent().toByteArray()
        }
        "subproject" / {
          "build.gradle.kts" {
            content =
              """
            plugins {
              id("dotfilesbuild.configuration")
            }

              """.trimIndent().toByteArray()
          }
        }
      }
    }

    expectCatching { runner.buildAndFail() }
      .isSuccess()
      .output
      .contains("Plugin must be applied to root project first")
  }

  @Test
  internal fun `default configurations are loaded from Gradle user home and then project root`(@TempDir tempDir: Path) {
    val runner = newGradleRunner(tempDir) {
      setupProjectDir {
        "build.gradle.kts" {
          content =
            """
            plugins {
              id("dotfilesbuild.configuration")
            }
            
            tasks.create("showConfigurations") {
              doFirst("print configurations") {
                val projectPath = project.projectDir.toPath()
                dotfilesConfig.sources.get()
                  .forEach { source ->
                    println("config source: ${"$"}{projectPath.relativize(source)}")
                  }
                println(projectPath)
              }
            }

            """.trimIndent().toByteArray()
        }
      }
      withArguments("--gradle-user-home", tempDir.resolve(".override-gradle-user-home").toString())
    }

    expectThat(runner.build("showConfigurations"))
      .output
      .get { split("\n") }
      .get { filter { it.contains("config source: ") } }
      .containsSequence(
        "config source: .override-gradle-user-home/dotfiles.conf",
        "config source: dotfiles.conf"
      )
  }

  @Test
  internal fun `can obtain configuration values at each project depth`(@TempDir tempDir: Path) {
    val runner = newGradleRunner(tempDir) {
      setupProjectDir {
        "settings.gradle.kts" {
          content = """ 
            include("subproject1")
            include("subproject1:nestedsubproject")
            include("subproject2")
          """.trimIndent().toByteArray()
        }
        "dotfiles.conf"(content = CONFIG)
        "build.gradle.kts" {
          content = """
            plugins {
              id("dotfilesbuild.configuration")
            }
            
            tasks.create("printTask") {
              doFirst {
                println("root: ${"$"}{dotfiles.config.map { it.getLong("a") }.get()}")
              }
            }
          """.trimIndent().toByteArray()
        }
        "subproject1" / {
          "build.gradle.kts" {
            content =
              """
                plugins {
                  id("dotfilesbuild.configuration")
                }
                
                tasks.create("printTask") {
                  doFirst {
                    println("subproject1: ${"$"}{dotfiles.config.map { it.getLong("a") }.get()}")
                  }
                }
              """.trimIndent().toByteArray()
          }
          "nestedsubproject" / {
            "build.gradle.kts" {
              content =
                """
                plugins {
                  id("dotfilesbuild.configuration")
                }

                tasks.create("printTask") {
                  doFirst {
                    println("nestedsubproject: ${"$"}{dotfiles.config.map { it.getLong("a") }.get()}")
                  }
                }
                """.trimIndent().toByteArray()
            }
          }
        }
        "subproject2" / {
          "build.gradle.kts" {
            content =
              """
                plugins {
                  id("dotfilesbuild.configuration")
                }

                tasks.create("printTask") {
                  doFirst {
                    println("subproject2: ${"$"}{dotfiles.config.map { it.getLong("a") }.get()}")
                  }
                }
              """.trimIndent().toByteArray()
          }
        }
      }
    }

    expectThat(runner.build("printTask"))
      .output
      .contains("root: 0")
      .contains("subproject1: 1")
      .contains("nestedsubproject: 2")
      .contains("subproject2: 3")
  }
}
