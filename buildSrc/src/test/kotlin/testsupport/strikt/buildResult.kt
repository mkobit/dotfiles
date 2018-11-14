package testsupport.strikt

import org.gradle.testkit.runner.BuildResult
import org.gradle.testkit.runner.BuildTask
import org.gradle.testkit.runner.TaskOutcome
import strikt.api.Assertion

val Assertion.Builder<out BuildResult>.output: Assertion.Builder<String>
  get() = get("build output", BuildResult::getOutput)

val Assertion.Builder<out BuildResult>.tasks: Assertion.Builder<List<BuildTask>>
  get() = get("build output", BuildResult::getTasks)

fun Assertion.Builder<out BuildResult>.task(path: String): Assertion.Builder<BuildTask?> =
  get("task at path $path") { task(path) }

fun Assertion.Builder<out BuildResult>.taskPaths(outcome: TaskOutcome): Assertion.Builder<List<String>> =
    get("task paths with outcome $outcome") { taskPaths(outcome) }

fun Assertion.Builder<out BuildResult>.tasks(outcome: TaskOutcome): Assertion.Builder<List<BuildTask>> =
    get("task paths with outcome $outcome") { tasks(outcome) }

val Assertion.Builder<out BuildTask>.taskPath: Assertion.Builder<String>
  get() = get("task path", BuildTask::getPath)

val Assertion.Builder<out BuildTask>.outcome: Assertion.Builder<TaskOutcome>
  get() = get("task path", BuildTask::getOutcome)

fun Assertion.Builder<out BuildTask>.hasOutcome(outcome: TaskOutcome) =
    assert("has outcome %s", outcome) {
      when {
        it.outcome == outcome -> pass()
        else -> fail(it, "was outcome %s")
      }
    }
