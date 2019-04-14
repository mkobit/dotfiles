package com.mkobit.chickendinner.amazon

import com.google.common.io.Resources
import org.junit.jupiter.api.Test
import strikt.api.expectThat
import strikt.assertions.containsExactlyInAnyOrder
import strikt.assertions.hasSize
import strikt.assertions.map

internal class GiveawayEmailParserTest {
  @Test
  internal fun `can parse an email`() {
    val emailText = Resources.getResource("com/mkobit/chickendinner/amazon/giveaway-emails/sanitized-email.html").readText(Charsets.UTF_8)

    val giveawaySources = GiveawayEmailParser().parse(emailText)
    expectThat(giveawaySources) {
      hasSize(16)
      map { it.url }.containsExactlyInAnyOrder(
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=HLRJVR6N48G2&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2F84b8c654b5e7a319%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=Z5OFTUPWFESGSTNODLIHREUPLOEA&ref_=pe_2644850_404992530_gde",
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=2NB9CI6P61ACG&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2F7e29342e2b4d49b3%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=AXCKZ94OHLRMBYKHOY2XQZ1COAYA&ref_=pe_2644850_404992530_gde",
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=FWTG2RA6CUFI&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2Fb31499248fe8f704%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=KFBXEVQYFZBU3CJWILZS7A5Y4KQA&ref_=pe_2644850_404992530_gde",
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=395BKUYJ5MCQL&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2F61ca9b827f265a37%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=TC4LBIFYI0LBQPJF9AIB7542VSOA&ref_=pe_2644850_404992530_gde",
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=1Q03Z7LP1W5D3&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2F0eff7d5439d90779%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=0TCOXYFTXFJ9XLXGALWSPHOOKBCA&ref_=pe_2644850_404992530_gde",
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=1O49AL7824TT9&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2F113ae82f4d9e44e8%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=4PGLVUMBZP4TAQYREMC6GGLPFG4A&ref_=pe_2644850_404992530_gde",
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=2C7IHYF3GU34J&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2Fff5e46711eab8ab5%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=KHHAR3C9KTHYNUC9HH4OLOWMRU8A&ref_=pe_2644850_404992530_gde",
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=2ME2PX65REC1M&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2Fb5ed7740fdfc94de%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=DEJICENERXYCGERWQFNRPWJRUCSA&ref_=pe_2644850_404992530_gde",
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=FUZJ1Z83VVQP&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2Fb270871b187f5997%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=G1TIQI4GJW7SBQFCXALHXLLXWGKA&ref_=pe_2644850_404992530_gde",
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=9KSVAD6JNW8D&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2F926aaab397878861%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=6AILPRI0LI6LTRBNI6XQJEPQG0EA&ref_=pe_2644850_404992530_gde",
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=18RY3TTIPOCZY&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2F41c12d520515cc2a%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=ZAEABYMZ7CEAA2CABN2SPQZSWYSA&ref_=pe_2644850_404992530_gde",
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=1FJXNJLHKVHVC&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2Ffa3b0aab38594083%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=KGJVJYPTLHTK0NRFT2LFGNDYE38A&ref_=pe_2644850_404992530_gde",
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=ZUONJZZUIRXX&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2F51c53d5e36265222%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=N46D60MW66MWHNQIEKVFFJM05JIA&ref_=pe_2644850_404992530_gde",
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=3RRZ8Q003ROFK&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2F9470fcca814352e6%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=7MN8O38PA9USTADNACVS4VWSSJYA&ref_=pe_2644850_404992530_gde",
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=1HCVNEVDRGMF3&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2F228a7768f6e8f552%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=53TDLWMTYVIYDYR91STEOBQKATYA&ref_=pe_2644850_404992530_gde",
        "https://www.amazon.com/gp/r.html?C=J8AJ5RKKDF1U&K=FQED9SIVD2LY&M=urn:rtn:msg:201904131618228f24c9dc19034e36bb951ff58320p0na&R=3PGXFJMDBI7IZ&T=C&U=https%3A%2F%2Fwww.amazon.com%2Fga%2Fp%2Ff4d500efac0c6fbe%3Fnav%3Damz%26fsrc%3Dml%26i%3Demd%26ref_%3Dpe_2644850_404992530_gde-ga&H=MKHMCBSGBCXAOGXE4IC5II5AGQOA&ref_=pe_2644850_404992530_gde"
      )
    }
  }
}
