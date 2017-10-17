package com.mkobit.personalassistant.chrome

import kotlinx.coroutines.experimental.Job

interface ChromeController {

  suspend fun start(): Job
}
