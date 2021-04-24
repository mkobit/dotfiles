package dotfilesbuild.utilities

import org.gradle.api.model.ObjectFactory
import org.gradle.api.provider.Provider
import org.gradle.kotlin.dsl.property

inline fun <reified T> ObjectFactory.property(value: T?) =
  property<T>().also { it.set(value) }

inline fun <reified T> ObjectFactory.property(provider: Provider<out T>) =
  property<T>().also { it.set(provider) }
