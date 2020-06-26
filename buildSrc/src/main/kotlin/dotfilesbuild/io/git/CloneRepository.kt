package dotfilesbuild.io.git

import mu.KotlinLogging
import org.gradle.api.DefaultTask
import org.gradle.api.file.DirectoryProperty
import org.gradle.api.model.ObjectFactory
import org.gradle.api.provider.Property
import org.gradle.api.tasks.Internal
import org.gradle.api.tasks.TaskAction
import org.gradle.kotlin.dsl.property
import org.gradle.kotlin.dsl.submit
import org.gradle.workers.IsolationMode
import org.gradle.workers.WorkerExecutor
import java.io.File
import java.nio.file.Files
import java.nio.file.Path
import javax.inject.Inject

@Deprecated("Simplification in-progress")
open class CloneRepository @Inject constructor(
  private val workerExecutor: WorkerExecutor,
  objectFactory: ObjectFactory
) : DefaultTask() {

  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  init {
    outputs.upToDateWhen { doesGitRepositoryExist() }
  }

  @get:Internal
  val repositoryDirectory: DirectoryProperty = objectFactory.directoryProperty()

  @get:Internal
  val repositoryUrl: Property<String> = objectFactory.property()

  private val repositoryDirectoryFile: File
    get() = repositoryDirectory.asFile.get()

  private val repositoryDirectoryPath: Path
    get() = repositoryDirectoryFile.toPath()

  @TaskAction
  fun cloneRepository() {
    val asFile = repositoryDirectory.asFile.get()
    if (doesGitRepositoryExist()) {
      LOGGER.info { "Directory already exists at $asFile" }
      return
    }
    workerExecutor.submit(CloneAction::class) {
      isolationMode = IsolationMode.NONE
      setParams(asFile, repositoryUrl.get())
    }
  }

  private fun doesGitRepositoryExist(): Boolean {
    // TODO: better way to determine if git repository already exists
    return Files.isDirectory(repositoryDirectoryPath)
  }
}
