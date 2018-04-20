package com.mkobit.personalassistant.inject

import io.ktor.application.Application
import io.ktor.application.ApplicationCall
import io.ktor.application.ApplicationCallPipeline
import io.ktor.application.ApplicationFeature
import io.ktor.util.AttributeKey

class DependencyInjection {
  companion object Feature : ApplicationFeature<Application, DependencyInjection, DependencyInjection> {
    override val key: AttributeKey<DependencyInjection> = AttributeKey("KodeinInjector")

    override fun install(pipeline: Application, configure: DependencyInjection.() -> Unit): DependencyInjection {
      val injection = DependencyInjection().apply(configure)

      pipeline.intercept(ApplicationCallPipeline.Infrastructure) {
      }

      return injection
    }
  }
}


