package git

import mu.KotlinLogging
import org.gradle.api.DefaultTask
import org.gradle.api.file.Directory
import org.gradle.api.file.DirectoryVar
import org.gradle.api.file.ProjectLayout
import org.gradle.api.provider.PropertyState
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.InputDirectory
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
    outputs.upToDateWhen { doesDirExists() }
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
    if (doesDirExists()) {
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

  private fun doesDirExists(): Boolean {
    val repositoryPath = destinationDirectory!!.toPath()
    return Files.isDirectory(repositoryPath)
  }
}
