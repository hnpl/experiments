import sys

def get_n_elements_array(start, end, step_size, element_size): # start, end, step_size are specified in terms of bytes
                                                               # element_size is the number of bytes per element
                                                               # so, the output is an array of number of elements per experiment
    sizes = list(range(start, end+1, step_size))
    for i in range(len(sizes)):
        sizes[i] //= element_size
    return sizes

if __name__ == "__main__":
    output_file = sys.argv[1]
    sizes = get_n_elements_array(2**16, 2**26, 2**16, 8) # [64KiB, 64MiB], step = 64 KiB
    with open(output_file, "w") as f:
        for size in sizes:
            f.write(f"{size} ")

