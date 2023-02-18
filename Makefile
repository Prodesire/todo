.PHONY: test clean run

run:
	uvicorn todo:app --reload

test:
	pytest -vv

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -r {} \+
	find . -type d -name ".pytest_cache" -exec rm -r {} \+
	find . -type f -name "*.db" -delete
	rm -f .coverage

help:
	@echo "Available commands:"
	@echo "  make test           Run tests"
	@echo "  make clean          Clean up cache files"
	@echo "  make run            Start the development server"
	@echo "  make help           Display this help message"
