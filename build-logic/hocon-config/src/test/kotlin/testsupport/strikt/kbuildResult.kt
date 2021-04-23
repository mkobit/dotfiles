package testsupport.strikt

import com.mkobit.gradle.test.kotlin.testkit.runner.KBuildResult
import strikt.api.Assertion
import java.nio.file.Path

val <T : KBuildResult> Assertion.Builder<T>.projectDir: Assertion.Builder<Path>
  get() = get("project directory", KBuildResult::projectDir)
