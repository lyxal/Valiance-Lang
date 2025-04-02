import mill._, scalalib._

object valiance extends ScalaModule {
  def scalaVersion = "3.6.4"
  def mainClass = Some("jvm.Main")
  override def sources =
    T.sources(
      build.millSourcePath / "jvm"
    )
}
