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
      log.info { "Saving response from ${it.request().url()} to ${destination.asFile.get()}" }
      Okio.buffer(Okio.sink(destination.asFile.get())).use { sink ->
        sink.writeAll(it.body()!!.source())
      }
    }
  }

  private val Response.isNotSuccessful get() = !isSuccessful
}
