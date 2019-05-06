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
import testsupport.strikt.isDirectory
import testsupport.strikt.projectDir
import testsupport.strikt.resolvePath
import java.nio.file.Path

internal class UnmanagedBinPluginTest {
  @Test
  internal fun `directory is created, exported in the PATH in zshell file, and not removed by clean`(@TempDir tempDir: Path) {
    val runner = newGradleRunner(tempDir) {
      setupProjectDir {
        "build.gradle.kts" {
          content = """
            plugins {
              id("dotfilesbuild.shell.unmanaged-bin")
            }
          """.trimIndent().toByteArray()
        }
      }
    }

    runner.build("generateZshrcFile").let { result ->
      expectThat(result) {
        projectDir.resolvePath(".unmanaged_bin")
            .exists()
            .isDirectory()
        projectDir.resolvePath("build/zsh/generated_zshrc")
            .exists()
            .content
            .contains("""export PATH="${'$'}PATH:${result.projectDir.resolve(".unmanaged_bin").toAbsolutePath()}" # dotfiles: dotfiles unmanaged bin files""")
      }
    }

    runner.build("clean").let { result ->
      expectThat(result) {
        projectDir.resolvePath(".unmanaged_bin")
            .exists()
            .isDirectory()
      }
    }
  }
}
