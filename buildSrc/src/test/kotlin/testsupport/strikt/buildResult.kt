package testsupport.strikt

import org.gradle.testkit.runner.BuildResult
import org.gradle.testkit.runner.BuildTask
import org.gradle.testkit.runner.TaskOutcome
import strikt.api.Assertion

val <T : BuildResult> Assertion.Builder<T>.output: Assertion.Builder<String>
  get() = get("build output", BuildResult::getOutput)

val <T : BuildResult> Assertion.Builder<T>.tasks: Assertion.Builder<List<BuildTask>>
  get() = get("build output", BuildResult::getTasks)

fun <T : BuildResult> Assertion.Builder<T>.task(path: String): Assertion.Builder<BuildTask?> =
  get("task at path $path") { task(path) }

fun <T : BuildResult> Assertion.Builder<T>.taskPaths(outcome: TaskOutcome): Assertion.Builder<List<String>> =
    get("task paths with outcome $outcome") { taskPaths(outcome) }

fun <T : BuildResult> Assertion.Builder<T>.tasks(outcome: TaskOutcome): Assertion.Builder<List<BuildTask>> =
    get("task paths with outcome $outcome") { tasks(outcome) }
