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

internal class SourceControlledBinPluginTest {
  @Test
  internal fun `PATH environment variable exported with link to bin path in project`(@TempDir tempDir: Path) {
    val runner = newGradleRunner(tempDir) {
      setupProjectDir {
        "build.gradle.kts" {
          content = """
            plugins {
              id("dotfilesbuild.shell.source-bin")
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
            .contains("""export PATH="${'$'}PATH:${result.projectDir.resolve("bin").toAbsolutePath()}" # dotfiles: source controlled bin files""")
      }
    }
  }
}
