package testsupport.strikt

import org.gradle.testkit.runner.BuildTask
import org.gradle.testkit.runner.TaskOutcome
import strikt.api.Assertion

fun <T : BuildTask> Assertion.Builder<T>.hasOutcome(outcome: TaskOutcome) =
    assert("has outcome %s", outcome) {
      when {
        it.outcome == outcome -> pass()
        else -> fail(it, "was outcome %s")
      }
    }

val <T : BuildTask> Assertion.Builder<T>.taskPath: Assertion.Builder<String>
  get() = get("task path", BuildTask::getPath)

val <T : BuildTask> Assertion.Builder<T>.outcome: Assertion.Builder<TaskOutcome>
  get() = get("task path", BuildTask::getOutcome)

fun <T : BuildTask> Assertion.Builder<T>.isSuccessful() = hasOutcome(TaskOutcome.SUCCESS)
fun <T : BuildTask> Assertion.Builder<T>.isFailed() = hasOutcome(TaskOutcome.FAILED)
fun <T : BuildTask> Assertion.Builder<T>.isFromCache() = hasOutcome(TaskOutcome.FROM_CACHE)
fun <T : BuildTask> Assertion.Builder<T>.isNoSource() = hasOutcome(TaskOutcome.NO_SOURCE)
fun <T : BuildTask> Assertion.Builder<T>.isSkipped() = hasOutcome(TaskOutcome.SKIPPED)
fun <T : BuildTask> Assertion.Builder<T>.isUpToDate() = hasOutcome(TaskOutcome.UP_TO_DATE)
