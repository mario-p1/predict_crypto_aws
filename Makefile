-include .env
export

SRC := $(shell find src -name '*.py')
.DELETE_ON_ERROR:

.PHONY: all
all: build/lambda.zip

build/lambda_base.zip: uv.lock
	rm -rf build/lambda_base build/lambda_base.zip
	mkdir -p build
	uv export \
		--frozen \
		--no-dev \
		--no-emit-project \
		-o build/requirements.txt
	uv pip install \
		--no-installer-metadata \
		--no-compile-bytecode \
		--python-platform x86_64-manylinux_2_34 \
		--python 3.14 \
		--target build/lambda_base \
		--only-binary :all: \
		-r build/requirements.txt
	cd build/lambda_base && zip -qr ../lambda_base.zip .

build/lambda.zip: build/lambda_base.zip $(SRC)
	cp build/lambda_base.zip build/lambda.zip
	cd src && zip -qr ../build/lambda.zip crypto_mlops -x '*__pycache__*'

.PHONY: deploy
deploy: build/lambda.zip
	aws s3 cp \
		build/lambda.zip \
		s3://$(CODE_BUCKET)/fetch_data_function.zip
	aws lambda update-function-code \
		--function-name $(FETCH_DATA_FUNCTION_NAME) \
		--s3-bucket $(CODE_BUCKET) \
		--s3-key fetch_data_function.zip

.PHONY: clean
clean:
	rm -rf build

.PHONY: format
format:
	uv run ruff check --fix .
	uv run ruff format .