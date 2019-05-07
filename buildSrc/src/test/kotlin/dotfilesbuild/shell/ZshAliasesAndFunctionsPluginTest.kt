package dotfilesbuild.shell

import com.mkobit.gradle.test.kotlin.testkit.runner.build
import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import strikt.api.expectThat
import strikt.assertions.contains
import strikt.assertions.exists
import strikt.assertions.resolve
import testsupport.gradle.newGradleRunner
import testsupport.strikt.content
import testsupport.strikt.projectDir
import java.nio.file.Path

internal class ZshAliasesAndFunctionsPluginTest {
  @Test
  internal fun `source functions of source controlled files added to generated zsh file`(@TempDir tempDir: Path) {
    val runner = newGradleRunner(tempDir) {
      setupProjectDir {
        "build.gradle.kts" {
          content = """
            plugins {
              id("dotfilesbuild.shell.zsh-aliases-and-functions")
            }
          """.trimIndent().toByteArray()
        }
      }
    }

    expectThat(runner.build("generateZshrcFile")) {
      projectDir
        .resolve("build/zsh/generated_zshrc")
        .exists()
        .content
        .contains(""". "${tempDir.resolve("zsh/aliases.source").toAbsolutePath()}" # dotfiles: aliases.source""")
        .contains(""". "${tempDir.resolve("zsh/functions.source").toAbsolutePath()}" # dotfiles: functions.source""")
    }
  }
}
