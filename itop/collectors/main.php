<?php

// Scan2Agent - collector
//
// testing:
// php exec.php --console_log_level=9 --collect_only

printf ("php: Scan2Agent.: main.php ...\n");
printf ("php: Scan2Agent.: START\n");

Orchestrator::AddRequirement('5.4.0');

require_once(APPROOT.'collectors/ep4srcLogicalInterface.class.inc.php');
require_once(APPROOT.'collectors/ep4srcOSLicence.class.inc.php');
require_once(APPROOT.'collectors/ep4srcVirtualMachine.class.inc.php');
require_once(APPROOT.'collectors/ep4srcSoftware.class.inc.php');
require_once(APPROOT.'collectors/ep4srcOtherSoftware.class.inc.php');

$iRank = 1;
//Orchestrator::AddCollector($iRank++, 'ep4srcLogicalInterface');
//Orchestrator::AddCollector($iRank++, 'ep4srcOSLicence');
Orchestrator::AddCollector($iRank++, 'ep4srcVirtualMachine');
Orchestrator::AddCollector($iRank++, 'ep4srcSoftware');
Orchestrator::AddCollector($iRank++, 'ep4srcOtherSoftware');

printf ("php: Scan2Agent.: END\n");
