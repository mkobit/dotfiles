package com.mkobit.chickendinner.chrome

/**
 * @param method the domain and method name in the form of `domain.method_name`
 */
data class RequestFrame(
    val id: Long,
    val method: String,
    val params: Any?
)
