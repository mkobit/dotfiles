package testsupport

import com.mkobit.gradle.test.kotlin.testkit.runner.projectDirPath
import org.gradle.testkit.runner.GradleRunner
import java.nio.file.Path

fun newGradleRunner(path: Path) = GradleRunner.create().apply {
  projectDirPath = path
  withPluginClasspath()
}
