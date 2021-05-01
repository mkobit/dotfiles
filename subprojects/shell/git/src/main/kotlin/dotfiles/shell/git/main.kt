@file:JvmName("Main")

package dotfiles.shell.git

import io.mkobit.git.config.Include
import io.mkobit.git.config.asText
import io.mkobit.git.host.execute
import picocli.CommandLine
import java.nio.file.Path
import java.util.concurrent.Callable
import kotlin.io.path.ExperimentalPathApi
import kotlin.io.path.createDirectories
import kotlin.io.path.div
import kotlin.io.path.Path
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
  var configFiles: List<Path> = emptyList()

  private companion object {
    const val GIT_CONFIG_FILENAME = ".gitconfig"
  }

  override fun call(): Int {
    val general = Path("general") / GIT_CONFIG_FILENAME
    val personal = Path("personal") / GIT_CONFIG_FILENAME
    val configurations = mapOf(
      general to generalGitConfig(globalExcludesFile),
      personal to personalGitConfig(),
    ).let {
      configFiles.fold(it) { accumulator, scriptPath ->
        execute(scriptPath, accumulator)
      }
    }.also {
      // just assuming all configurations still present, maybe modified
      require(general in it)
      require(personal in it)
    }

    configurations
      .mapKeys { (path, _) -> outputDir / path }
      .onEach { (path, _) -> require(path.isChildOf(outputDir)) { "$path must be a child of $outputDir"} }
      .forEach { (path, sections) ->
        path.parent.createDirectories()
        path.writeText(sections.asText())
      }

    val work = configFiles.firstOrNull { it.contains(Path("work")) }

    val includes = outputDir / "includes" / GIT_CONFIG_FILENAME
    includes.parent.createDirectories()
    includes.writeText(
      (
        listOf(
          Include(path = outputDir / general),
          Include(outputDir / personal).ifGitDir(dotfilesDir),
          Include(outputDir / personal).ifGitDir(personalDir),
          Include(outputDir / personal).ifGitDir(codeLabDir),
        ) + listOfNotNull(work).map { Include(outputDir / it).ifGitDir(workDir) }
      ).asText()
    )
    return 0
  }
}

private fun Path.isChildOf(path: Path): Boolean = normalize().startsWith(path.normalize())

@ExperimentalPathApi
fun main(args: Array<String>): Unit = exitProcess(CommandLine(GenerateGitConfig()).execute(*args))
