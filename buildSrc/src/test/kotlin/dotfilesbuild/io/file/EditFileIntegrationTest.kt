package dotfilesbuild.io.file

import com.mkobit.gradle.test.kotlin.io.Original
import com.mkobit.gradle.test.kotlin.testkit.runner.build
import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import strikt.api.expectThat
import strikt.assertions.allLines
import strikt.assertions.containsExactly
import strikt.assertions.isEqualTo
import strikt.assertions.isNotNull
import strikt.assertions.isRegularFile
import strikt.assertions.resolve
import strikt.gradle.testkit.isSuccess
import strikt.gradle.testkit.isUpToDate
import strikt.gradle.testkit.task
import testsupport.gradle.newGradleRunner
import testsupport.strikt.content
import testsupport.strikt.projectDir
import java.nio.file.Files
import java.nio.file.Path

internal class EditFileIntegrationTest {
  @Test
  internal fun `edit the content of a file with multiple actions`(@TempDir directory: Path) {
    val result = newGradleRunner(directory).setupProjectDir {
      "build.gradle"(content = Original) {
        append("""
          import dotfilesbuild.io.file.EditFile
          import dotfilesbuild.io.file.content.AppendIfNoLinesMatch
          import dotfilesbuild.io.file.content.AppendTextIfNotFound
          import dotfilesbuild.io.file.content.SearchTextDeleteLine
          import kotlin.jvm.functions.Function0

          plugins {
            id('dotfilesbuild.file-management')
          }

          tasks.create('convergeFile', EditFile) {
            file = layout.projectDirectory.file('myfile.txt')
            editActions = [
              new AppendIfNoLinesMatch(~/^sixth${'$'}/, { 'sixth' } as Function0),
              new AppendIfNoLinesMatch(~/^seventh${'$'}/, { 'seventh' } as Function0),
              new AppendTextIfNotFound({ 'first' } as Function0),
              new AppendTextIfNotFound({ 'eighth' } as Function0),
              new SearchTextDeleteLine(~/^ninth${'$'}/),
              new SearchTextDeleteLine(~/^forth${'$'}/),
            ]
          }
        """.trimIndent())
        appendNewline()
      }
      "myfile.txt"(content = Original) {
        append(
          """
            first
            second
            third
            forth
            fifth
            sixth
          """.trimIndent()
        )
        appendNewline()
      }
    }.build("convergeFile")

    println(Files.readAllLines(directory.resolve("myfile.txt")))
    println(Files.readAllBytes(directory.resolve("myfile.txt")).toString(Charsets.UTF_8))

    expectThat(result) {
      task(":convergeFile")
        .isNotNull()
        .isSuccess()
      projectDir
        .resolve("myfile.txt")
        .allLines()
        .containsExactly(
          "first",
          "second",
          "third",
          "fifth",
          "sixth",
          "seventh",
          "eighth"
        )
    }
  }

  @Test
  internal fun `editing a file where no actions are applied result in an UP-TO-DATE task and the file is unchanged`(@TempDir directory: Path) {
    val originalText = """
      first
      second
      third
    """.trimIndent()
    val gradleRunner = newGradleRunner(directory)

    gradleRunner.setupProjectDir {
      "build.gradle"(content = Original) {
        append("""
          import dotfilesbuild.io.file.EditFile
          import dotfilesbuild.io.file.content.AppendIfNoLinesMatch
          import dotfilesbuild.io.file.content.AppendTextIfNotFound
          import dotfilesbuild.io.file.content.SearchTextDeleteLine
          import kotlin.jvm.functions.Function0

          plugins {
            id('dotfilesbuild.file-management')
          }

          tasks.create('convergeFile', EditFile) {
            file = layout.projectDirectory.file('myfile.txt')
            editActions = [
              new AppendIfNoLinesMatch(~/^first${'$'}/, { 'first' } as Function0),
              new AppendTextIfNotFound({ 'second' } as Function0),
              new SearchTextDeleteLine(~/^tenth${'$'}/),
            ]
          }
        """.trimIndent())
        appendNewline()
      }
      "myfile.txt"(content = originalText)
    }.build("convergeFile")

    expectThat(gradleRunner.build("convergeFile")) {
      task(":convergeFile")
        .isNotNull()
        .isUpToDate()

      projectDir
        .resolve("myfile.txt")
        .isRegularFile()
        .content
        .isEqualTo(originalText)
    }
  }

  @Test
  internal fun `editing a file with no actions results in empty file being created`(@TempDir directory: Path) {
    val gradleRunner = newGradleRunner(directory)

    gradleRunner.setupProjectDir {
      "build.gradle"(content = Original) {
        append("""
          import dotfilesbuild.io.file.EditFile
          import kotlin.jvm.functions.Function0

          plugins {
            id('dotfilesbuild.file-management')
          }

          tasks.create('convergeFile', EditFile) {
            file = layout.projectDirectory.file('myfile.txt')
          }
        """.trimIndent())
        appendNewline()
      }
    }.build("convergeFile")

    expectThat(gradleRunner.build("convergeFile")) {
      task(":convergeFile")
        .isNotNull()
        .isUpToDate()

      projectDir
        .resolve("myfile.txt")
        .isRegularFile()
        .content
        .isEqualTo("")
    }
  }
}
