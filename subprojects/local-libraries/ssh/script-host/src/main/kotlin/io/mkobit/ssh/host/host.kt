package io.mkobit.ssh.host

import io.mkobit.ssh.script.SshConfigScript
import java.nio.file.Path
import kotlin.script.experimental.api.EvaluationResult
import kotlin.script.experimental.api.ResultWithDiagnostics
import kotlin.script.experimental.host.toScriptSource
import kotlin.script.experimental.jvm.dependenciesFromCurrentContext
import kotlin.script.experimental.jvm.jvm
import kotlin.script.experimental.jvmhost.BasicJvmScriptingHost
import kotlin.script.experimental.jvmhost.createJvmCompilationConfigurationFromTemplate

fun evalFile(scriptFile: Path): ResultWithDiagnostics<EvaluationResult> {
  val compilationConfiguration = createJvmCompilationConfigurationFromTemplate<SshConfigScript> {
    jvm {
      // configure dependencies for compilation, they should contain at least the script base class and
      // its dependencies
      // variant 1: try to extract current classpath and take only a path to the specified "script.jar"
      dependenciesFromCurrentContext(
        "script-definition" /* script library jar name (exact or without a version) */
      )
      // variant 2: try to extract current classpath and use it for the compilation without filtering
//            dependenciesFromCurrentContext(wholeClasspath = true)
      // variant 3: try to extract a classpath from a particular classloader (or Thread.contextClassLoader by default)
      // filtering as in the variat 1 is supported too
//            dependenciesFromClassloader(classLoader = SimpleScript::class.java.classLoader, wholeClasspath = true)
      // variant 4: explicit classpath
//            updateClasspath(listOf(File("/path/to/jar")))
    }
  }

  return BasicJvmScriptingHost().eval(
    scriptFile.toFile().toScriptSource(),
    compilationConfiguration,
    null
  )
}
