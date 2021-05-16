package io.mkobit.ssh.script

import io.mkobit.ssh.config.HostConfig
import io.mkobit.ssh.config.SshConfig
import java.nio.file.Path
import kotlin.io.path.ExperimentalPathApi
import kotlin.reflect.typeOf
import kotlin.script.experimental.annotations.KotlinScript
import kotlin.script.experimental.api.ScriptCompilationConfiguration
import kotlin.script.experimental.api.ScriptEvaluationConfiguration
import kotlin.script.experimental.api.defaultImports
import kotlin.script.experimental.api.providedProperties
import kotlin.script.experimental.jvm.dependenciesFromCurrentContext
import kotlin.script.experimental.jvm.jvm

@ExperimentalStdlibApi
@KotlinScript(
  fileExtension = "ssh.kts",
  compilationConfiguration = SshConfigScriptCompilationConfiguration::class,
  evaluationConfiguration = SshConfigScriptEvaluationConfiguration::class,
)
@ExperimentalPathApi
interface SshConfigScript

@ExperimentalStdlibApi
object SshConfigScriptCompilationConfiguration : ScriptCompilationConfiguration({
  defaultImports(
    HostConfig::class,
    SshConfig::class,
  )

  defaultImports(
    "kotlin.io.path.Path",
    "kotlin.io.path.div",
    "io.mkobit.ssh.config.HostConfig",
    "io.mkobit.ssh.config.SshConfig",
  )

  providedProperties(
    "configurations" to typeOf<Map<Path, List<HostConfig>>>(),
  )
  jvm {
    // configure dependencies for compilation, they should contain at least the script base class and
    // its dependencies
    // variant 1: try to extract current classpath and take only a path to the specified "script.jar"
//    dependenciesFromCurrentContext(
//      "kotlin-stdlib-jdk7", // kotlin.io.path.Path
//      "ssh-config-generator",
//      "ssh-script-definition", /* script library jar name (exact or without a version) */
//    )
    dependenciesFromCurrentContext(wholeClasspath = true)
    // variant 2: try to extract current classpath and use it for the compilation without filtering
//            dependenciesFromCurrentContext(wholeClasspath = true)
    // variant 3: try to extract a classpath from a particular classloader (or Thread.contextClassLoader by default)
    // filtering as in the variat 1 is supported too
//            dependenciesFromClassloader(classLoader = SimpleScript::class.java.classLoader, wholeClasspath = true)
    // variant 4: explicit classpath
//            updateClasspath(listOf(File("/path/to/jar")))
  }
})

class SshConfigScriptEvaluationConfiguration : ScriptEvaluationConfiguration({
  providedProperties(
    "configurations" to emptyMap<Path, List<HostConfig>>()
  )
})
