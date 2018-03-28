package dotfilesbuild.io.http

import mu.KotlinLogging
import okhttp3.HttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okio.Okio
import org.gradle.api.DefaultTask
import org.gradle.api.GradleException
import org.gradle.api.file.ProjectLayout
import org.gradle.api.file.RegularFileProperty
import org.gradle.api.model.ObjectFactory
import org.gradle.api.provider.Property
import org.gradle.api.provider.ProviderFactory
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.OutputFile
import org.gradle.api.tasks.TaskAction
import org.gradle.kotlin.dsl.property
import javax.inject.Inject

open class Download @Inject constructor(
    objectFactory: ObjectFactory,
    providerFactory: ProviderFactory,
    projectLayout: ProjectLayout
) : DefaultTask() {

  companion object {
    private val log = KotlinLogging.logger {}
  }

  @get:Input
  val url: Property<String> = objectFactory.property()

  @get:OutputFile
  val destination: RegularFileProperty = projectLayout.fileProperty()

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

    log.info { "Issuing ${request.method()} to ${request.url()}" }
    client.newCall(request).execute().use {
      log.info { "Response code ${it.code()} from ${it.request().url()}" }
      if (it.isNotSuccessful) {
        throw GradleException("Could not download file from ${it.request().url()} - exited with code ${it.code()} and message ${it.message()}")
      }
      it.header("Content-Length")?.let {
        log.info { "Content-Length header value: $it" }
      }
      log.info { "Saving response from ${it.request().url()} to $destinationFile" }
      Okio.buffer(Okio.sink(destinationFile)).use { sink ->
        sink.writeAll(it.body()!!.source())
      }
    }
  }

  private val Response.isNotSuccessful get() = !isSuccessful
}
