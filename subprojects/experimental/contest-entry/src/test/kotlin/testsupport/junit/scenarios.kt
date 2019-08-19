package testsupport.junit

import org.junit.jupiter.api.MethodOrderer
import org.junit.jupiter.api.TestInstance
import org.junit.jupiter.api.TestMethodOrder
import org.junit.jupiter.api.extension.ConditionEvaluationResult
import org.junit.jupiter.api.extension.ExecutionCondition
import org.junit.jupiter.api.extension.ExtendWith
import org.junit.jupiter.api.extension.ExtensionContext
import org.junit.jupiter.api.extension.TestExecutionExceptionHandler

// https://github.com/junit-team/junit5/issues/48 - Introduce first-class support for scenario tests
// https://github.com/junit-team/junit5/issues/431 - Introduce mechanism for terminating Dynamic Tests early

private class StepwiseExtension : ExecutionCondition, TestExecutionExceptionHandler {
  override fun handleTestExecutionException(context: ExtensionContext, throwable: Throwable) {
    val namespace = namespaceFor(context)
    val store = storeFor(context, namespace)
    store.put(StepwiseExtension::class, context.displayName)
    throw throwable
  }

  override fun evaluateExecutionCondition(context: ExtensionContext): ConditionEvaluationResult {
    val namespace = namespaceFor(context)
    val store = storeFor(context, namespace)
    val value: String? = store.get(StepwiseExtension::class, String::class.java)
    return if (value == null) {
      ConditionEvaluationResult.enabled("No test failures in stepwise tests")
    } else {
      ConditionEvaluationResult.disabled("Stepwise test disabled due to previous failure in '$value'")
    }
  }

  private fun namespaceFor(context: ExtensionContext): ExtensionContext.Namespace =
    ExtensionContext.Namespace.create(StepwiseExtension::class, context.parent)

  private fun storeFor(context: ExtensionContext, namespace: ExtensionContext.Namespace): ExtensionContext.Store =
    context.parent.get().getStore(namespace)
}


@TestInstance(TestInstance.Lifecycle.PER_CLASS)
@TestMethodOrder(MethodOrderer.OrderAnnotation::class)
@ExtendWith(StepwiseExtension::class)
@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.RUNTIME)
annotation class Stepwise
