package com.mkobit.chickendinner.chrome

import kotlinx.coroutines.experimental.channels.ReceiveChannel
import kotlinx.coroutines.experimental.channels.SendChannel

class ChromeDebuggerSession(
    val incoming: ReceiveChannel<Any>,
    val outgoing: SendChannel<Any>
) {
}
