.PHONY: build

build:
	docker build -t micro-infrastructure/adaptor-lofar-stage .

run: build
	docker run -dt --rm -P micro-infrastructure/adaptor-lofar-stage

push: build
	docker push micro-infrastructure/adaptor-lofar-stage

