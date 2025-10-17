script = """
import time
global time
def get_current_time():
	return time.time()
	
print( get_current_time() )
"""

def main():
	exec(script)
main()