package io.mkobit.ssh.host

import io.mkobit.ssh.script.SshConfigScript
import java.nio.file.Path
import kotlin.script.experimental.api.EvaluationResult
import kotlin.script.experimental.api.ResultWithDiagnostics
import kotlin.script.experimental.host.createEvaluationConfigurationFromTemplate
import kotlin.script.experimental.host.toScriptSource
import kotlin.script.experimental.jvmhost.BasicJvmScriptingHost
import kotlin.script.experimental.jvmhost.createJvmCompilationConfigurationFromTemplate
import kotlin.script.experimental.jvmhost.createJvmEvaluationConfigurationFromTemplate

fun evalFile(scriptFile: Path): ResultWithDiagnostics<EvaluationResult> {
  return BasicJvmScriptingHost().eval(
    scriptFile.toFile().toScriptSource(),
    createJvmCompilationConfigurationFromTemplate<SshConfigScript>(),
    createJvmEvaluationConfigurationFromTemplate<SshConfigScript>()
  )
}
