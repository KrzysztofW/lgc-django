<?php

$dev = 0;
$hote = "localhost";

$utilisateur="lgc";
$pass="zqooe872Fjdhe";
$base="lgc_v5";
$c=@mysqli_connect("$hote","$utilisateur","$pass", "$base") or die('Echec de la connexion à la base de donnée');

$devises = array("EUR", "USD", "CAD", "GBP" );
$TVA = 20;

$ap_desc_line = 55;
$ap_desc_lines = 20;
define("__FACTURE_MAX_LINES__", 50);
define("__NB_FACT_COL__", 16);
define("__FILE_NB_LINES__", 50);
define("__FRAIS_DIVERS_RATE__", 5);
define("__FRAIS_DIVERS_LIMIT__", 100);
define("__MARGE_DEB__", 20);

define("__DEBUG_LGC__", 1);
define("__DEBUG_FILE__", "/management/lgc/www/logs/lgc.log");
define("__DEBUG_EMAIL__", "admin@example.com");

if ($dev) {
	$invoice_alert_emails_to = "admin2@example.com,admin@example.com";
	$invoice_alert_emails_cc = "admin@example.com,admin2@example.com";
	$invoice_alert_nb_days = 2;
} else {
	$invoice_alert_emails_cc = "btissam.bougrine@example.com";
	$invoice_alert_nb_days = 90;
}

?>
