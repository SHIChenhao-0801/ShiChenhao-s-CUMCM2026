from pathlib import Path
import shutil
import hashlib
import json
ROOT=Path(__file__).resolve().parents[3]
QA=ROOT/'paper_output/qa/support_completion_20260913/vs'
QA.mkdir(parents=True,exist_ok=True)
src=ROOT/'支撑材料/05_数值检验与实验/Python检验源码'
dst=QA/'source'
assert not dst.exists()
shutil.copytree(src,dst)
venv=ROOT/'tmp/cache/support_completion_verification_venv'
assert (venv/'Scripts/python.exe').is_file()
project=dst/'VerificationReview.pyproj'
project.write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<Project DefaultTargets="Build" xmlns="http://schemas.microsoft.com/developer/msbuild/2003" ToolsVersion="4.0">
<PropertyGroup>
<Configuration Condition="'$(Configuration)' == ''">Debug</Configuration>
<ProjectGuid>{{B35A6409-0D0C-47D6-A90A-51A1A3646627}}</ProjectGuid>
<SchemaVersion>2.0</SchemaVersion><ProjectHome>.</ProjectHome><StartupFile>run_checks.py</StartupFile>
<WorkingDirectory>.</WorkingDirectory><OutputPath>.</OutputPath><Name>VerificationReview</Name>
<RootNamespace>VerificationReview</RootNamespace><LaunchProvider>Standard Python launcher</LaunchProvider>
<CommandLineArguments>--check method --quick --output-dir "{QA/'method_gui_run'}"</CommandLineArguments>
<InterpreterArguments>-X utf8 -B</InterpreterArguments><EnableNativeCodeDebugging>False</EnableNativeCodeDebugging>
<InterpreterId>MSBuild|$(MSBuildProjectFullPath)|VerificationEnv</InterpreterId>
</PropertyGroup>
<ItemGroup><Compile Include="run_checks.py"/><Compile Include="paper_output/code/verification/method_comparison.py"/>
<Interpreter Include="{venv}"><Id>VerificationEnv</Id><Version>3.14</Version><Description>Verified Python 3.14.7</Description><InterpreterPath>Scripts\\python.exe</InterpreterPath><WindowsInterpreterPath>Scripts\\pythonw.exe</WindowsInterpreterPath><PathEnvironmentVariable>PYTHONPATH</PathEnvironmentVariable><Architecture>x64</Architecture></Interpreter>
</ItemGroup>
<Import Project="$(MSBuildExtensionsPath32)\\Microsoft\\VisualStudio\\v$(VisualStudioVersion)\\Python Tools\\Microsoft.PythonTools.targets" />
</Project>''',encoding='utf-8')
(dst/'VerificationReview.sln').write_text('''Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 18
VisualStudioVersion = 18.10.12201.205
MinimumVisualStudioVersion = 10.0.40219.1
Project("{888888A0-9F3D-457C-B088-3A5042F75D52}") = "VerificationReview", "VerificationReview.pyproj", "{B35A6409-0D0C-47D6-A90A-51A1A3646627}"
EndProject
Global
 GlobalSection(SolutionConfigurationPlatforms) = preSolution
  Debug|Any CPU = Debug|Any CPU
 EndGlobalSection
 GlobalSection(ProjectConfigurationPlatforms) = postSolution
  {B35A6409-0D0C-47D6-A90A-51A1A3646627}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
 EndGlobalSection
EndGlobal
''',encoding='utf-8')
rows=[]
for p in src.rglob('*'):
    if p.is_file():
        target=dst/p.relative_to(src)
        assert p.read_bytes()==target.read_bytes()
        rows.append({'path':p.relative_to(src).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(QA/'source_snapshot.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(project)
