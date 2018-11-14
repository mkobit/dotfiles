package testsupport.strikt

import org.gradle.testkit.runner.BuildTask
import org.gradle.testkit.runner.TaskOutcome
import strikt.api.Assertion

fun Assertion.Builder<out BuildTask>.isSuccessful() = hasOutcome(TaskOutcome.SUCCESS)
fun Assertion.Builder<out BuildTask>.isFailed() = hasOutcome(TaskOutcome.FAILED)
fun Assertion.Builder<out BuildTask>.isFromCache() = hasOutcome(TaskOutcome.FROM_CACHE)
fun Assertion.Builder<out BuildTask>.isNoSource() = hasOutcome(TaskOutcome.NO_SOURCE)
fun Assertion.Builder<out BuildTask>.isSkipped() = hasOutcome(TaskOutcome.SKIPPED)
fun Assertion.Builder<out BuildTask>.isUpToDate() = hasOutcome(TaskOutcome.UP_TO_DATE)
