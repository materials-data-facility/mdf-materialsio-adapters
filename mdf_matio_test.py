from materials_io.utils.interface import run_all_parsers_on_group
import mdf_matio

group = ['/Users/tylerskluzacek/Desktop/matio-data/INCAR', '/Users/tylerskluzacek/Desktop/matio-data/OUTCAR', '/Users/tylerskluzacek/Desktop/matio-data/POSCAR']

x = run_all_parsers_on_group(group=group, include_parsers=['dft'], adapter_map='match')

for item in x:
    print(item)
