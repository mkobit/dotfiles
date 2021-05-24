import java.util.zip.ZipFile
import java.util.zip.ZipException
import java.nio.file.Files
import java.util.zip.ZipEntry

plugins {
  id("dotfilesbuild.dotfiles-lifecycle")
}

repositories {
  exclusiveContent {
    forRepository {
      ivy {
        name = "github"
        url = uri("https://github.com")
        patternLayout {
          artifact("/[organisation]/[module]/archive/[revision].[ext]")
        }
        metadataSources { artifact() }
      }
    }
    filter {
      includeGroup("junegunn")
    }
  }
}

abstract class Unzip : TransformAction<TransformParameters.None> {
  @get:InputArtifact
  abstract val inputArtifact: Provider<FileSystemLocation>

  override fun transform(outputs: TransformOutputs) {
    val input = inputArtifact.get().asFile
    val unzipDir = outputs.dir(input.name)
    unzipTo(input, unzipDir)
  }

  private fun unzipTo(zipFile: File, unzipDir: File) {
    ZipFile(zipFile).use { zip ->
      val outputDirectoryCanonicalPath = unzipDir.canonicalPath
      for (entry in zip.entries()) {
        unzipEntryTo(unzipDir, outputDirectoryCanonicalPath, zip, entry)
      }
    }
  }

  private fun unzipEntryTo(outputDirectory: File, outputDirectoryCanonicalPath: String, zip: ZipFile, entry: ZipEntry) {
    val output = outputDirectory.resolve(entry.name)
    if (!output.canonicalPath.startsWith(outputDirectoryCanonicalPath)) {
      throw ZipException("Zip entry '${entry.name}' is outside of the output directory")
    }
    if (entry.isDirectory) {
      output.mkdirs()
    } else {
      output.parentFile.mkdirs()
      zip.getInputStream(entry).use { Files.copy(it, output.toPath()) }
    }
  }
}

val artifactType = Attribute.of("artifactType", String::class.java)
val unpacked = Attribute.of("unpacked", Boolean::class.javaObjectType)

val vimPlug by configurations.creating {
  attributes.attribute(unpacked, true)
}

dependencies {
  attributesSchema {
    attribute(unpacked)
  }
  registerTransform(Unzip::class) {
    from.attribute(unpacked, false).attribute(artifactType, "zip")
    to.attribute(unpacked, true).attribute(artifactType, "unpacked")
  }
  artifactTypes.register("zip") {
    attributes.attribute(unpacked, false)
  }
  vimPlug("junegunn:vim-plug:master@zip") {
    isChanging = true
  }
}

tasks {
  val unpackVimPlug by registering(Sync::class) {
    from(vimPlug)
    into(layout.buildDirectory.dir("vim-plug-source"))
  }

  val extractVimPlugFileIntoAutoload by registering(Sync::class) {
    from(unpackVimPlug)
    into(layout.buildDirectory.dir("vim-plug"))
    include("**/plug.vim")
    eachFile {
      relativePath = RelativePath(true, *relativePath.segments.drop(1).toTypedArray())
    }
    includeEmptyDirs = false
  }

  val stageVimFiles by registering(Sync::class) {
    from(layout.projectDirectory.dir("config"))
    into(layout.buildDirectory.dir("generated-vim-config-staging"))
    dependsOn(extractVimPlugFileIntoAutoload)
  }

  val syncStaged by registering(Sync::class) {
    from(stageVimFiles)
    into(layout.buildDirectory.dir("generated-vim-config"))
    dependsOn(extractVimPlugFileIntoAutoload)
  }

  dotfiles {
    // add directive to ~/.vimrc to vim file
    // :source <path>
    dependsOn(syncStaged)
  }
}
