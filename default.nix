{
  src ? ./.,
  buildPythonPackage,
  librelane,
  poetry-core,
  setuptools,
  quaigh,
  nl2bench,
  cocotb,
  bitarray,
  marshmallow-dataclass,
  yosys-difetto,
}: let
  self = buildPythonPackage {
    pname = "librelane_plugin_difetto";
    version = (builtins.fromTOML (builtins.readFile ./pyproject.toml)).project.version;

    inherit src;

    doCheck = false;

    format = "pyproject";

    nativeBuildInputs = [
      poetry-core
      setuptools
    ];

    includedTools = [
      quaigh
      nl2bench
    ];

    addedYosysPlugins = [
      yosys-difetto
    ];

    dependencies = [
      cocotb
      bitarray
      marshmallow-dataclass
      librelane
    ];
  };
in
  self
