package dotfilesbuild.kubernetes

import com.mkobit.gradle.test.kotlin.testkit.runner.build
import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import testsupport.gradle.newGradleRunner
import java.nio.file.Path

internal class KubectlProgramPluginTest {
  @Test
  internal fun `can configure kubectl version`(@TempDir tempDir: Path) {
    val runner = newGradleRunner(tempDir) {
      setupProjectDir {
        "build.gradle.kts" {
          content = """
            plugins {
              id("dotfilesbuild.kubernetes.kubectl-managed-binary")
            }
            kubectl {
              version.set("v1.12.2")
            }
          """.trimIndent().toByteArray()
        }
      }
    }

//    expectThat(
//        catching {
          runner.build("help")
//        }
//    ).isNull()
  }
}
