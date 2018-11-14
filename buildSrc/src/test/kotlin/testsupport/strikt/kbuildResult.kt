package testsupport.strikt

import com.mkobit.gradle.test.kotlin.testkit.runner.KBuildResult
import org.gradle.testkit.runner.BuildResult
import org.gradle.testkit.runner.BuildTask
import org.gradle.testkit.runner.TaskOutcome
import strikt.api.Assertion
import java.nio.file.Path

val Assertion.Builder<out KBuildResult>.projectDir: Assertion.Builder<Path>
  get() = get("project directory", KBuildResult::projectDir)
