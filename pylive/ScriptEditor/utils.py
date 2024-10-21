def get_line_at_offset(text, offset):
	if offset > len(text):
		raise IndexError(f"Offset {offset} is greater than text length {len(text)}")
	
	line_start = text.rfind('\n', 0, offset) + 1  # Add 1 to move past the newline
	line_end = text.find('\n', offset)
	
	if line_end == -1:  # If no newline is found, go to the end of the text
		line_end = len(text)
	
	# Return the line containing the offset
	return text[line_start:line_end]