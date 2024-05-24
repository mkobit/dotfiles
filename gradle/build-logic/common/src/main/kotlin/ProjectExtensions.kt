import org.gradle.api.Project
import org.gradle.api.artifacts.VersionCatalog
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.the

//private val PluginDependenciesSpec.libsVersionCatalog: VersionCatalog
//  get() = the<VersionCatalogsExtension>().named("libs")

fun Project.dependencyFromLibs(name: String) =
  libsVersionCatalog.findLibrary(name).get()

fun Project.bundleFromLibs(name: String) =
  libsVersionCatalog.findBundle(name).get()

private val Project.libsVersionCatalog: VersionCatalog
  get() = the<VersionCatalogsExtension>().named("libs")
