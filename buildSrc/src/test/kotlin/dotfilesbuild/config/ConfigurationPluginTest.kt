package dotfilesbuild.config

import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import com.mkobit.gradle.test.kotlin.testkit.runner.build
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import strikt.api.expectCatching
import strikt.api.expectThat
import strikt.assertions.isSuccess
import strikt.assertions.containsSequence
import strikt.gradle.testkit.output
import testsupport.gradle.newGradleRunner
import java.nio.file.Path

internal class ConfigurationPluginTest {
  @Test
  internal fun `cannot be applied to subproject`(@TempDir tempDir: Path) {
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
}
