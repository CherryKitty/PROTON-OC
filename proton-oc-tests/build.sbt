lazy val root = (project in file(".")).
  settings(
    inThisBuild(List(
      organization := "it.cnr.istc.labss",
      scalaVersion := "2.12.4"
    )),
    name := "proton-oc-tests"
  )

libraryDependencies ++= Seq(
  "org.scalatest" %% "scalatest" % "3.0.5" % Test
)

lazy val downloadFromZip = taskKey[Unit]("Download zipped extensions and extract them to ./extensions")

downloadFromZip := {
  val baseURL = "https://raw.githubusercontent.com/NetLogo/NetLogo-Libraries/6.0/extensions/"
  val extensions = List(
    "nw" -> "nw-3.7.5.zip", "table" -> "table-1.3.0.zip",
    "csv" -> "csv-1.1.0.zip", "profiler" -> "profiler-1.1.0.zip",
    "rnd" -> "rnd-3.0.0.zip"
  )
  for {
    (extension, file) <- extensions
    path = new File("extensions/" + extension)
    if java.nio.file.Files.notExists(path.toPath)
    url = new URL(baseURL + file)
  } {
    println("Downloading " + url)
    IO.unzipURL(url, path)
  }
}

compile in Test := (compile in Test).dependsOn(downloadFromZip).value

fork in Test := true

javaOptions in test += "-Xms512M -Xmx3000M -Xss1M -XX:+UseConcMarkSweepGC -XX:NewRatio=8"
