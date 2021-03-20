@file:JvmName("Main")

package dotfiles.shell.git

import com.typesafe.config.Config
import com.typesafe.config.ConfigException
import com.typesafe.config.ConfigFactory
import io.mkobit.git.config.Include
import io.mkobit.git.config.Section
import io.mkobit.git.config.asText
import picocli.CommandLine
import java.nio.file.Path
import java.util.concurrent.Callable
import kotlin.io.path.ExperimentalPathApi
import kotlin.io.path.createDirectories
import kotlin.io.path.div
import kotlin.io.path.writeText
import kotlin.system.exitProcess

@CommandLine.Command(
  name = "generateGitConfig",
  mixinStandardHelpOptions = true,
)
@ExperimentalPathApi
internal class GenerateGitConfig : Callable<Int> {

  @CommandLine.Option(
    names = ["--output-dir"],
    required = true
  )
  lateinit var outputDir: Path

  @CommandLine.Option(
    names = ["--global-excludes-file"],
    required = true
  )
  lateinit var globalExcludesFile: Path

  @CommandLine.Option(
    names = ["--work-dir"],
    required = true
  )
  lateinit var workDir: Path

  @CommandLine.Option(
    names = ["--code-lab-dir"],
    required = true
  )
  lateinit var codeLabDir: Path

  @CommandLine.Option(
    names = ["--personal-dir"],
    required = true
  )
  lateinit var personalDir: Path

  @CommandLine.Option(
    names = ["--dotfiles-dir"],
    required = true
  )
  lateinit var dotfilesDir: Path

  @CommandLine.Option(
    names = ["--config-file"],
    required = false,
  )
  lateinit var configFiles: List<Path>

  override fun call(): Int {
    val hocon = hoconConfig(configFiles)
    val general = gitConfigFileFor(outputDir / "general")
    general.writeText(generalGitConfig(globalExcludesFile).asText())

    val personal = gitConfigFileFor(outputDir / "personal")
    personal.writeText(personalGitConfig().asText())

    val work = workGitConfig(hocon).let { workConfig ->
      if (workConfig.isNotEmpty()) {
        gitConfigFileFor(outputDir / "work").also {
          it.writeText(workConfig.asText())
        }
      } else {
        null
      }
    }

    val includes = gitConfigFileFor(outputDir / "includes")
    includes.writeText(
      (
        listOf(
          Include(path = general),
          Include(personal).ifGitDir(dotfilesDir),
          Include(personal).ifGitDir(personalDir),
          Include(personal).ifGitDir(codeLabDir),
        ) + listOfNotNull(work).map {
          Include(it).ifGitDir(workDir)
        }
      ).asText()
    )
    return 0
  }

  private fun gitConfigFileFor(path: Path): Path =
    path.createDirectories() / ".gitconfig"
}

private fun hoconConfig(files: List<Path>): Config =
  files
    .map { it.toFile() }
    .map { ConfigFactory.parseFile(it) }
    .fold(ConfigFactory.empty()) { accumulated, config -> accumulated.withFallback(config) }

@ExperimentalPathApi
fun main(args: Array<String>): Unit = exitProcess(CommandLine(GenerateGitConfig()).execute(*args))
