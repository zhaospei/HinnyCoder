# Define two sets
set_a = {1, 2, 3, 4, 5}
set_b = {4, 5, 6, 7, 8}

# Elements in set A but not in set B
missing_in_b = set_a - set_b
print("Elements in set A that are not in set B:", missing_in_b)

# Elements in set B but not in set A
missing_in_a = set_b - set_a
print("Elements in set B that are not in set A:", missing_in_a)