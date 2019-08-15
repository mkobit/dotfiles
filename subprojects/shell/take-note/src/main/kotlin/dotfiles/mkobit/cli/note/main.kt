@file:JvmName("Main")
package dotfiles.mkobit.cli.note

import picocli.CommandLine
import java.nio.file.Files
import java.nio.file.Path
import java.time.Instant
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeFormatterBuilder
import kotlin.system.exitProcess

@CommandLine.Command(
  name = "note",
  mixinStandardHelpOptions = true
)
internal class TakeNote : Runnable {

  @CommandLine.Option(
    names = ["--dir"],
    paramLabel = "DIRECTORY",
    description = ["Target directory to create note in (defaults to current directory)"],
    showDefaultValue = CommandLine.Help.Visibility.ALWAYS
  )
  private var directory: Path = Path.of(System.getProperty("user.dir"))

  @CommandLine.Option(
    names = ["--dry-run"],
    paramLabel = "DRY RUN",
    description = ["Prints out the expected file name without creating it"]
  )
  private var dryRun: Boolean = false

  @CommandLine.Option(
    names = ["--mkdirs"],
    description = ["Makes the directory path if it does not exist yet,"]
  )
  private var makeDirs: Boolean = false

  @CommandLine.Parameters(
    paramLabel = "NAME",
    description = ["Name of the note"]
  )
  private lateinit var noteName: String

  companion object {
    private val NOTE_NAME_REGEX = Regex("^[\\w-]+(?!-\$)\$")
    private val FORMATTER = DateTimeFormatterBuilder()
      .appendInstant(0)
      .toFormatter()
  }

  override fun run() {
    require(noteName.matches(NOTE_NAME_REGEX)) { "Note name $noteName must match regex $NOTE_NAME_REGEX" }
    if (makeDirs) {
      Files.createDirectories(directory)
    } else {
      require(Files.isDirectory(directory)) { "${directory.toAbsolutePath()} must be an existing directory" }
    }

    val filename ="${FORMATTER.format(Instant.now())}-$noteName.adoc"
    Files.createFile(directory.resolve(filename))
  }
}

fun main(args: Array<String>) {
  val cli = CommandLine(TakeNote())
  exitProcess(cli.execute(*args))
}
