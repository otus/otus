var OpenTSDBURL="http://localhost:4242";
var SuggestURL=OpenTSDBURL+"/suggest?";
var QueryURL=QueryURL+"/q?";
var NumMapper=6;
var NumReducer=4;
var MetricList = ["cpu_user", "cpu_system", "vmrss", "vmsize", "readbytesrate", "writebytesrate"];
var ProcessList = ["DataNode", "TaskTracker"];
var MetricYLabel = {cpu_user:"User CPU", cpu_system:"System CPU", vmrss:"Resident Memory (Bytes)",
					vmsize:"Virtual Memory (Bytes)", readbytesrate:"Disk I/O Read Throughput (Bytes)",
					writebytesrate:"Disk I/O Write Throughput (Bytes)"};
var ServerList = ['localhost']
