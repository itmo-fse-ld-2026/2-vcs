filepath=report/
filename=main

generate:
	docker run --rm -it -v .:/project --user $(id -u):$(id -g) test python src/main.py
clean:
	# clean LaTeX artifacts
	@for file_ext in "*.pdf" "*.aux" "*.log" "*.toc" "*.out" "*.bbl" "*.blg" "*.bcf" "*.run.xml"; do \
		find $(filepath) -name "$${file_ext}" -delete; \
	done
	# clean project artifacts
	rm -rf $$(grep "git_dir:" config.yaml | cut -d '"' -f 2)
	rm -rf $$(grep "svn_dir:" config.yaml | cut -d '"' -f 2)
	rm -rf $$(grep "git_log:" config.yaml | cut -d '"' -f 2)
	rm -rf $$(grep "svn_log:" config.yaml | cut -d '"' -f 2)
pdf:
	cd "${filepath}"; \
	xelatex "${filename}"; \
	xelatex "${filename}"