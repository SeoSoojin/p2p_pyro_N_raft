SHELL := /bin/bash
server:
	@echo "Starting the server"
	python3 -u ./server.py

client:
	@echo "Starting the client"
	python3 -u ./client.py