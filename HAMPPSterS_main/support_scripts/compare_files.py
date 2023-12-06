import difflib

def compare_files(file1_path, file2_path):
    with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
        lines1 = file1.readlines()
        lines2 = file2.readlines()

    diff = difflib.unified_diff(lines1, lines2, fromfile=file1_path, tofile=file2_path, lineterm='')
    diff_text = '\n'.join(diff)
    return diff_text

# Usage example
file1_path = "job_M1.sh"
file2_path = "job.sh"
diff_result = compare_files(file1_path, file2_path)

print(diff_result)
