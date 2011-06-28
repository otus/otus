var SuggestURL=OpenTSDBURL+"/suggest?";
var QueryURL=OpenTSDBURL+"/q?";
var MetricList = ["cpu_user", "cpu_system", "vmrss", "vmsize", "readbytesrate", "writebytesrate"];
var ProcessList = ["DataNode", "TaskTracker"];
var MetricYLabel = {cpu_user:"User CPU", cpu_system:"System CPU", vmrss:"Resident Memory (Bytes)",
                                        vmsize:"Virtual Memory (Bytes)", readbytesrate:"Disk I/O Read Throughput (Bytes)",
                                        writebytesrate:"Disk I/O Write Throughput (Bytes)"};

function getArrayToORString(strarray) {
	if (strarray.length == 0) {
		return null;
	}
	var ret = strarray[0];
	for (var i = 1; i < strarray.length; ++i) {
		ret += "|" + strarray[i];
	}
	return ret;
};

function getObjStrValue(id, initVal) {
	var val = $(id).val();
	if (val == null || val == "") {
		return initVal;
	} else {
		return val;
	}
};

var registerDashboardToReload = null;

