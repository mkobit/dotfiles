package dotfilesbuild.shell

import com.mkobit.gradle.test.kotlin.testkit.runner.build
import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import strikt.api.expectThat
import strikt.assertions.contains
import strikt.assertions.exists
import strikt.assertions.isDirectory
import strikt.assertions.resolve
import testsupport.gradle.newGradleRunner
import testsupport.strikt.content
import testsupport.strikt.projectDir
import java.nio.file.Path

internal class ManagedBinPluginTest {
  @Test
  internal fun `managed bin directory is created and exported in the PATH in zshell file`(@TempDir tempDir: Path) {
    val runner = newGradleRunner(tempDir) {
      setupProjectDir {
        "build.gradle.kts" {
          content = """
            plugins {
              id("dotfilesbuild.shell.managed-bin")
            }
          """.trimIndent().toByteArray()
        }
      }
    }

    expectThat(runner.build("generateZshrcFile")) {
      projectDir
        .resolve("build/managed_bin")
        .exists()
        .isDirectory()
      projectDir
        .resolve("build/zsh/generated_zshrc")
        .exists()
        .content
        .contains("""export PATH="${'$'}PATH:${tempDir.resolve("build/managed_bin").toAbsolutePath()}" # dotfiles: dotfiles managed bin files""")
    }

    expectThat(runner.build("clean")) {
      projectDir
        .resolve("build/managed_bin")
        .not { exists() }
    }
  }
}
