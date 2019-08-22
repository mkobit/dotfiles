package dotfilesbuild.io.file

import com.mkobit.gradle.test.kotlin.io.FileContext
import com.mkobit.gradle.test.kotlin.testkit.runner.build
import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import strikt.api.expectThat
import strikt.assertions.isEqualTo
import strikt.assertions.isNotNull
import strikt.assertions.resolve
import strikt.gradle.testkit.isSuccess
import strikt.gradle.testkit.isUpToDate
import strikt.gradle.testkit.task
import testsupport.gradle.newGradleRunner
import testsupport.strikt.content
import testsupport.strikt.projectDir
import java.nio.file.Path

internal class CalculateChecksumTest {

  companion object {
    private fun FileContext.DirectoryContext.kotlinBuildFile() {
      "build.gradle.kts" {
        content = """
          import dotfilesbuild.io.file.CalculateChecksum
          
          plugins {
            id("dotfilesbuild.internal.noop")
          }
          
          val calculate by tasks.registering(CalculateChecksum::class) {
            digestFiles.from(files("files"))
            checksums.set(layout.buildDirectory.dir("checksums"))
          }
        """.trimIndent().toByteArray()
      }
    }
  }

  @Test
  internal fun `can calculate sha256 checksum for single file`(@TempDir directory: Path) {
    val result = newGradleRunner(directory).setupProjectDir {
      "files" / {
        "file1.txt" {
          append("abc")
          appendNewline()
        }
      }
      kotlinBuildFile()
    }.build("calculate")

    expectThat(result)
      .projectDir
      .resolve("build/checksums")
      .and {
        resolve("file1.txt.sha256").content.isEqualTo("edeaaff3f1774ad2888673770c6d64097e391bc362d7d6fb34982ddf0efd18cb")
      }
  }

  @Test
  internal fun `can calculate sha256 checksum for multiple files in diferent nested contexts`(@TempDir directory: Path) {
    val result = newGradleRunner(directory).setupProjectDir {
      "files" / {
        "file1.txt" {
          append("abc")
          appendNewline()
        }
        "file2.txt" {
          append("123")
          appendNewline()
        }
        "file3.txt" {
          append("!@#")
          appendNewline()
        }
        "dir" / {
          "file4.txt" {
            append("ABC")
            appendNewline()
          }
        }
      }
      kotlinBuildFile()
    }.build("calculate")

    expectThat(result)
      .projectDir
      .resolve("build/checksums")
      .and {
        resolve("file1.txt.sha256")
          .content
          .isEqualTo("edeaaff3f1774ad2888673770c6d64097e391bc362d7d6fb34982ddf0efd18cb")
        resolve("file2.txt.sha256")
          .content
          .isEqualTo("181210f8f9c779c26da1d9b2075bde0127302ee0e3fca38c9a83f5b1dd8e5d3b")
        resolve("file3.txt.sha256")
          .content
          .isEqualTo("777e06a9752b81e8991a3d057e9c70fa21234666f76915c54e4bd61a91fd0ce1")
        resolve("dir")
          .resolve("file4.txt.sha256")
          .content
          .isEqualTo("8470d56547eea6236d7c81a644ce74670ca0bbda998e13c629ef6bb3f0d60b69")
      }
  }

  @Test
  internal fun `task is up-to-date after first execution`(@TempDir directory: Path) {
    val runner = newGradleRunner(directory)
    runner.setupProjectDir {
      "files" / {
        "file1.txt" {
          append("abc")
          appendNewline()
        }
      }
      kotlinBuildFile()
    }.build("calculate").let { firstResult ->
      expectThat(firstResult).task(":calculate").isNotNull().isSuccess()
    }

    runner.build("calculate").let { secondResult ->
      expectThat(secondResult).task(":calculate").isNotNull().isUpToDate()
    }
  }
}
