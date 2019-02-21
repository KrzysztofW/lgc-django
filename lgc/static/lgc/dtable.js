function countLines(textarea) {
    var text = textarea.replace(/\s+$/g,"");
    var split = text.split("\n");
    return split.length;
}

function copyValue(oldrow, newrow) {

    function update(type, resize) {
	var oelements = oldrow.getElementsByTagName(type);
	var nelements = newrow.getElementsByTagName(type);

	if (oelements.length != nelements.length)
	    return false;

	for (var i = 0; i < oelements.length; i++){
	    nelements[i].value = oelements[i].value;
	    //if (resize) {
		//var nb_lines = countLines(nelements[i].value);
		//nelements[i].rows = nb_lines;
	    //}
	}
    }
    update('input', 0);
    update('select', 0);
    update('textarea', 1);
    update('div', 0);

    /*	var old = oldrow.getElementsByTagName('a');
	var new = newrow.getElementsByTagName('a');
	for (var i = 0; i < old.length; i++){
	if(old[i].name.match('^anchor.*')){
	alert(old[i].name + " " + old[i].text + " " + old[i].value);
	//			new[i].text='kk';
	//			new[i].value = old[i].value;
	}
	}*/
}

function changeNames(row, index) {
    var re = /(.*_)(\d+|new)$/;
    var rt = '$1' + index;

    function update(type) {
	var elements = row.getElementsByTagName(type);
	for (var i = 0, n = elements.length; i < n; i++) {
	    switch(type) {
	    case 'input': case 'select':
		var newname = elements[i].name.replace(re, rt);
		elements[i].setAttribute('name', newname);
		break;
	    case 'div':
		var newid = elements[i].id.replace(re, rt);
		elements[i].setAttribute('id', newid);
		break;
	    case 'textarea':
		var newname = elements[i].name.replace(re, rt);
		elements[i].setAttribute('name', newname);

		var newid = elements[i].id.replace(re, rt);
		elements[i].setAttribute('id', newid);

		break;
	    default:
		break;
	    }
	}
    }

    update('input');
    update('select');
    update('textarea');
    update('div');
}

function resetRow(row) {

    var elements = row.getElementsByTagName('input');
    var elements_textarea = row.getElementsByTagName('textarea');
    var elements_div = row.getElementsByTagName('div');

    for (var i = 0, n = elements.length; i < n; ++i) {
	elements[i].value = '';
	//elements[i].readOnly = true;
    }

    for (var i = 0, n = elements_textarea.length; i < n; ++i) {
	elements_textarea[i].value = '';
	elements_textarea[i].rows = 1;
	//elements_textarea[i].readOnly = true;
    }

    for (var i = 0, n = elements_div.length; i < n; ++i) {
	elements_div[i].innerHTML = '';
    }

}

function arrayInsert(button) {
    var fcell, clone, frow, brows, fsection, bsection, tbl;

    if ((fcell = button.parentNode) &&
	(frow = fcell.parentNode) &&
	(fsection = frow.parentNode) &&
	(tbl = fsection.parentNode) &&
	(bsection = tbl.tBodies[0]) &&
	(brows = bsection.rows) &&
	frow.cloneNode &&
	bsection.appendChild) {

	var oldval = button.value;
	var oldid = button.id;
	button.value = 'X';
	button.id = 'array_del';

	if ((clone = frow.cloneNode(true)) &&
	    clone.getElementsByTagName) {

	    copyValue(frow, clone);
	    //clone.style.cssText = frow.style.cssText;
	    bsection.appendChild(clone);
	    changeNames(clone, bsection.rows.length - 1);
	}

	resetRow(frow);
	button.value = oldval;
	button.id = oldid;

	return false;
    }
    return true;
}

function arrayRemove(button) {
    var cell, row, section;

    if ((cell = button.parentNode) &&
	(row = cell.parentNode) &&
	(section = row.parentNode) &&
	section.deleteRow &&
	section.rows) {
	for (i = row.sectionRowIndex + 1; i < section.rows.length;
	     i++) {
	    changeNames(section.rows[i], i - 1);
	}

	section.deleteRow(row.sectionRowIndex);
	return false;
    }
    return true;
}

function arrayAction(button) {
    if (button.id.match('.*array_insert$')) {
	arrayInsert(button);
    } else {
	arrayRemove(button);
    }
}
