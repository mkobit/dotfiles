package io.mkobit.testing.kotest.scope

import io.kotest.core.TestConfiguration
import io.kotest.core.test.TestCase
import io.kotest.core.test.TestResult
import kotlin.properties.ReadOnlyProperty

fun <T> TestConfiguration.generatePerTest(
  create: suspend (TestCase) -> T
): ReadOnlyProperty<Any?, T> = generatePerTest(create) { _, _ -> }

fun <T> TestConfiguration.generatePerTest(
   create: suspend (TestCase) -> T,
  destroy: suspend T.(TestCase, TestResult) -> Unit,
): ReadOnlyProperty<Any?, T> {
  val property = ResettableScopedValue<T>()
  beforeTest {
    val fromCreate = create(it)
    property.setTo(fromCreate)
  }
  afterTest { (testCase, testResult) ->
    property.value.destroy(testCase, testResult)
    property.reset()
  }

  return property
}
