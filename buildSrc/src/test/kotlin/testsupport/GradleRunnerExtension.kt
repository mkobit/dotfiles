package testsupport

import com.mkobit.gradle.test.kotlin.testkit.runner.projectDirPath
import com.mkobit.gradle.test.kotlin.testkit.runner.stacktrace
import org.gradle.testkit.runner.GradleRunner
import org.junit.jupiter.api.extension.AfterEachCallback
import org.junit.jupiter.api.extension.ExtensionContext
import org.junit.jupiter.api.extension.ParameterContext
import org.junit.jupiter.api.extension.ParameterResolver
import java.nio.file.Files
import java.nio.file.Path

class GradleRunnerExtension : ParameterResolver, AfterEachCallback {
  override fun supportsParameter(parameterContext: ParameterContext, extensionContext: ExtensionContext): Boolean =
      parameterContext.parameter.type == GradleRunner::class.java

  override fun resolveParameter(parameterContext: ParameterContext, extensionContext: ExtensionContext): Any {
    val temporaryDirectory: Path = extensionContext.store.getOrComputeIfAbsent(
        extensionContext,
        { Files.createTempDirectory(extensionContext.displayName) },
        Path::class.java
    )

    val gradleRunner = GradleRunner.create().apply {
      projectDirPath = temporaryDirectory
      stacktrace = true
      withPluginClasspath()
    }

    return gradleRunner
  }

  override fun afterEach(context: ExtensionContext) {
    val temporaryDirectory: Path = context.store.get(context, Path::class.java)!!
    temporaryDirectory.toFile().deleteRecursively()
  }

  private val ExtensionContext.store: ExtensionContext.Store
    get() = getStore(ExtensionContext.Namespace.create(GradleRunnerExtension::class.java, this))
}
