#!/bin/bash

for i in message_*.html; do
	echo $i
	f="${i%.*}"
	html2text $i | grep -v "<?xml " | sed 's/sur ce lien/sur ce lien: ${URL}/' | sed 's/on this link/on this link: ${URL}/'> ${f}.txt
done
