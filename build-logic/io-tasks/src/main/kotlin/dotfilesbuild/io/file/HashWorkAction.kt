package dotfilesbuild.io.file

import org.gradle.api.file.RegularFileProperty
import org.gradle.api.provider.Property
import org.gradle.workers.WorkAction
import org.gradle.workers.WorkParameters
import java.nio.file.Files
import java.security.MessageDigest

abstract class HashWorkAction : WorkAction<HashWorkParameters> {
  override fun execute() {
    val messageDigest = parameters.algorithm.map { MessageDigest.getInstance(it) }.get()
    val sourceBytes = parameters.source
      .map { it.asFile }
      .map { it.toPath() }
      .map { Files.readAllBytes(it) }
      .get()
    val outputBytes = messageDigest.digest(sourceBytes)
    val outputPath = parameters.destination
      .map { it.asFile }
      .map { it.toPath() }
      .get()
    Files.createDirectories(outputPath.parent)
    Files.writeString(outputPath, outputBytes.toHexString())
  }

  @ExperimentalUnsignedTypes
  private fun ByteArray.toHexString() =
    asUByteArray()
      .joinToString("") {
        it.toString(16).padStart(2, '0')
      }
}

interface HashWorkParameters : WorkParameters {
  val source: RegularFileProperty
  val destination: RegularFileProperty
  val algorithm: Property<String>
}
