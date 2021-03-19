@file:JvmName("Main")

package dotfiles.shell.ssh

import picocli.CommandLine
import java.nio.file.Path
import java.util.concurrent.Callable
import kotlin.io.path.ExperimentalPathApi
import kotlin.io.path.div
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

  lateinit var externalConfigurations: List<Path>

  override fun call(): Int {
    val sshd = outputDir / "config.d"

    return 0
  }
}

@ExperimentalPathApi
fun main(args: Array<String>): Unit = exitProcess(CommandLine(GenerateSshConfig()).execute(*args))
