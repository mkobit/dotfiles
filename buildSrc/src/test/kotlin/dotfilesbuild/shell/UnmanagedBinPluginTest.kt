package dotfilesbuild.shell

import com.mkobit.gradle.test.kotlin.testkit.runner.build
import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import org.junitpioneer.jupiter.TempDirectory
import strikt.api.expectThat
import strikt.assertions.isEmpty
import testsupport.gradle.newGradleRunner
import testsupport.strikt.content
import testsupport.strikt.exists
import testsupport.strikt.isDirectory
import testsupport.strikt.isRegularFile
import testsupport.strikt.projectDir
import testsupport.strikt.resolvePath
import java.nio.file.Path

@ExtendWith(TempDirectory::class)
internal class UnmanagedBinPluginTest {
  @Test
  internal fun `directory is created and not removed by clean`(@TempDirectory.TempDir tempDir: Path) {
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

    runner.build("makeUnmanagedBinDirectory").let { result ->
      expectThat(result) {
        projectDir.resolvePath(".unmanaged_bin")
            .exists()
            .isDirectory()
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
