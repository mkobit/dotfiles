@file:JvmName("Main")

package io.mkobit.homedir.assembler

import com.github.ajalt.clikt.core.CliktCommand
import com.github.ajalt.clikt.parameters.options.option
import com.github.ajalt.clikt.parameters.options.required
import com.github.ajalt.clikt.parameters.types.path
import kotlin.jvm.JvmName

class GenerateGitFiles : CliktCommand() {
  val destinationDir by option("--destination-dir", help = "Generation")
    .path(mustBeWritable = true)
    .required()

  override fun run() {
    TODO("Not yet implemented")
  }
}

fun main(args: Array<String>) = GenerateGitFiles().main(args)

@ExperimentalStdlibApi
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
    val general = Path("general")
    val personal = Path("personal")
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
      .mapKeys { (path, _) -> outputDir / path / GIT_CONFIG_FILENAME }
      .onEach { (path, _) -> require(path.isChildOf(outputDir)) { "$path must be a child of $outputDir"} }
      .forEach { (path, sections) ->
        path.parent.createDirectories()
        path.writeText(sections.asText())
      }

    val work = configurations.keys.firstOrNull { it.contains(Path("work")) }

    val includes = outputDir / "includes" / GIT_CONFIG_FILENAME
    includes.parent.createDirectories()
    fun includePathFor(path: Path) = Path("") / path /  GIT_CONFIG_FILENAME
    includes.writeText(
      (
        listOf(
          Include(path = includePathFor(general)),
          Include(includePathFor(personal)).ifGitDir(dotfilesDir),
          Include(includePathFor(personal)).ifGitDir(Path("Workspace/personal/**")),
          Include(includePathFor(personal)).ifGitDir(Path("Workspace/code_lab/**")),
        ) + listOfNotNull(work?.let { Include(includePathFor(it)).ifGitDir(Path("Workspace/work/**")) })
      ).asText()
    )
    return 0
  }
}
