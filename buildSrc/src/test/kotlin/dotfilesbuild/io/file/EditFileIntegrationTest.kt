package dotfilesbuild.io.file

import com.mkobit.gradle.test.assertj.GradleAssertions.assertThat
import com.mkobit.gradle.test.kotlin.io.Original
import com.mkobit.gradle.test.kotlin.testkit.runner.build
import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import org.junitpioneer.jupiter.TempDirectory
import testsupport.gradle.newGradleRunner
import java.nio.file.Path

@ExtendWith(TempDirectory::class)
internal class EditFileIntegrationTest {
  @Test
  internal fun `edit the content of a file with multiple actions`(@TempDirectory.TempDir projectDir: Path) {
    val result = newGradleRunner(projectDir).setupProjectDir {
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
        append("""
          first
          second
          third
          forth
          fifth
          sixth
        """.trimIndent())
        appendNewline()
      }
    }.build("convergeFile")

    assertThat(result)
        .hasTaskSuccessAtPath(":convergeFile")
    assertThat(result.projectDir.resolve("myfile.txt"))
        .hasContent("""
          first
          second
          third
          fifth
          sixth
          seventh
          eighth
        """.trimIndent() + System.lineSeparator())
  }

  @Test
  internal fun `editing a file where no actions are applied result in an UP-TO-DATE task and the file is unchanged`(@TempDirectory.TempDir projectDir: Path) {
    val originalText = """
      first
      second
      third
    """.trimIndent()
    val gradleRunner = newGradleRunner(projectDir)

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

    val result = gradleRunner.build("convergeFile")

    assertThat(result)
        .hasTaskUpToDateAtPath(":convergeFile")
    assertThat(result.projectDir.resolve("myfile.txt"))
        .hasContent(originalText)
  }

  @Test
  internal fun `editing a file with no actions results in empty file being created`(@TempDirectory.TempDir projectDir: Path) {
    val gradleRunner = newGradleRunner(projectDir)

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

    val result = gradleRunner.build("convergeFile")

    assertThat(result)
        .hasTaskUpToDateAtPath(":convergeFile")
    assertThat(result.projectDir.resolve("myfile.txt"))
        .isRegularFile()
        .hasContent("")
  }
}
