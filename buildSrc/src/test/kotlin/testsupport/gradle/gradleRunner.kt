package testsupport.gradle

import com.mkobit.gradle.test.kotlin.testkit.runner.stacktrace
import org.gradle.testkit.runner.GradleRunner
import java.nio.file.Path

fun newGradleRunner(path: Path, configuration: GradleRunner.() -> Unit = {}): GradleRunner = GradleRunner.create().apply {
  withProjectDir(path.toFile())
  withPluginClasspath()
  stacktrace = true
  configuration()
}
