from pathlib import Path

def read_file(path):
	return Path(path).read_text()

def process_text(text:str):
	return "\n".join( [f"|{line}" for line in text.split("\n")] )
		
if __name__ == "__main__":
	file_path = "C:/dev/src/pylive/TODOs.md"
	text = read_file(file_path)
	processed_text = process_text(text)
	print(processed_text)