def get_differences(file_a, file_b):
    with open(file_a, 'r') as file:
        a = file.readlines()
        a = [line.strip() for line in a]
    with open(file_b, 'r') as file:
        b = file.readlines()
        b = [line.strip() for line in b]
    return {i: (a[i], b[i]) for i in range(len(a)) if a[i] != b[i]}


file_a = 'base_model/new_output.csv'
file_b = 'base_model/ensemble_output.csv'
differences = get_differences(file_a, file_b)
for i, (line_a, line_b) in differences.items():
    guess_a = line_a.split(',')[1]
    guess_b = line_b.split(',')[1]
    print(f'Line {i}: {guess_a} vs {guess_b}')