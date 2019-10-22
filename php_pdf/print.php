#!/usr/bin/php
<?php
#print "$argc arguments were passed. In order: \n";

#for ($i = 0; $i <= $argc -1; ++$i) {
#    print "$i: $argv[$i]\n";
#}

# id

$id = $argv[1];

require('fpdf.php');
require('config.php');
require("print_msg.php");
include "facture_functions.php";

$pdflog_file = "/tmp/pdf.log";
$fh = fopen($pdflog_file, 'w') or die("can't open file");
//foreach($_POST as $val => $key)  fwrite($fh, "$val => $key\n");

function get_devise($lang, $devise)
{
	if ($lang == "FR") {
		switch ($devise) {
		case "EUR":
			return "Euro";
			break;
		case "USD":
			return "Dollar";
			break;
		case "CAD":
			return "Dollar canadien";
			break;
		case "GBP":
			return "Livre";
			break;
		default :
			return $devise;
		}
	} else if ($lang == "EN") {
		switch ($devise) {
		case "EUR":
			return "In euros";
			break;
		case "USD":
			return "In US dollars";
			break;
		case "CAD":
			return "In Canadian dollars";
			break;
		case "GBP":
			return "In pounds";
			break;
		default :
			return $devise;
		}
	}
}

function get_month($lang, $nb)
{
	if ($lang == "FR") {
		switch ($nb) {
		case 1:
			return "Janvier";
			break;
		case 2:
			return "Fevrier";
			break;
		case 3:
			return "Mars";
			break;
		case 4:
			return "Avril";
			break;
		case 5:
			return "Mai";
			break;
		case 6:
			return "Juin";
			break;
		case 7:
			return "Juillet";
			break;
		case 8:
			return "Août";
			break;
		case 9:
			return "Septembre";
			break;
		case 10:
			return "Octobre";
			break;
		case 11:
			return "Novembre";
			break;
		case 12:
			return "Décembre";
			break;

		default:
			return "Janvier";
		}
	} else if ($lang == "EN") {
		switch ($nb) {
		case 1:
			return "January";
			break;
		case 2:
			return "February";
			break;
		case 3:
			return "March";
			break;
		case 4:
			return "April";
			break;
		case 5:
			return "May";
			break;
		case 6:
			return "June";
			break;
		case 7:
			return "July";
			break;
		case 8:
			return "August";
			break;
		case 9:
			return "September";
			break;
		case 10:
			return "October";
			break;
		case 11:
			return "November";
			break;
		case 12:
			return "December";
			break;

		default:
			return "January";
		}
	}
}

function get_mode($lang, $mode) {
	if ($lang == "FR") {
		switch ($mode) {
		case "BT":
			return "virement";
			break;
		case "CB":
			return "carte bancaire";
			break;
		case "CH":
			return "chèque";
			break;
		case "CA":
			return "espèces";
			break;
		#case "FR":
		#	return "traite";
		#	break;
		default:
			return '';
		}
	} else if ($lang == "EN") {
		switch ($mode) {
		case "BT":
			return "bank transfer";
			break;
		case "CB":
			return "credit card";
			break;
		case "CH":
			return "cheque";
			break;
		case "CA":
			return "";
			break;
		default:
			return '';
		}
	}
}


class PDF extends FPDF
{
	public $date;

	function set_date($date)
	{
		$this->date = $date;
	}
	// Page header
	function Header()
	{
		// Logo
		//$this->Image('logo.png',10,6,30);
		// Arial bold 15
		$this->SetFont('Times','B',16);
		// Move to the right
		$this->Cell(80);
		// Title
		$this->Cell(20,0,'K A R L   W A H E E D  A V O C A T S',0,0,'C');
		// Line break
		$this->Ln(0);
		$this->SetFont('Times','',9);
		$this->Cell(80);
		//$this->Cell(20,12,'A V O C A T S',0,0,'C');
		$this->Ln(9);
		$this->Cell(0,5,'Toque C 818',0,0,'L');
		$this->SetFont('Times','I',9);
		$this->Cell(0,5,'-at-law (New York)',0,0,'R');
		$this->Ln(15);
		$this->Rect(20, 25, 170, 0.4, 'F');
	}

	// Page footer
	function Footer()
	{
		// Position at 1.5 cm from bottom
		if (!$this->date or $this->date >= "2019-01-01")
			$this->SetY(-15);
		else
			$this->SetY(-11);
		$this->SetFont('Times','',9);
		if (!$this->date or $this->date >= "2019-01-01") {
			$this->Cell(0, 10, "Office SARL", 0,0,'C');
			$this->Ln(4);
		}

		$this->Cell(0,10, 'Address - Téléphone : 00 (0) 1 23 45 67 89 Télécopie : 00 (0) 1 23 45 67 89 office@exemple.com', 0, 0, 'C');
		$this->Ln(4);
		if ($this->date and $this->date < "2019-01-01")
			$this->Cell(0,10, 'N° SIRET : 43754338200026 - APE 741A - N° TVA intracommunautaire : FR65437543382',0,0,'C');
		else
			$this->Cell(0,10, 'N° SIRET : 84497614200019 - APE 741A - N° TVA intracommunautaire : FR84844976142',0,0,'C');

		// Arial italic 8
		//$this->SetFont('Arial','I',8);
		// Page number
		//$this->Cell(0,10,'Page '.$this->PageNo().'/{nb}',0,0,'C');
	}
}

if (!isset($id)) {
	fwrite($fh, "error line ".__LINE__."\n");
	exit;
 }

$sql = "select * from lgc_invoice where id=$id;";
$resultat = mysqli_query($c, $sql);

if (! $resultat) {
	fwrite($fh, "impossible de s&eacute;lectionner facture: ligne=".__LINE__."\n");
	fwrite($fh, "$sql\n");
	exit;
}
$row = mysqli_fetch_assoc($resultat);
if ($row['type'] == 'C')
	$prefix = 'AV';
else if ($row['type'] == 'Q')
        $prefix = 'DE';
else
	$prefix = 'FA';

$id_facture = $row['number'];
$file_id = $row['person_id'];

$pdf = new PDF();
$pdf->set_date($row['invoice_date']);
$pdf->SetMargins(20, 10, 20);

$pdf->AliasNbPages();
$pdf->AddPage();
$lang = $row['language'];

$pdf->SetFont('Times','B', 11);
if ($row['type'] == 'Q')
	$pdf->Cell(0, 10, $devis[$lang], 0, 0, 'C');
else if ($row['type'] == 'C')
	$pdf->Cell(0, 10, $avoir[$lang], 0, 0, 'C');
else
	$pdf->Cell(0, 10, $note_honoraires_et_frais[$lang], 0, 0, 'C');

$pdf->Ln(15);
$pdf->SetFont('Times','', 11);
if ($lang == "FR") {
	if (preg_match("/^([1-2][0-9][0-9][0-9])-([0-1][0-9])-([0-3][0-9])$/", $row['invoice_date'], $regs))
		$pdf->Cell(0,10,"London, le $regs[3] ". get_month($lang, $regs[2]) . " $regs[1]",0,0,'R');
} else if ($lang == "EN") {
	if (preg_match("/^([1-2][0-9][0-9][0-9])-([0-1][0-9])-([0-3][0-9])$/", $row['invoice_date'], $regs))
		$pdf->Cell(0,10, "$regs[3] ".get_month($lang, $regs[2])." $regs[1]",0,0,'R');
}
if ($lang == "FR") {
	if (preg_match("/^([1-2][0-9][0-9][0-9])-([0-1][0-9])-([0-3][0-9])$/", $row['modification_date'], $regs)) {
		$pdf->SetFont('Times','I', 9);
		$pdf->Ln(5);
		$pdf->Cell(0,10, "Modifiée le $regs[3] " . get_month($lang, $regs[2])." $regs[1]",0,0,'R');
		$pdf->SetFont('Times','', 11);
	}
} else if ($lang == "EN") {
	if (preg_match("/^([1-2][0-9][0-9][0-9])-([0-1][0-9])-([0-3][0-9])$/", $row['modification_date'], $regs)) {
		$pdf->SetFont('Times','I', 9);
		$pdf->Ln(5);
		$pdf->Cell(0,10,"Modified ".get_month($lang, $regs[2])." $regs[3], $regs[1]",0,0,'R');
		$pdf->SetFont('Times','', 11);
	}
}

$pdf->Ln(5);

$pdf->SetFont('Times','B', 11);
$pdf->Cell(0,0, $row['company'],0,0,'L');
$pdf->Ln(5);
$pdf->Cell(0,0, $row['first_name'] . " " . $row['last_name'], 0,0,'L');
$pdf->Ln(5);


$pdf->SetFont('Times','', 11);

$pieces = explode("\n", $row['address']);

foreach ($pieces as $val => $key) {
	$pdf->Cell(0, 0, "$key", 0, 0, 'L');
	$pdf->Ln(4);
}
$pdf->Ln(1);

if (!empty($row['post_code']))
	$cpville = $row['post_code'];

if (!empty($row['city']))
	$cpville = "$cpville" . " " .$row['city'];
if (!isset($cpville))
   $cpville = '';

$pdf->Cell(0, 0, $cpville, 0, 0, 'L');
$pdf->Ln(5);

$country = $row['country'];
if (!empty($country)) {
	$pdf->Cell(0,0, $countries[$country],0,0,'L');
	$pdf->Ln(5);
}

$pdf->Ln(5);
if (!empty($row['siret'])) {
	$pdf->Cell(0, 0, "SIRET : ".$row['siret'], 0, 0, 'L');
	$pdf->Ln(5);
}

if (!empty($row['vat'])) {
	$pdf->Cell(0, 0, $TVA_txt[$lang] ." : ".$row['vat'], 0, 0, 'L');
	$pdf->Ln(5);
}

if (!empty($row['po_last_name']) || !empty($row['po_first_name'])) {
	$pdf->Cell(0,10, $autorisation[$lang].":  " . $row['po_first_name'] ." ". $row['po_last_name'],0,0,'L');
	$pdf->Ln(5);
}

if (!empty($row['po_email'])) {
	$pdf->Cell(0,10,'E-mail :' . " " . $row['po_email'],0,0,'L');
	$pdf->Ln(5);
}

$pdf->Ln(5);
if ($row['type'] == 'C')
	$doc_number = $avoir_no[$lang];
else if ($row['type'] == 'Q')
	$doc_number = $devis_no[$lang];
else
	$doc_number = $facture_no[$lang];
$pdf->Cell(0, 10, $doc_number . ": " . $prefix . str_pad($row['number'], 5, "0", STR_PAD_LEFT),0,0,'L');
if (!empty($row['payment_option'])) {
	$pdf->Ln(5);
	$str = get_mode($lang, $row['payment_option']);
	$pdf->Cell(0, 10, $mode_reglement[$lang] . " " .$str,0,0,'L');
}
if (! empty($row['po'])) {
	$pdf->SetFont('Times','B', 11);
	$pdf->Ln(5);
	$pdf->Cell(0, 10, 'PO : ' . $row['po'], 0, 0, 'L');
	$pdf->SetFont('Times','', 11);
}
if (! empty($row['with_regard_to'])) {
	$pdf->Ln(5);
	$pdf->Cell(0, 10, $concernant_msg[$lang] . $row['with_regard_to'], 0, 0, 'L');
}

if (! empty($file_id)) {
	$sql = "select u.last_name, u.first_name from lgc_person_responsible r, users_user u where r.person_id='".$file_id."' and u.id=r.user_id;";
	$resultat = mysqli_query($c, $sql);
	if ($resultat) {
		$pdf->Ln(5);
		$first = 1;
		$str = "";
		while ($row_resp = mysqli_fetch_assoc($resultat)) {
			if ($first) {
				$first = 0;
				$str = $row_resp['last_name'] . " " . $row_resp['first_name'];
			} else
				$str = "$str, " . $row_resp['last_name']. " " . $row_resp['first_name'];
		}
		$pdf->Cell(0, 10, $resp_msg[$lang] . " $str");
	}
}
$pdf->Ln(15);

/* diligences */

$ret_deb_dil = get_dil_total_pdf($id, $pdf, $fh);
$t_notva = $ret_deb_dil['t_notva'];
$t_tva = $ret_deb_dil['t_tva'];
$t_tva_ht = $ret_deb_dil['t_tva_ht'];
$total_ht = $ret_deb_dil['total_ht'];
$total = $ret_deb_dil['total'];

$pdf->Ln(6);

$pdf->SetFont('Times','B', 11);
$pdf->Cell(20);

$euro_val = "";
$pdf->Cell(25, 0, get_devise($lang, $row['currency']), 0, 0, 'L');
$pdf->SetFont('Times','', 11);
$pdf->Cell(0, 0, $euro_val, 0, 0, 'L');
$pdf->Ln(5);
$pdf->Cell(32);
$pdf->Cell(78, 0, $honoraires[$lang], 0, 0, 'L');
$pdf->Cell(10);
$pdf->Cell(30, 0, number_format($total_ht, 2, ',', ' '), 0, 0, 'R');
$pdf->Ln(10);
#
#
#/* debours */
#
$pdf->Cell(32);
$pdf->Cell(78, 0, $debours[$lang], 0, 0, 'L');
$pdf->Ln(1);

if ($row['various_expenses'])
	$dil_total_ht = $ret_deb_dil['total_ht'];
else
	$dil_total_ht = 0;
$ret_deb_dil = get_deb_total_pdf($id, $pdf, $fh, $dil_total_ht);
$t_notva += $ret_deb_dil['t_notva'];
$t_tva += $ret_deb_dil['t_tva'];
$t_tva_ht += $ret_deb_dil['t_tva_ht'];
$total_ht += $ret_deb_dil['total_ht'];
$total += $ret_deb_dil['total'];

$pdf->Ln(1);
$pdf->Cell(132);
$Xabs = $pdf->GetX();
$Yord = $pdf->GetY();

if ($lang == "FR" or $t_tva_ht > 0 or $t_tva > 0 or $row['already_paid'] > 0)
	$pdf->Line($Xabs, $Yord, $Xabs + 17, $Yord);

if ($t_tva_ht > 0 or $lang == "FR") {
	$pdf->Ln(3);
	$pdf->Cell(60);
	$pdf->Cell(60, 0, $total_soumis_tva[$lang], 0, 0, 'L');
	$pdf->Cell(30, 0, number_format($t_tva_ht, 2, ',', ' '), 0, 0, 'R');
}

if ($t_notva > 0 or $lang == "FR") {
	if ($lang != "EN" or $t_tva_ht > 0) {
		$pdf->Ln(5);
		$pdf->Cell(60);
		$pdf->Cell(60, 0, $non_soumis[$lang], 0, 0, 'L');
		$pdf->Cell(30, 0, number_format($t_notva, 2, ',', ' '), 0, 0, 'R');
	}
}

if ($t_tva > 0 or $lang == "FR") {
	$pdf->Ln(5);
	$pdf->Cell(60);
	//XXX 19.6 or 0 !!!
	$pdf->Cell(60, 0, $TVA_txt[$lang]." ($TVA %) :", 0, 0, 'L');
	$pdf->Cell(30, 0, number_format($t_tva, 2, ',', ' '), 0, 0, 'R');
}

if (! empty($row['already_paid']) and $row['already_paid'] != 0) {
	$pdf->Ln(5);
	$pdf->Cell(60);
	if (!empty($row['already_paid_desc'])) {
		$desc = "(" . substr($row['already_paid_desc'], 0, 30) . ")";
	} else {
		$desc = "";
	}
	$pdf->Cell(60, 0, $deja_regle[$lang] ." $desc" ." :", 0, 0, 'L');
	$pdf->Cell(30, 0, number_format($row['already_paid'], 2, ',', ' '), 0, 0, 'R');
	$total -=  $row['already_paid'];
}

$pdf->Ln(2.5);
$pdf->Cell(132);
$Xabs = $pdf->GetX();
$Yord = $pdf->GetY();
$pdf->Line($Xabs, $Yord, $Xabs + 17, $Yord);

$pdf->Ln(2.5);
$pdf->Cell(60);
$pdf->Cell(60, 0, $montant[$lang], 0, 0, 'L');
$pdf->SetFont('Times','B', 11);
$pdf->Cell(30, 0, number_format($total, 2, ',', ' '), 0, 0, 'R');

$pdf->Ln(20);
$pdf->SetFont('Times','', 11);
$pdf->Cell(10, 0, $en_votre_aimable_reglement[$lang], 0, 0, 'L');
$pdf->Ln(4);
$pdf->SetFont('Times','', 9);
$pdf->Cell(10, 0, $changement_coordonnees_bancaires_1[$lang], 0, 0, 'L');
if ($lang == "FR") {
	$pdf->Ln(3);
	$pdf->Cell(10, 0, $changement_coordonnees_bancaires_2[$lang],
		   0, 0, 'L');
}
$pdf->SetFont('Times','', 11);
if ($lang == "EN")
	$pdf->Ln(4);

$pdf->SetFont('Times','', 10);
$pdf->Ln(4);
$pdf->Cell(60);
if ($row['invoice_date'] >= "2019-01-01")
        $pdf->Cell(60, 0, "Office SARL", 0, 0, 'L');
else
        $pdf->Cell(60, 0, "Office", 0, 0, 'L');

$pdf->Ln(4);
$pdf->Cell(60);
$pdf->Cell(60, 0, "Banque : Crédit Coopératif", 0, 0, 'L');

$pdf->Ln(4);
$pdf->Cell(60);
$pdf->Cell(60, 0, "252, Boulevard Voltaire, 75011 London - France", 0, 0, 'L');

$pdf->Ln(4);
$pdf->Cell(60);
if ($row['invoice_date'] < "2019-01-01")
	$pdf->Cell(60, 0, "N° de compte : 42559 10000 08001518478 95", 0, 0, 'L');
else
	$pdf->Cell(60, 0, "N° de compte : 42559 10000 08023340650 43", 0, 0, 'L');

$pdf->Ln(4);
$pdf->Cell(60);

if ($row['invoice_date'] < "2019-01-01")
	$pdf->Cell(60, 0, "IBAN: FR76 4255 9100 0008 0015 1847 895", 0, 0, 'L');
else
	$pdf->Cell(60, 0, "IBAN: FR76 4255 9100 0008 0233 4065 043", 0, 0, 'L');

$pdf->Ln(4);
$pdf->Cell(60);
$pdf->Cell(60, 0, "SWIFT: CCOPFRPPXXX", 0, 0, 'L');


$pdf->Ln(16);
$pdf->SetFont('Times','', 9);
if ($lang == "FR") {
	$pdf->Cell(10, 0, "Le paiement est dû à la réception de la présente note d'honoraires. Si le paiement n'est pas reçu dans les 45 jours suivant la réception", 0, 0, 'L');
	$pdf->Ln(3);
	$pdf->Cell(10, 0, "de la présente note d'honoraires le montant dû sera assujetti à une pénalité. Le taux de pénalité exigible sera le taux", 0, 0, 'L');
	$pdf->Ln(3);
	$pdf->Cell(10, 0, "le plus élevé autorisé par la législation française. En outre, en cas de retard de paiement, les clients professionnels seront soumis", 0, 0, 'L');
	$pdf->Ln(3);
	$pdf->Cell(10, 0, "à un supplément de 40 euros, conformément à l'article L441-6 du Code de commerce.", 0, 0, 'L');
} else if ($lang == "EN") {
	$delay = "45";
	$pdf->Cell(10, 0, "The payment is due upon receipt of this invoice. If payment is not receive within $delay days from the receipt of this invoice the amount due", 0, 0, 'L');
	$pdf->Ln(3);
	$pdf->Cell(10, 0, "will be subject to a penalty. The rate of the penalty will be the highest rate allowed under French laws for such purpose.", 0, 0, 'L');
	$pdf->Ln(3);
	$pdf->Cell(10, 0, "Furthermore, in case of late payment, professional clients will be subject to a surcharge of 40 euros, in accordance with", 0, 0, 'L');
	$pdf->Ln(3);
	$pdf->Cell(10, 0, "Article L441-6 of the Code of commerce.", 0, 0, 'L');
}
$pdf->Output($prefix . $id_facture . '.pdf', 'D');

fclose($fh);
?>
