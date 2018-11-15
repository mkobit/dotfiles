package dotfilesbuild.shell

import com.mkobit.gradle.test.kotlin.testkit.runner.build
import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import org.junitpioneer.jupiter.TempDirectory
import strikt.api.expectThat
import strikt.assertions.contains
import testsupport.gradle.newGradleRunner
import testsupport.strikt.content
import testsupport.strikt.doesNotExist
import testsupport.strikt.exists
import testsupport.strikt.isDirectory
import testsupport.strikt.projectDir
import testsupport.strikt.resolvePath
import java.nio.file.Path

@ExtendWith(TempDirectory::class)
internal class ManagedBinPluginTest {
  @Test
  internal fun `managed bin directory is created and exported in the PATH in zshell file`(@TempDirectory.TempDir tempDir: Path) {
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

    runner.build("generateZshrcFile").let { result ->
      expectThat(result) {
        projectDir.resolvePath("build/managed_bin")
            .exists()
            .isDirectory()
        projectDir.resolvePath("build/zsh/generated_zshrc")
            .exists()
            .content
            .contains("""export PATH="${'$'}PATH:${result.projectDir.resolve("build/managed_bin").toAbsolutePath()}" # dotfiles: dotfiles managed bin files""")
      }
    }

    runner.build("clean").let { result ->
      expectThat(result) {
        projectDir.resolvePath("build/managed_bin")
            .doesNotExist()
      }
    }
  }
}
