package dotfilesbuild.shell

import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import org.junitpioneer.jupiter.TempDirectory
import testsupport.gradle.newGradleRunner
import java.nio.file.Path

@ExtendWith(TempDirectory::class)
internal class SourceControlledBinPluginTest {
  @Test
  internal fun `PATH environment variable exported with link to bin path in project`(@TempDirectory.TempDir projectDir: Path) {
    val runner = newGradleRunner(projectDir) {
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
  }
}
