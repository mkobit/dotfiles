package com.mkobit.personalassistant.chrome

import retrofit2.Call
import retrofit2.http.GET

/**
 * @see <a href="https://chromedevtools.github.io/devtools-protocol/">DevTools Protocol</a>
 *
 */
interface Chrome {

  @GET("/json/list")
  fun discover(): Call<Page>
}
