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

function listener_cb(inp, arr) {
    var a, b, i, val = inp.value;
    /* close any already open lists of autocompleted values */
    closeAllLists(null, inp);
    if (!val || typeof arr == 'undefined')
	return false;

    currentFocus = -1;
    /* create a DIV element that will contain the items (values): */
    a = document.createElement("DIV");
    a.setAttribute("id", inp.id + "autocomplete-list");
    a.setAttribute("class", "autocomplete-items");
    /* append the DIV element as a child of the autocomplete container: */
    inp.parentNode.appendChild(a);
    /* for each item in the array... */
    for (i = 0; i < arr.length; i++) {
	val = val.toLowerCase();
	/* create a DIV element for each matching element: */
	b = document.createElement("DIV");
	b.innerHTML = arr[i].replace(val, "<strong>" + val + "</strong>");
	b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
	b.addEventListener("click", function(e) {
	    input_values = this.getElementsByTagName("input")
	    inp.value = input_values[0].value;
	    closeAllLists(null, inp);
	});
	a.appendChild(b);
    }
}

function closeAllLists(elmnt, inp) {
    /* close all autocomplete lists in the document,
     * except the one passed as an argument: */
    var x = document.getElementsByClassName("autocomplete-items");
    for (var i = 0; i < x.length; i++) {
	if (elmnt != x[i] && elmnt != inp) {
	    x[i].parentNode.removeChild(x[i]);
	}
    }
}


$("#search_box").keyup(function (event) {
    if (url == '')
       return;
    var term = $("#search_box").val();

    if (term.length == 0)
	return;

    if (event.keyCode === 13) {
	$("#search").submit();
	return;
    }

    /* ignore up/down arrow keys */
    if (event.keyCode == 40 || event.keyCode == 38)
	return;

    /* ignore left/right arrow keys */
    if (event.keyCode == 37 || event.keyCode == 39)
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

	    /* remove duplicates */
	    set = new Set(array2);
	    array = Array.from(set);

	    search_box = document.getElementById("search_box");
	    autocomplete(search_box, array);
	    listener_cb(search_box, array);
	}
    });
});

function autocomplete(inp, arr) {
    var currentFocus = -1;

    inp.addEventListener("input", function(e) {
	listener_cb(inp, arr);
    });
    function show_completed(e, keyCode) {
	var x = document.getElementById(inp.id + "autocomplete-list");

	if (x)
		x = x.getElementsByTagName("div");
	if (keyCode == 40) {
	    /* If the arrow DOWN key is pressed,
	     * increase the currentFocus variable: */
	    currentFocus++;
	    /* and make the current item more visible: */
	    addActive(x);
	} else if (keyCode == 38) { //up
	    /* If the arrow UP key is pressed,
	     * decrease the currentFocus variable: */
	    currentFocus--;
	    /* and and make the current item more visible: */
	    addActive(x);
	} else if (keyCode == 13) {
	    /* If the ENTER key is pressed, prevent the form from being submitted */
	    e.preventDefault();
	    if (currentFocus > -1) {
		/* and simulate a click on the "active" item: */
		if (x) x[currentFocus].click();
	    }
	}
    }

    inp.addEventListener("keydown", function(e) {
	show_completed(e, e.keyCode);
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
    show_completed(null, 38);
    /* execute a function when someone clicks in the document: */
    document.addEventListener("click", function (e) {
	closeAllLists(e.target, inp);
	$("#search").submit();
    });
}

function specific_stage_action(elem) {
    var div = document.getElementById('specific_stage');

    if (elem.id == 'id_id_action_0_3')
	div.style.display = "inline";
    else
	div.style.display = "none";
}

var lgc_tab_link_ids = []
var lgc_tab_body_ids = []

function get_lgc_links() {
    var active_tab = document.getElementById('id_active_tab');
    var l = document.links;

    /* build IDs */
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
	    /* set first tab as active */
	    active_tab.value = lgc_tab_link_ids[0];
	    tab = document.getElementById(lgc_tab_link_ids[0]);
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

var prefecture_select = [];
var subprefecture_select = [];
var direccte_select = [];
var jurisdiction_select = [];
var consulate_select = [];

function __fill_select(selectobject, array) {
    for (var i = 0; i < selectobject.length; i++)
	array.push(selectobject[i]);
}

function fill_selects() {
    var prefecture = document.getElementById("id_prefecture");
    var subprefecture = document.getElementById("id_subprefecture");
    var direccte = document.getElementById("id_direccte");
    var jurisdiction = document.getElementById("id_jurisdiction");
    var consulate = document.getElementById("id_consulate");

    __fill_select(prefecture, prefecture_select);
    __fill_select(subprefecture, subprefecture_select);
    __fill_select(direccte, direccte_select);
    __fill_select(jurisdiction, jurisdiction_select);
    __fill_select(consulate, consulate_select);
}

function find_in_select(select, str) {
    var re = new RegExp(str + '.*');

    for (var i = 0; i < select.length; i++) {
	if (select[i].text.match(re))
	    return true;
    }
    return false;
}

function empty_select(select) {
    while (select.options.length)
	select.remove(0);
}

function build_select(from_select, to_select, str) {
    var re = new RegExp(str + '.*');

    empty_select(to_select);
    for (var i = 0; i < from_select.length; i++) {
	if (from_select[i].text.match(re))
	    to_select.appendChild(from_select[i]);
    }
}

function build_selects(post_code) {
    var prefecture = document.getElementById("id_prefecture");
    var subprefecture = document.getElementById("id_subprefecture");
    var direccte = document.getElementById("id_direccte");

    code = post_code.substr(0, 2);
    build_select(prefecture_select, prefecture, code);
    build_select(subprefecture_select, subprefecture, code);
    build_select(direccte_select, direccte, code);
}

function auto_complete_region(elem) {
    if (elem.value == '')
	return;

    if (prefecture_select.length == 0)
	fill_selects();

    post_code = elem.value.match(/\d{5}/)
    if (post_code && post_code.length)
	build_selects(post_code[0]);
}

function auto_complete_jurisdiction(elem) {
    if (elem.value == '')
	return;

    if (prefecture_select.length == 0)
	fill_selects();

    country = elem.value
    if (!country || country.length == 0)
	return;

    var jurisdiction = document.getElementById("id_jurisdiction");
    empty_select(jurisdiction);

    for (var i = 0; i < jurisdiction_select.length; i++) {
	c = jurisdiction_select[i].value.substr(0, 2);
	if (c && c == country)
	    jurisdiction.appendChild(jurisdiction_select[i]);
    }

    var consulate = document.getElementById("id_consulate");
    empty_select(consulate);

    for (var i = 0; i < consulate_select.length; i++) {
	c = consulate_select[i].value;
	if (c && c == country)
	    consulate.appendChild(consulate_select[i]);
    }
}

function compute_invoice() {
  var various_expenses_input = document.getElementById('id_various_expenses');

  var items_total_div = document.getElementById('id_items_total_div');
  var items_total_vat_div = document.getElementById('id_items_total_vat_div');

  var already_paid_div = document.getElementById('id_already_paid_div');
  var already_paid_input = document.getElementById('id_already_paid');
  var already_paid = 0;

  var disbursements_total_div = document.getElementById('id_disbursements_total_div');
  var disbursements_total_vat_div = document.getElementById('id_disbursements_total_vat_div');

  var total_div = document.getElementById('id_total_div');
  var total_vat_div = document.getElementById('id_total_vat_div');
  var invoice_total_div = document.getElementById('id_invoice_total_div');
  var invoice_total_input = document.getElementById('id_total');

  var items_total = 0;
  var items_total_vat = 0;
  var disbursements_total = 0;
  var disbursements_total_vat = 0;

  var subtotal = 0;
  var subtotal_vat = 0;
  var invoice_total = 0;

  var various_expenses = 0;
  var various_expenses_vat = 0;
  var first_item_vat = 0;
  var i = 0;

  while (document.getElementById('id_items-'+i+'-description') !== null) {
    var rate_input = document.getElementById('id_items-'+i+'-rate');
    var quantity_input = document.getElementById('id_items-'+i+'-quantity');
    var vat_input = document.getElementById('id_items-'+i+'-vat');
    var total_input = document.getElementById('id_items-'+i+'-total');
    var total = 0;
    var rate_quantity = 0;

    rate = parseFloat(rate_input.value);
    quantity = parseFloat(quantity_input.value);
    rate_quantity = rate * quantity;
    vat = parseFloat(vat_input.value) / 100;

    /* this will be used to compute various expenses */
    if (i == 0)
      first_item_vat = vat;

    total = rate_quantity * (1 + vat);
    total_input.value = total.toFixed(2);

    items_total += rate_quantity
    items_total_vat += rate_quantity * vat;

    i++;
  }

  i = 0;
  while (document.getElementById('id_disbursements-'+i+'-description') !== null) {
    var rate_input = document.getElementById('id_disbursements-'+i+'-rate');
    var quantity_input = document.getElementById('id_disbursements-'+i+'-quantity');
    var vat_input = document.getElementById('id_disbursements-'+i+'-vat');
    var margin_input = document.getElementById('id_disbursements-'+i+'-margin');
    var total_input = document.getElementById('id_disbursements-'+i+'-total');
    var margin = 20 / 100.; // 20%

    var rate_quantity = 0;
    var total = 0;

    rate = parseFloat(rate_input.value);
    quantity = parseFloat(quantity_input.value);
    rate_quantity = rate * quantity;
    vat = parseFloat(vat_input.value) / 100.;

    total = rate_quantity * (1 + vat);

    if (margin_input.checked)
      total = total * (1 + margin);

    total_input.value = total.toFixed(2);

    disbursements_total += rate_quantity;
    disbursements_total_vat += rate_quantity * vat;

    if (margin_input.checked) {
      disbursements_total += rate_quantity * margin;
      disbursements_total_vat += (rate_quantity * vat) * margin;
    }
    i++;
  }

  items_total_div.innerHTML = items_total.toFixed(2);
  items_total_vat_div.innerHTML = items_total_vat.toFixed(2);

  if (various_expenses_input.checked) {
    various_expenses = items_total *  5/100.;

    if (various_expenses > 100)
      various_expenses = 100;
    various_expenses_vat = various_expenses * first_item_vat;
  }

  disbursements_total += various_expenses;
  disbursements_total_vat += various_expenses_vat;
  disbursements_total_div.innerHTML = disbursements_total.toFixed(2);
  disbursements_total_vat_div.innerHTML = disbursements_total_vat.toFixed(2);

  if (already_paid_input !== null)
    already_paid = parseFloat(already_paid_input.value);
  already_paid_div.innerHTML = already_paid.toFixed(2);

  subtotal = items_total + disbursements_total;
  subtotal_vat =items_total_vat + disbursements_total_vat;

  total_div.innerHTML = '<b>' + subtotal.toFixed(2) + '</b>';
  total_vat_div.innerHTML = '<b>' + subtotal_vat.toFixed(2) + '</b>';

  invoice_total = items_total + items_total_vat + disbursements_total + disbursements_total_vat;
  if (already_paid)
    invoice_total -= already_paid;

  invoice_total_div.innerHTML = '<b>' + invoice_total.toFixed(2) + '</b>';
  invoice_total_input.value = invoice_total.toFixed(2);
}

function client_id_check(client_id) {
  if (!client_id || typeof client_id == 'undefined')
    return false;

  if (client_id.value == '') {
    $.notify("{% trans 'Client not set' %}",
	     {
	       className: 'error',
	       position: 'top center',
	     });
    return false;
  }
  return true;
}

function invoice_form_checks(msg) {
  var state_elem = document.getElementById('id_state');

  if (state_elem && state_elem.value == 'V') {
    if (!confirm(msg))
      return false;
  }
  return client_id_check(document.getElementById('id_client'));
}

function remove_item(index, formset_id) {
  var description_input;

  if (formset_id == 'items_id')
    description_input = document.getElementById('id_items-' + index + '-rate');
  else if (formset_id == 'disbursements_id')
    description_input = document.getElementById('id_disbursements-' + index + '-rate');

  description_input.value = 0;
  compute_invoice();
}

function insert_item(url, element, index) {
    var currency = document.getElementById('id_currency');
    url = url + '?index=' + index + '&currency=' + currency.value;
    window.open(url, 'newwindow', config='height=400,width=950, toolbar=no, menubar=no,scrollbars=yes, resizable=no,location=no,directories=no, status=no');
    return false;
}

function invoice_validated_state_alert(elem, msg) {
  if (elem.value == "V")
    alert(msg);
}

function invoice_confirm_validated_state(elem, msg) {
  return confirm(msg);
}
