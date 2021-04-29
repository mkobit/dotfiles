package io.mkobit.git.host

import io.mkobit.git.script.GitConfigScript
import java.nio.file.Path
import kotlin.script.experimental.api.EvaluationResult
import kotlin.script.experimental.api.ResultWithDiagnostics
import kotlin.script.experimental.host.toScriptSource
import kotlin.script.experimental.jvmhost.BasicJvmScriptingHost
import kotlin.script.experimental.jvmhost.createJvmCompilationConfigurationFromTemplate
import kotlin.script.experimental.jvmhost.createJvmEvaluationConfigurationFromTemplate

fun evalFile(scriptFile: Path): ResultWithDiagnostics<EvaluationResult> {
  return BasicJvmScriptingHost().eval(
    scriptFile.toFile().toScriptSource(),
    createJvmCompilationConfigurationFromTemplate<GitConfigScript>(),
    createJvmEvaluationConfigurationFromTemplate<GitConfigScript>()
  )
}
