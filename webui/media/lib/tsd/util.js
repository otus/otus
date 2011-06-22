function getArrayToORString(strarray) {
	if (strarray.length == 0) {
		return null;
	}
	var ret = strarray[0];
	for (var i = 1; i < strarray.length; ++i) {
		ret += "|" + strarray[i];
	}
	return ret;
}

function getObjStrValue(id, initVal) {
	var val = $(id).val();
	if (val == null || val == "") {
		return initVal;
	} else {
		return val;
	}
}
