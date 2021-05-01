@file:JvmName("Main")

package dotfiles.shell.ssh

import io.mkobit.ssh.config.SshConfig
import io.mkobit.ssh.config.asText
import io.mkobit.ssh.host.execute
import picocli.CommandLine
import java.nio.file.Path
import kotlin.io.path.Path
import java.util.concurrent.Callable
import kotlin.io.path.ExperimentalPathApi
import kotlin.io.path.createDirectories
import kotlin.io.path.div
import kotlin.io.path.writeText
import kotlin.system.exitProcess

@CommandLine.Command(
  name = "generateSshConfig",
  mixinStandardHelpOptions = true,
)
@ExperimentalPathApi
internal class GenerateSshConfig : Callable<Int> {

  @CommandLine.Option(
    names = ["--output-dir"],
    required = true
  )
  lateinit var outputDir: Path

  @CommandLine.Option(
    names = ["--config-file"],
    required = false,
  )
  var configFiles: List<Path> = emptyList()

  override fun call(): Int {
    val sshd = outputDir / "config.d"
    sshd.createDirectories()
    val commonAll = Path("common_all_hosts")
    val mkobit = Path("mkobit_github")

    val configurations = mapOf(
      mkobit to mkobitGithub(),
      commonAll to commonAllHostsConfig(),
    ).let {
      configFiles.fold(it) { accumulator, scriptPath ->
        execute(scriptPath, accumulator)
      }
    }

    configurations
      .mapKeys { (path, _) -> sshd / path }
      .onEach { (path, _) -> require(path.isChildOf(outputDir)) { "$path must be a child of $outputDir"} }
      .forEach { (path, hostConfigs) ->
        path.parent.createDirectories()
        path.writeText(hostConfigs.asText())
      }

    val includes = outputDir / "includes"
    includes.writeText(
      SshConfig(
        includes = configurations.keys.map { sshd / it }
      ).asText()
    )

    return 0
  }
}

private fun Path.isChildOf(path: Path): Boolean = normalize().startsWith(path.normalize())

@ExperimentalPathApi
fun main(args: Array<String>): Unit = exitProcess(CommandLine(GenerateSshConfig()).execute(*args))
