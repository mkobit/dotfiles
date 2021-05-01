package io.mkobit.git.host

import io.mkobit.git.config.Section
import io.mkobit.git.script.GitConfigScript
import java.nio.file.Path
import kotlin.io.path.ExperimentalPathApi
import kotlin.script.experimental.api.ResultValue
import kotlin.script.experimental.api.providedProperties
import kotlin.script.experimental.api.valueOr
import kotlin.script.experimental.host.toScriptSource
import kotlin.script.experimental.jvmhost.BasicJvmScriptingHost
import kotlin.script.experimental.jvmhost.createJvmCompilationConfigurationFromTemplate
import kotlin.script.experimental.jvmhost.createJvmEvaluationConfigurationFromTemplate

@ExperimentalPathApi
fun execute(scriptFile: Path, configurations: Map<Path, List<Section>>): Map<Path, List<Section>> {
  val result = BasicJvmScriptingHost().eval(
    scriptFile.toFile().toScriptSource(),
    createJvmCompilationConfigurationFromTemplate<GitConfigScript>(),
    createJvmEvaluationConfigurationFromTemplate<GitConfigScript> {
      providedProperties(
        "configurations" to configurations,
      )
    }
  )

  val evalResult = result.valueOr { throw RuntimeException("failure: $$it",) }
  when (val returnValue = evalResult.returnValue) {
    is ResultValue.Value -> {
      @Suppress("UNCHECKED_CAST")
      return returnValue.value as Map<Path, List<Section>>
    }
    is ResultValue.Unit -> throw IllegalArgumentException("Script $scriptFile must return a Map<Path, Section>, but returned unit")
    is ResultValue.Error -> throw RuntimeException("Error processing script", returnValue.error)
    ResultValue.NotEvaluated -> throw IllegalStateException("This should not happen")
  }
}

