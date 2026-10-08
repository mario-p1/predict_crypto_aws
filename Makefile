.PHONY:
base_lambda:
	rm -f build/requirements.txt
	rm -rf build/packages
	rm -f build/base_lambda.zip

	uv export --frozen --no-dev --no-editable -o build/requirements.txt
	uv pip install \
		--no-installer-metadata \
		--no-compile-bytecode \
		--python-platform x86_64-manylinux_2_34 \
		--python 3.14 \
		--target build/packages \
		--only-binary :all: \
		-r build/requirements.txt
	cd build/packages && zip -r ../base_lambda.zip .

.PHONY:
lambda_build:
	cp build/base_lambda.zip build/fetch_data_function.zip
	cp src/crypto_mlops/fetch_data_function.py build/
	cd build && zip -u fetch_data_function.zip fetch_data_function.py

.PHONY:
deploy_lambda: lambda_build
	aws s3 cp build/fetch_data_function.zip s3://$(CODE_BUCKET)/fetch_data_function.zip
	aws lambda update-function-code --function-name $(FETCH_DATA_FUNCTION_NAME) --s3-bucket $(CODE_BUCKET) --s3-key fetch_data_function.zip