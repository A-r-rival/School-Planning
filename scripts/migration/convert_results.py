# Read and print investigation results
with open('investigation_results.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Write to a simpler format file
with open('results_simple.txt', 'w', encoding='ascii', errors='replace') as f:
    f.write(content)

print("Converted to ASCII - results_simple.txt")
