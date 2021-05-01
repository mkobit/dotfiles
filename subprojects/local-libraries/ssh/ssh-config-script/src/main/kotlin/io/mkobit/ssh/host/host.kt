package io.mkobit.ssh.host

import io.mkobit.ssh.config.HostConfig
import io.mkobit.ssh.script.SshConfigScript
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
fun main() {
  execute(kotlin.io.path.Path("/Users/mikekobit/dotfiles/subprojects/local-libraries/ssh/ssh-config-script/testData/example.ssh.kts"), emptyMap())
}

@ExperimentalPathApi
fun execute(scriptFile: Path, configurations: Map<Path, List<HostConfig>>): Map<Path, List<HostConfig>> {
  val result = BasicJvmScriptingHost().eval(
    scriptFile.toFile().toScriptSource(),
    createJvmCompilationConfigurationFromTemplate<SshConfigScript>(),
    createJvmEvaluationConfigurationFromTemplate<SshConfigScript> {
      providedProperties(
        "configurations" to configurations,
      )
    }
  )

  val evalResult = result.valueOr { throw RuntimeException("failure: $$it",) }
  when (val returnValue = evalResult.returnValue) {
    is ResultValue.Value -> {
      @Suppress("UNCHECKED_CAST")
      return returnValue.value as Map<Path, List<HostConfig>>
    }
    is ResultValue.Unit -> throw IllegalArgumentException("Script $scriptFile must return a Map<Path, List<HostConfig>>, but returned unit")
    is ResultValue.Error -> throw RuntimeException("Error processing script", returnValue.error)
    ResultValue.NotEvaluated -> throw IllegalStateException("This should not happen")
  }
}

