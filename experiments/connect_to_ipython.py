from jupyter_client import BlockingKernelClient

"""
1 start jupyter console
python -m console

2 run the folowing in the jupyter console
from jupyter_client import find_connection_file
print(find_connection_file())
"""

# Path to the connection file
connection_file = 'C:\\Users\\andris\\AppData\\Roaming\\jupyter\\runtime\\kernel-23724.json'


# Create and configure the Kernel Client
client = BlockingKernelClient(connection_file=connection_file)
client.load_connection_file()
client.start_channels()

# # Message to send to the console
# message_to_display = "print('Hello from the script!')"

# # Send the message to the kernel for display in qtconsole
# client.execute(message_to_display, store_history=True)

# Code to execute and display
code_to_execute = """
x = 10
y = 20
print(f"The sum is: {x + y}")
x
"""

client.execute_interactive(code_to_execute)

# Fetch and print all output from the kernel
try:
    while True:
        msg = client.get_iopub_msg(timeout=2)  # Timeout to avoid infinite loops
        msg_type = msg['header']['msg_type']

        if msg_type in ('stream', 'execute_result', 'display_data'):
            print(msg['content'].get('text', ''))

        if msg_type == 'error':
            print("Error:", ''.join(msg['content']['traceback']))

        # Exit after the execution completes
        if msg_type == 'status' and msg['content']['execution_state'] == 'idle':
            break
except Exception as e:
    print(f"Error fetching message: {e}")

# Stop the client when done
client.stop_channels()
