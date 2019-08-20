package dotfilesbuild.io.git

import mu.KotlinLogging
import org.gradle.api.DefaultTask
import org.gradle.api.file.DirectoryProperty
import org.gradle.api.model.ObjectFactory
import org.gradle.api.provider.Property
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.Internal
import org.gradle.api.tasks.TaskAction
import org.gradle.kotlin.dsl.property
import org.gradle.kotlin.dsl.submit
import org.gradle.workers.IsolationMode
import org.gradle.workers.WorkerExecutor
import javax.inject.Inject

@Deprecated("Simplification in-progress")
open class ConfigureRemotes @Inject constructor(
  private val workerExecutor: WorkerExecutor,
  objectFactory: ObjectFactory
) : DefaultTask() {

  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  @get:Internal
  val repositoryDirectory: DirectoryProperty = newOutputDirectory()

  @get:Input
  val remotes: Property<Map<String, String>> = objectFactory.property()

  @TaskAction
  fun configureRemotes() {
    workerExecutor.submit(ConfigureRemotesAction::class) {
      isolationMode = IsolationMode.NONE
      setParams(repositoryDirectory.get().asFile, remotes.get().toMap())
    }
  }
}
