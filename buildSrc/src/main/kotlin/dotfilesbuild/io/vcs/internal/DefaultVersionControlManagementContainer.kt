package dotfilesbuild.io.vcs.internal

import dotfilesbuild.io.vcs.VersionControlTarget
import org.gradle.api.internal.DefaultPolymorphicDomainObjectContainer
import org.gradle.internal.reflect.Instantiator
import javax.inject.Inject

open class DefaultVersionControlManagementContainer @Inject constructor(instantiator: Instantiator) : DefaultPolymorphicDomainObjectContainer<VersionControlTarget>(VersionControlTarget::class.java, instantiator)
