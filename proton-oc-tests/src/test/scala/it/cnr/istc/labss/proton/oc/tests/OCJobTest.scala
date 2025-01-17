package it.cnr.istc.labss.proton.oc.tests

import org.nlogo.headless.HeadlessWorkspace
import org.nlogo.core.LogoList
import org.nlogo.api.ScalaConversions.RichSeq

class OCJobTest extends OCModelSuite {

  test("Work system stays coherent ") { ws =>
    ws.cmd("""
      set num-persons 1000
      setup
      """
    )
    for (fid <- 1 to 36) {
      println(fid)
      ws.cmd("go")
      // no minors working
      ws.rpt("any? persons with [ my-job != nobody and age <= 16 ] ") shouldBe false
      // unemployed stay so
      ws.rpt("any? persons with [ (job-level = 1 or job-level = 0) and my-job != nobody ] ") shouldBe false
      // job levels are coherent     
      ws.rpt("any? persons with [ (job-level = 1 or job-level = 0) and my-job != nobody ] ") shouldBe false   
      // nobody has two jobs
      ws.rpt("""
        all? all-persons with [ my-job != nobody ] [ count jobs with [ my-worker = myself ]  = 1 ]      
      """) shouldBe true 
    }
  }
}
