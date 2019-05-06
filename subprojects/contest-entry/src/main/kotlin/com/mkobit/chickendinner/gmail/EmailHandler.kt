package com.mkobit.chickendinner.gmail

// pipeline:
// 1) list emails (remote, rate-limited)
// 2) classify emails (local)
// 3) send classified email to registered handler
// 4) registered handler runs business logic for specific email type
//   4.a) parse email, send to downstream commands,
// 5) archive email, store results whatever
interface EmailHandler {
}
