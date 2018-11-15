package dotfilesbuild.shell

import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import org.junitpioneer.jupiter.TempDirectory
import testsupport.gradle.newGradleRunner
import java.nio.file.Path

@ExtendWith(TempDirectory::class)
internal class ManagedBinPluginTest {
  @Test
  internal fun `managed bin directory is created and exported in the PATH in zshell file`(@TempDirectory.TempDir projectDir: Path) {
    val runner = newGradleRunner(projectDir) {
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
  }
}
