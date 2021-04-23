package dotfilesbuild.io.http

import mu.KotlinLogging
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okio.buffer
import okio.sink
import org.gradle.api.DefaultTask
import org.gradle.api.GradleException
import org.gradle.api.file.RegularFileProperty
import org.gradle.api.model.ObjectFactory
import org.gradle.api.provider.Property
import org.gradle.api.tasks.CacheableTask
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.Optional
import org.gradle.api.tasks.OutputFile
import org.gradle.api.tasks.TaskAction
import org.gradle.kotlin.dsl.property
import java.nio.file.Files
import java.nio.file.attribute.PosixFilePermission
import javax.inject.Inject

@CacheableTask
open class Download @Inject constructor(
  objectFactory: ObjectFactory
) : DefaultTask() {

  companion object {
    private val log = KotlinLogging.logger {}
  }

  @get:Input
  val url: Property<String> = objectFactory.property()

  @get:OutputFile
  val destination: RegularFileProperty = objectFactory.fileProperty()

  @get:Input
  @get:Optional
  val executable: Property<Boolean> = objectFactory.property()

  @TaskAction
  fun retrieveFile() {
    val destinationFile = destination.asFile.get()
    if (destinationFile.exists()) {
      // TODO: up-to-date checking instead?
      log.info { "File at $destinationFile already exists, skipping download" }
      return
    }
    val client = OkHttpClient.Builder()
      .build()
    val request = Request.Builder()
      .get()
      .url(url.get())
      .build()

    log.info { "Issuing ${request.method} to ${request.url}" }
    client.newCall(request).execute().use {
      log.info { "Response code ${it.code} from ${it.request.url}" }
      if (it.isNotSuccessful) {
        throw GradleException("Could not download file from ${it.request.url} - exited with code ${it.code} and message ${it.message}")
      }
      it.header("Content-Length")?.let {
        log.info { "Content-Length header value: $it" }
      }
      log.info { "Saving response from ${it.request.url} to $destinationFile" }
      destinationFile.sink().buffer().use { sink ->
        sink.writeAll(it.body!!.source())
      }
    }
    if (executable.getOrElse(false)) {
      log.info { "Marking $destinationFile as executable" }
      val destinationPath = destinationFile.toPath()
      val currentPermission = Files.getPosixFilePermissions(destinationPath)
      Files.setPosixFilePermissions(
        destinationPath,
        currentPermission + setOf(
          PosixFilePermission.OWNER_EXECUTE,
          PosixFilePermission.GROUP_EXECUTE
        )
      )
    }
  }

  private val Response.isNotSuccessful get() = !isSuccessful
}
