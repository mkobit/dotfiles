package git

import mu.KotlinLogging
import org.gradle.api.DefaultTask
import org.gradle.api.file.Directory
import org.gradle.api.provider.PropertyState
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.OutputDirectory
import org.gradle.api.tasks.TaskAction
import org.gradle.workers.IsolationMode
import org.gradle.workers.WorkerExecutor
import java.io.File
import java.nio.file.Files
import javax.inject.Inject

open class CloneRepository @Inject constructor(
    private val workerExecutor: WorkerExecutor
) : DefaultTask() {

  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  init {
    outputs.upToDateWhen { doesGitRepositoryExist() }
  }

  var repositoryDirectoryProvider: Directory? = null
  val repositoryUrlState: PropertyState<String> = project.property(String::class.java)

  @get:OutputDirectory
  val destinationDirectory: File?
    get() = repositoryDirectoryProvider?.get()

  @get:Input
  var repositoryUrl: String?
    get() = repositoryUrlState.orNull
    set(value) = repositoryUrlState.set(value)

  @TaskAction
  fun cloneRepository() {
    if (doesGitRepositoryExist()) {
      LOGGER.info { "Directory already exists at $destinationDirectory" }
      didWork = false
      return
    }
    workerExecutor.submit(CloneAction::class.java) {
      it.apply {
        isolationMode = IsolationMode.NONE
        setParams(destinationDirectory!!, repositoryUrl!!)
      }
    }
  }

  private fun doesGitRepositoryExist(): Boolean {
    // TODO: better way to determine if git repository already exists
    val repositoryPath = destinationDirectory!!.toPath().resolve(".git")
    return Files.isDirectory(repositoryPath)
  }
}
