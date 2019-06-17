<?php

function get_total($id_facture, $pdf, $file_log, $type, $frais_divers) {
	$ret['t_notva'] = 0;
	$ret['t_tva'] = 0;
	$ret['t_tva_ht'] = 0;
	$ret['total_ht'] = 0;
	$ret['tva'] = 0;
	$ret['total'] = 0;
	global $frais_divers_msg;
	global $lang;

	if ($type == "dil")
		$sql = "select * from lgc_invoiceitem where invoice_id=$id_facture order by id;";
	elseif($type == "deb")
		$sql = "select * from lgc_invoicedisbursement where invoice_id=$id_facture order by id;";

	$resultat = mysqli_query($GLOBALS['c'], $sql);

	if (! $resultat) {
		if ($pdf) {
			fwrite($file_log, "impossible de s&eacute;lectionner diligence: ligne=".__LINE__."\n");
			fwrite($file_log, "$sql\n");
			exit;
		} else {
			echo "impossible de s&eacute;lectionner diligence: ligne=".__LINE__."<br>";
			echo "$sql<br>";
		}
	} else {
		while ($row_op = mysqli_fetch_assoc($resultat)) {

			$prix_ht = $row_op['rate'];
			$marge = 0;
			if ($type == "deb" and $row_op['margin'])
				$marge = 0.2;

			$tva = $row_op['vat'] / 100;
			$ret['tva'] = $row_op['vat'];
			$prix_ttc = $prix_ht * ($tva + 1);
			if ($marge > 0)
				$prix_ttc = $prix_ttc * ($marge + 1);
			$prix_ht = $prix_ttc / ($tva + 1);

			if ($tva != 0) {
				$ret['t_tva'] += ($prix_ht * $row_op['quantity']) * $tva;
				$ret['total'] += ($prix_ht * $row_op['quantity']) * (1 + $tva);
				$ret['t_tva_ht'] += $prix_ht * $row_op['quantity'];
			} else {
				$ret['t_notva'] += $prix_ht * $row_op['quantity'];
				$ret['total'] += $prix_ht * $row_op['quantity'];
			}

			$ret['total_ht'] += $prix_ht * $row_op['quantity'];

			if ($pdf and $type == "dil") {
				$pdf->Cell(20, 4, '-', 0, 0, 'R');
				$pdf->MultiCell(0, 4, $row_op['description'], '','L');
				$pdf->Ln(1);
			} elseif ($pdf and $type == "deb") {
				$pdf->Cell(60);
				$Xabs = $pdf->GetX();
				$Yord = $pdf->GetY();

				$pdf->Cell(60);
				$prix_ht_all = $prix_ht * $row_op['quantity'];
				$pdf->Cell(30, 4, number_format($prix_ht_all, 2, ',', ' '), 0, 0, 'R');

				$pdf->SetX($Xabs, $Yord);
				$pdf->MultiCell(70, 4, $row_op['description'], '','L');

				$pdf->Ln(1);
			}
		}
		if ($pdf and $frais_divers['frais_divers'] > 0) {
			$pdf->Cell(60);
			$Xabs = $pdf->GetX();
			$Yord = $pdf->GetY();

			$pdf->Cell(60);
			$fd = $frais_divers['frais_divers'];

			$pdf->Cell(30, 4, number_format($fd, 2, ',', ' '), 0, 0, 'R');

			$pdf->SetX($Xabs, $Yord);
			$pdf->MultiCell(70, 4, utf8_decode($frais_divers_msg[$lang]), '','L');

			$pdf->Ln(1);
		}
	}
	return $ret;
}


function get_dil_total_pdf($id_facture, $pdf, $file_log) {
	return get_total($id_facture, $pdf, $file_log, "dil", 0);
}

function get_dil_total($id_facture) {
	return get_total($id_facture, 0, 0, "dil", 0);
}

function get_frais_divers($id_facture, $dil_total_ht, $file_log) {
	$frais_divers = 0;
	$frais_divers_tva = 0;
	$tva = 0;

	if ($dil_total_ht) {
		$sql = "select vat from lgc_invoiceitem where id=$id_facture limit 1;";
		$resultat_tmp = mysqli_query($GLOBALS['c'], $sql);
		if (! $resultat_tmp) {
			if ($file_log) {
				fwrite($file_log, "impossible de s&eacute;lectionner diligence: ligne=".__LINE__."\n");
				fwrite($file_log, "$sql\n");
			} else {
				echo "impossible de s&eacute;lectionner diligence: ligne=".__LINE__."\n";
				echo "$sql\n";
			}
			exit;
		} else {
			$row_op = mysqli_fetch_assoc($resultat_tmp);
			$tva = $row_op['vat'];

			$frais_divers = (__FRAIS_DIVERS_RATE__ * $dil_total_ht) / 100;
			if ($frais_divers > __FRAIS_DIVERS_LIMIT__)
				$frais_divers = __FRAIS_DIVERS_LIMIT__;
			if ($tva != 0)
				$frais_divers_tva = $frais_divers * ($tva / 100) + $frais_divers;
		}
	}
	$ret['frais_divers'] = $frais_divers;
	$ret['frais_divers_tva'] = $frais_divers_tva;
	$ret['tva'] = $tva;
	return $ret;
}

function get_deb_total_pdf($id_facture, $pdf, $file_log, $dil_total_ht) {
	$frais_divers = get_frais_divers($id_facture, $dil_total_ht, $file_log);

	$ret = get_total($id_facture, $pdf, $file_log, "deb", $frais_divers);
	if ($frais_divers['frais_divers_tva'] == 0) {
		$ret['t_notva'] += $frais_divers['frais_divers'];
		$ret['total'] += $frais_divers['frais_divers'];
	} else {
		$ret['t_tva'] += $frais_divers['frais_divers'] * ($frais_divers['tva'] / 100);
		$ret['t_tva_ht'] += $frais_divers['frais_divers'];
		$ret['total_ht'] += $frais_divers['frais_divers'];
		$ret['total'] += $frais_divers['frais_divers_tva'];
	}
	return $ret;
}

function get_deb_total($id_facture, $dil_total_ht) {
	$frais_divers = get_frais_divers($id_facture, $dil_total_ht, 0);

	$ret = get_total($id_facture, 0, 0, "deb", 0);
	$ret['total_hors_frais_divers_ht'] = $ret['total_ht'];

	$ret['frais_divers'] = $frais_divers;
	if ($frais_divers['frais_divers_tva'] == 0) {
		$ret['t_notva'] += $frais_divers['frais_divers'];
		$ret['total'] += $frais_divers['frais_divers'];
	} else {
		$ret['t_tva'] += $frais_divers['frais_divers'] * ($frais_divers['tva'] / 100);
		$ret['t_tva_ht'] += $frais_divers['frais_divers'];
		$ret['total_ht'] += $frais_divers['frais_divers'];
		$ret['total'] += $frais_divers['frais_divers_tva'];
	}
	return $ret;
}

?>