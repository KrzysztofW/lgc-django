var url;
var delim = /,/;

$(document).ready(function(){
    url = $("#search").attr("ajax-search");
    d = $("#search").attr("delim");
    if (d == "break")
	delim = /\n/;
    $(".clickable-row").click(function() {
        window.location = $(this).data("href");
    });
});

$("#search_box").keyup(function (event) {
    var term = $("#search_box").val();

    if (term.length < 2)
	return;
    if (event.keyCode === 13) {
	$("#search").submit();
	return;
    }
    if (event.keyCode == 40 || event.keyCode == 38)
	return;
    $.ajax({
	url: url,
	data: {
	    'term': term
	},
	success: function (data) {
	    var array;
	    var array2 = [];

	    data = data.replace(/,\n/gm, "");
	    if (data != "")
		array = data.split(delim);
	    for (var item in array) {
		if (array[item] == "" || array[item] == '\n')
		    continue;
		array2.push(array[item]);
	    }
	    autocomplete(document.getElementById("search_box"), array2);
	}
    });
});

function autocomplete(inp, arr) {
    var currentFocus = -1;

    inp.addEventListener("input", function(e) {
	var a, b, i, val = this.value;
	/* close any already open lists of autocompleted values */
	closeAllLists();
	if (!val || typeof arr == 'undefined')
	    return false;

	currentFocus = -1;
	/* create a DIV element that will contain the items (values): */
	a = document.createElement("DIV");
	a.setAttribute("id", this.id + "autocomplete-list");
	a.setAttribute("class", "autocomplete-items");
	/* append the DIV element as a child of the autocomplete container: */
	this.parentNode.appendChild(a);
	/* for each item in the array... */
	for (i = 0; i < arr.length; i++) {
	    val = val.toLowerCase();

	    /* create a DIV element for each matching element: */
	    b = document.createElement("DIV");
	    b.innerHTML = arr[i].replace(val, "<strong>" + val + "</strong>");
	    b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
	    b.addEventListener("click", function(e) {
		inp.value = this.getElementsByTagName("input")[0].value;
		closeAllLists();
	    });
	    a.appendChild(b);
	}
    });

    inp.addEventListener("keydown", function(e) {
	var x = document.getElementById(this.id + "autocomplete-list");
	if (x) x = x.getElementsByTagName("div");
	if (e.keyCode == 40) {
	    /* If the arrow DOWN key is pressed,
	     * increase the currentFocus variable: */
	    currentFocus++;
	    /* and and make the current item more visible: */
	    addActive(x);
	} else if (e.keyCode == 38) { //up
	    /* If the arrow UP key is pressed,
	     * decrease the currentFocus variable: */
	    currentFocus--;
	    /* and and make the current item more visible: */
	    addActive(x);
	} else if (e.keyCode == 13) {
	    /* If the ENTER key is pressed, prevent the form from being submitted */
	    e.preventDefault();
	    if (currentFocus > -1) {
		/* and simulate a click on the "active" item: */
		if (x) x[currentFocus].click();
	    }
	}
    });
    function addActive(x) {
	/* a function to classify an item as "active": */
	if (!x) return false;
	/* start by removing the "active" class on all items: */
	removeActive(x);
	if (currentFocus >= x.length) currentFocus = 0;
	if (currentFocus < 0) currentFocus = (x.length - 1);
	/* add class "autocomplete-active": */
	x[currentFocus].classList.add("autocomplete-active");
    }
    function removeActive(x) {
	/* a function to remove the "active" class from all autocomplete items: */
	for (var i = 0; i < x.length; i++) {
	    x[i].classList.remove("autocomplete-active");
	}
    }
    function closeAllLists(elmnt) {
	/* close all autocomplete lists in the document,
	 * except the one passed as an argument: */
	var x = document.getElementsByClassName("autocomplete-items");
	for (var i = 0; i < x.length; i++) {
	    if (elmnt != x[i] && elmnt != inp) {
		x[i].parentNode.removeChild(x[i]);
	    }
	}
    }
    /* execute a function when someone clicks in the document: */
    document.addEventListener("click", function (e) {
	closeAllLists(e.target);
	$("#search").submit();
    });
}

function specific_stage_action(elem) {
    var div = document.getElementById('specific_stage');

    if (elem.id == 'id_action_2')
	div.style.display = "inline";
    else
	div.style.display = "none";
}

var lgc_tab_link_ids = []
var lgc_tab_body_ids = []

function get_lgc_links() {
    var active_tab = document.getElementById('id_active_tab');
    var l = document.links;

    for (var i = 0; i < l.length; i++) {
      if (l[i].id.match('^lgc-tab.*$')) {
	lgc_tab_link_ids.push(l[i].id);
	lgc_tab_body_ids.push(l[i].id.substring(8));
      }
    }

    if (active_tab && typeof active_tab !== 'undefined') {
	var body_id = active_tab.value.substring(8);
	var tab_body = document.getElementById(body_id);
	var tab = document.getElementById(active_tab.value);

      if (tab && typeof tab !== 'undefined' &&
	  tab_body && typeof tab_body !== 'undefined') {
	for (var i = 0; i < lgc_tab_body_ids.length; i++) {
	  var pane = document.getElementById(lgc_tab_body_ids[i]);
	  pane.className = "tab-pane";
	}
	tab_body.className = "tab-pane show active";
	tab.className = "nav-link active show";
      } else {
	var tab = document.getElementById(lgc_tab_link_ids[0]);
	if (tab) {
	  tab.className = "nav-link active show";
	}
      }
    }
}

function select_tab(elem) {
    var active_tab = document.getElementById('id_active_tab');

    for (var i = 0; i < lgc_tab_link_ids.length; i++) {
	if (lgc_tab_link_ids[i] == elem.id) {
	    active_tab.value = elem.id;
	    break;
	}
    }
}
