package com.mkobit.chickendinner.chrome.domain

@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.RUNTIME)
annotation class DebugProtocolMethod(val method: String)
