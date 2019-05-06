package com.mkobit.personalassistant.process

//class ProcessModule(
//    private val launcherPoolSize: Int = 10
//) : AbstractModule () {
//  override fun configure() {
//    bind(ChromeController::class.java).to(BackgroundProcessChromeController::class.java)
//  }
//
//  @Provides
//  @Singleton
//  @ProcessLauncherContext
//  fun coroutinePool(): CoroutineContext = newFixedThreadPoolContext(launcherPoolSize, "ProcessLauncher pool")
//}

@Target(AnnotationTarget.VALUE_PARAMETER, AnnotationTarget.FUNCTION)
annotation class ProcessLauncherContext
