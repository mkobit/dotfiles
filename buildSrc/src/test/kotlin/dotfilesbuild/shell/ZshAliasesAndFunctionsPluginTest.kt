package dotfilesbuild.shell

import com.mkobit.gradle.test.kotlin.testkit.runner.build
import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import strikt.api.expectThat
import strikt.assertions.contains
import testsupport.gradle.newGradleRunner
import testsupport.strikt.content
import testsupport.strikt.exists
import testsupport.strikt.projectDir
import testsupport.strikt.resolvePath
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

    runner.build("generateZshrcFile").let { result ->
      expectThat(result) {
        projectDir.resolvePath("build/zsh/generated_zshrc")
            .exists()
            .content
            .contains(""". "${result.projectDir.resolve("zsh/aliases.source").toAbsolutePath()}" # dotfiles: aliases.source""")
            .contains(""". "${result.projectDir.resolve("zsh/functions.source").toAbsolutePath()}" # dotfiles: functions.source""")
      }
    }
  }
}
