package dotfilesbuild.io.git

import mu.KotlinLogging
import org.eclipse.jgit.lib.RepositoryCache
import org.eclipse.jgit.util.FS
import org.gradle.api.DefaultTask
import org.gradle.api.file.DirectoryProperty
import org.gradle.api.model.ObjectFactory
import org.gradle.api.provider.Property
import org.gradle.api.tasks.Internal
import org.gradle.api.tasks.TaskAction
import org.gradle.kotlin.dsl.property
import org.gradle.workers.WorkerExecutor
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

  @TaskAction
  fun cloneRepository() {
    val asFile = repositoryDirectory.asFile.get()
    if (doesGitRepositoryExist()) {
      LOGGER.info { "Directory already exists at $asFile" }
      return
    }
//    workerExecutor.noIsolation().submit(CloneAction::class) {
//      isolationMode = IsolationMode.NONE
//      setParams(asFile, repositoryUrl.get())
//    }
  }

  private fun doesGitRepositoryExist(): Boolean {
    // Both below are in regards to "How to Check if A Git Clone Has Been Done Already with JGit"
    // https://stackoverflow.com/questions/13586502/how-to-check-if-a-git-clone-has-been-done-already-with-jgit
    // https://www.eclipse.org/lists/jgit-dev/msg01892.html

    return RepositoryCache.FileKey.isGitRepository(repositoryDirectory.asFile.get(), FS.DETECTED)
  }
}
