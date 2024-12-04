#%% Setup
from pylive.QtLiveApp import display


#%% Print to console, and Display text in the preview area
print("print this to the console")
display("Display this in the preview Area")


#%% Drag numbers with the mouse
print(f"drag the number to set its value {49}")


#%% Live update current cell
k=1
#%% execute changed cells only
print(f"""
try to modify thdsadasis text. Only the chagged cell will be executed!
""")
k+=1
display(k)