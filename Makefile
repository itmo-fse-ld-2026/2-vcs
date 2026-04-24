report_dir=report/
report_name=main

config_name=config.yaml

generate:
	python src/main.py
clean:
	# clean LaTeX artifacts
	@for file_ext in "*.pdf" "*.aux" "*.log" "*.toc" "*.out" "*.bbl" "*.blg" "*.bcf" "*.run.xml"; do \
		find $(report_dir) -name "$${file_ext}" -delete; \
	done
	# clean project artifacts
	rm -rf $$(grep "output_dir:" ${config_name} | cut -d '"' -f 2)
pdf:
	cd "${report_dir}"; \
	xelatex --shell-escape -interaction=nonstopmode "${report_name}"; \
	xelatex --shell-escape -interaction=nonstopmode "${report_name}"