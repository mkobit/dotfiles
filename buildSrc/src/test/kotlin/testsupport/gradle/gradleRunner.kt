package testsupport.gradle

import org.gradle.testkit.runner.GradleRunner
import java.nio.file.Path

fun newGradleRunner(path: Path, configuration: GradleRunner.() -> Unit = {}): GradleRunner = GradleRunner.create().apply {
  withProjectDir(path.toFile())
  withPluginClasspath()
  configuration()
}
