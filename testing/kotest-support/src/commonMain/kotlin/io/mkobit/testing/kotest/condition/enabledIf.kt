package io.mkobit.testing.kotest.condition

import io.kotest.core.test.Enabled
import io.kotest.core.test.EnabledOrReasonIf

val NotImplemented: EnabledOrReasonIf = {
  Enabled.disabled("not implemented yet")
}
