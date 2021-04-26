package io.mkobit.ssh.script

import io.mkobit.ssh.config.HostConfig
import java.nio.file.Path
import kotlin.reflect.KTypeProjection
import kotlin.reflect.full.createType
import kotlin.script.experimental.annotations.KotlinScript
import kotlin.script.experimental.api.ScriptCompilationConfiguration
import kotlin.script.experimental.api.ScriptEvaluationConfiguration
import kotlin.script.experimental.api.defaultImports
import kotlin.script.experimental.api.hostConfiguration
import kotlin.script.experimental.api.providedProperties
import kotlin.script.experimental.jvm.dependenciesFromCurrentContext
import kotlin.script.experimental.jvm.jvm

@KotlinScript(
  fileExtension = "ssh.kts",
  compilationConfiguration = SshConfigScriptCompilationConfiguration::class,
  evaluationConfiguration = SshConfigScriptEvaluationConfiguration::class,
)
interface SshConfigScript

object SshConfigScriptCompilationConfiguration : ScriptCompilationConfiguration({
  jvm {
    // configure dependencies for compilation, they should contain at least the script base class and
    // its dependencies
    // variant 1: try to extract current classpath and take only a path to the specified "script.jar"
    dependenciesFromCurrentContext(
      "ssh-config-generator",
      "ssh-script-definition", /* script library jar name (exact or without a version) */
    )
    // variant 2: try to extract current classpath and use it for the compilation without filtering
//            dependenciesFromCurrentContext(wholeClasspath = true)
    // variant 3: try to extract a classpath from a particular classloader (or Thread.contextClassLoader by default)
    // filtering as in the variat 1 is supported too
//            dependenciesFromClassloader(classLoader = SimpleScript::class.java.classLoader, wholeClasspath = true)
    // variant 4: explicit classpath
//            updateClasspath(listOf(File("/path/to/jar")))

    defaultImports(
      HostConfig::class,
    )

    val configurationsType = Map::class.createType(
      arguments = listOf(
        KTypeProjection.invariant(Path::class.createType()),
        KTypeProjection.invariant(
          List::class.createType(
            arguments = listOf(KTypeProjection.invariant(HostConfig::class.createType()))
          )
        ),
      )
    )
    providedProperties(
        "configurations" to configurationsType
    )
  }
})

class SshConfigScriptEvaluationConfiguration : ScriptEvaluationConfiguration({
  providedProperties(
    "configurations" to emptyMap<Path, List<HostConfig>>()
  )
})
