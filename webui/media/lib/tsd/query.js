/** 
*  Query to OpenTSDB to generate visual reports for Otus
*
*  Kai Ren (kair@cs.cmu.edu) 
*
**/

function genMetricQuery(metric, tags, conf) {
	var query = "m=" + conf.aggfunc;
	if (conf.downSample != null) {
		query += ":"+conf.downSample;
	}
	if (conf.isRate) {
		query += ":rate";
	}
	query += ":"+metric;
	first = true;
	for (tagName in tags) {
		if (first) {
			query += "{";
			first = false;
		} else {
			query += ",";
		}
		query += tagName + "=" + tags[tagName];
	}
	if (!first) {
		query += "}";
	}
	return query;
}

function procClusterView(metric, procname, conf) {
	return genMetricQuery("process."+metric, {proc: procname}, conf);
}

function totClusterView(metric, conf) {
	return genMetricQuery("node."+metric, {}, conf);
}

function totJobClusterView(metric, conf) {
	return genMetricQuery("mrjob."+metric, {}, conf);
}

function jobClusterView(metric, _jobid, conf) {
	return genMetricQuery("mrjob."+metric, {jobid: _jobid}, conf);
}

function procNodeView(metric, hostid, procname, conf) {
	return genMetricQuery("process."+metric, {proc: procname, host:hostid}, conf);
}

function totNodeView(metric, hostid, conf) {
	return genMetricQuery("node."+metric, {host:hostid}, conf);
}

function jobNodeView(metric, hostid, _jobid, conf) {
	return genMetricQuery("mrjob."+metric, {jobid: _jobid, host:hostid}, conf);
}

function slotsNodeView(metric, hostid, _jobid, conf) {
	var slots = new Array();
	for (var i = 0; i < NumMapper; ++i)
		slots.push("m"+i);
	for (var i = 0; i < NumReducer; ++i)
		slots.push("r"+i);
	var typevalue = getArrayToORString(slots);
	return genMetricQuery("mrjob."+metric, {jobid: _jobid, host:hostid, tasktype: typevalue}, conf);
}

function totJobNodeView(metric, hostid, conf) {
	return genMetricQuery("mrjob."+metric, {host: hostid}, conf);
}

function getOpenTSDBURL() {
	return QueryURL;
}

function genQuery(startTime, endTime, metricQueries, callback) {
	query = getOpenTSDBURL()+"start="+startTime+"&end="+endTime+"&ascii&injson";
	for (var i = 0; i < metricQueries.length; ++i) {
		query += "&"+metricQueries[i];
	}
	//return encodeURI(query+"&callback=?");
	return query+"&callback=?";
}

function getClusterView(startTime, endTime, conf) {
	var queries = new Array();
	queries.push(totClusterView(conf.metric, conf));
	queries.push(totJobClusterView(conf.metric, conf));
	var procname = getArrayToORString(conf.proclist);
	if (procname != null) {
		queries.push(procClusterView(conf.metric, procname, conf));
	}
	var jobname = getArrayToORString(conf.joblist);
	if (jobname != null) {
		queries.push(jobClusterView(conf.metric, jobname, conf));
	}
	ret = new Object();
	ret.uri = genQuery(startTime, endTime, queries);
	return ret;
}

function getNodeView(startTime, endTime, conf) {
	var queries = new Array();
	var labels = new Array();
	queries.push(totNodeView(conf.metric, conf.hostid, conf));
	queries.push(totJobNodeView(conf.metric, conf.hostid, conf));
	var procname = getArrayToORString(conf.proclist);
	if (procname != null) {
		queries.push(procNodeView(conf.metric, conf.hostid, procname, conf));
	}
	var jobname = getArrayToORString(conf.joblist);
	if (jobname != null) {
		queries.push(jobNodeView(conf.metric, conf.hostid, jobname, conf));
		queries.push(slotsNodeView(conf.metric, conf.hostid, jobname, conf));		
	}
	ret = new Object();
	ret.uri = genQuery(startTime, endTime, queries);
	return ret;
}

function getCustomizedView(startTime, endTime, conf) {
	ret = new Object();	
	ret.uri = genQuery(startTime, endTime, conf.queries);
	return ret;
}

function getDashboardView(startTime, endTime, conf) {
	ret = new Object();
	ret.uri = getOpenTSDBURL()+"start="+startTime+"&end="+endTime+"&ascii&injson&"+conf.query+"&callback=?";
	return ret;
}

function setGraphToDashboard(dashboardName, graphName, queries) {
	if (queries.length <= 0)
		return;
	var graphQuery = queries[0];
	for (var i = 1; i < queries.length; ++i) {
		graphQuery += "&"+queries[i];
	}
	$.get("update/", 
		{dashboardname: dashboardName, graphname: graphName, graphquery: graphQuery},
		function (data) {
			alert("Add graph to "+dashboardName+" successfully.");
		}
	);
}

function getLabel(data) {
	var labels = new Array();
	for (var i = 0; i < data.length; ++i) {
		if (data[i]['metric'].indexOf("node") >= 0) {
			labels.push({label:"Total"});
		} else
		if (data[i]['metric'].indexOf("process") >= 0) {
			var procname = data[i]['tags']['proc'];
			if (procname == null) {
				labels.push({label: "TotalProcess"});
			} else {
				labels.push({label: procname});
			}
		} else
		if (data[i]['metric'].indexOf("mrjob") >= 0) {
			var jobid = data[i]['tags']['jobid'];
			if (jobid == null) {
				labels.push({label: "TotalMRJob"});
			} else {
				var tasktype = data[i]['tags']['tasktype'];
				if (tasktype == null) {
					labels.push({label: jobid});
				} else {
					labels.push({label: jobid+"_"+tasktype});
				}
			}
		} else {
			labels.push("unknown");
		}
	}
	return labels;
}

function getMaxDataPoint(data) {
	var max = 0;
	for (var i = 0; i < data.length; ++i) {
		for (var j = 0; j < data[i]['data'].length; ++j) {
			if (data[i]['data'][j][1] > max) {
				max = data[i]['data'][j][1];
			}
		}
	}
	return max;
}

function getAxisMax(max) {
	var base = Math.exp(Math.floor(Math.log(max) / Math.LN10) * Math.LN10);
	return Math.ceil(max / base) * base;
}

function unitFormatter(format, val) {
	if (typeof val == 'number' && val > 0) { 
		if (val >= 1) {
			var units = ['', 'K', 'M', 'G', 'T', 'P'];
			var nunit = Math.floor(Math.log(val) / Math.LN10 / 3) ;
			var base = Math.exp(nunit * 3 * Math.LN10);
			return $.jqplot.sprintf("%.1f"+units[nunit], val / base);
		} else { 
			var units = ['', 'm', 'μ', 'n'];
			var nunit = Math.ceil(Math.log(val) / Math.LN10 / 3) ;
			var base = Math.exp(nunit * 3 * Math.LN10);
			return $.jqplot.sprintf("%.1f"+units[-nunit], val / base);			
		}
	} else {
		return $.jqplot.sprintf("%.1f", val);
	}
}

function renderView(startTime, endTime, genViewFun, conf, plotdiv) {
	var ret = genViewFun(startTime, endTime, conf);
	try {
		$.getJSON(ret.uri, function(response) {
			try {
			        startTime = startTime.replace('-',' ').replace('/','-').replace('/','-')
				endTime = endTime.replace('-',' ').replace('/','-').replace('/','-')

				var datalist = new Array();
				for (var i = 0; i < response['data'].length; ++i) {
					datalist.push(response['data'][i]['data']);
				}
				var labels = getLabel(response['data']);
				var maxDataPoint = getMaxDataPoint(response['data']);
				var maxYAxis = getAxisMax(maxDataPoint);
				var jqplotConf = {
		   			seriesDefaults: {showMarker:false, showLabel: true},
		   			series: labels, 
		   		 	cursor: {
		        		show: true,
		        		tooltipLocation:'sw', 
		        		zoom:true
		      		}, 
		      		legend: {
		      			show: true
		      		},
		      		highlighter: {
		        		show: true,
		        		sizeAdjust: 7.5
		      		},      		
		          	axes: {
		          		xaxis: { 
		          			renderer: $.jqplot.DateAxisRenderer,
		          			tickOptions:{formatString:'%H:%M:%S'},
		          			label: 'Time',
		          			min: startTime,
		          			max: endTime 
		          		},
		          		yaxis: {
		          			min: 0,
		          			max: maxYAxis,
		          			label: MetricYLabel[conf.metric],
		          			labelRenderer: $.jqplot.CanvasAxisLabelRenderer,
		          			autoscale: true,
		          			tickOptions: {formatter: unitFormatter}
		          		}          	          	
		          	}
		       };
		       
		       $.jqplot(plotdiv, datalist, jqplotConf).redraw();
		   } catch (err) {
		   		alert(err.name + ":"+ err.message);
		      	alert("There is no mrjob running in the node.");
		   }
	    }).error(function() { alert("Failed to fetch data from the server"); });
	} catch (err) {
		alert("Failed to fetch data from the server");
	}
}
