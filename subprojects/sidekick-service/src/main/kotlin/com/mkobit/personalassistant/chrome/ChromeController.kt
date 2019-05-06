package com.mkobit.personalassistant.chrome

import kotlinx.coroutines.Job

interface ChromeController {

  suspend fun start(): Job
}
