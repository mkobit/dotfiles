package dotfilesbuild.process

import org.gradle.api.file.FileTree
import org.gradle.api.provider.Property
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.InputFiles
import org.gradle.process.CommandLineArgumentProvider

class FileTreeExpandingCommandLineArgumentProvider(
  @get:Input val option: Property<String>,
  @get:InputFiles val fileTree: FileTree
) : CommandLineArgumentProvider {

  override fun asArguments(): Iterable<String> =
    option.get().let { optionValue ->
      fileTree.files.flatMap { file -> listOf(optionValue, file.absolutePath) }
    }
}
