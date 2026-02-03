# Read the investigation file and print it cleanly
with open('duplication_investigation.txt', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Print each line
for line in content.split('\n'):
    print(line)
