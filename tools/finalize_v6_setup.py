"""One-time, explicit source cleanup and Visual Studio launch configuration."""
from pathlib import Path
import ast
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
assert Path.cwd().resolve() == root
path = root/'paper_output/code/modeling/verify_convergence.py'
source = path.read_text(encoding='utf-8')
first = source.index('        with warnings.catch_warnings')
last = source.index('        gc.collect()', first)
body = source[first:last].replace('        run.close()\n','').replace('        del run\n','')
source = (source[:first]+'        run = None\n        try:\n'+
          ''.join('    '+line if line.strip() else line for line in body.splitlines(keepends=True))+
          '        finally:\n            if run is not None:\n                run.close()\n        del run\n'+source[last:])
ast.parse(source)
path.write_text(source, encoding='utf-8')
path = root/'paper_output/code/modeling/A_Drying.pyproj'
source = path.read_text(encoding='utf-8')
source = source.replace('<StartupFile>run_experiments.py</StartupFile>',
                        '<StartupFile>run_modeling.py</StartupFile>')
source = source.replace('<ScriptArguments>--batch baseline --n 100 --tag _vs</ScriptArguments>',
    '<ScriptArguments>--review --version gui_final_v6a --n1 3200 --n23 3200 --n4 6400 --blas-threads 1</ScriptArguments>')
modules = ['run_modeling.py','production_provenance.py','disk_dense.py','analytic_jacobian.py',
           'export_outputs.py','publication_plots.py','q1_model.py','q2_model.py','q3_model.py',
           'q4_model.py','verify_convergence.py','verify_dense_storage.py']
needle = '    <Compile Include="run_experiments.py" />'
source = source.replace(needle, needle+'\n'+''.join('    <Compile Include="'+name+'" />\n' for name in modules))
ET.fromstring(source)
path.write_text(source, encoding='utf-8')
print('Convergence finally-close and Visual Studio single-process review configuration saved')
