filepath=report/
filename=main

clean:
	for file_ext in "*.pdf" "*.aux" "*.log" "*.toc" "*.out" "*.bbl" "*.blg" "*.bcf" "*.run.xml"; do \
		find $(filepath) -name "$${file_ext}" -delete; \
	done
pdf:
	cd "${filepath}"; \
	xelatex "${filename}"; \
	biber "${filename}"; \
	xelatex "${filename}"