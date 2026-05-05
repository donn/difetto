{
  inputs = {
    librelane.url = "github:librelane/librelane";
    nl2bench = {
      url = "github:donn/nl2bench";
      inputs.nix-eda.follows = "librelane/nix-eda";
    };
  };

  outputs = {
    self,
    librelane,
    nl2bench,
    ...
  }: let
    nix-eda = librelane.inputs.nix-eda;
    nixpkgs = nix-eda.inputs.nixpkgs;
    lib = nixpkgs.lib;
  in {
    overlays = {
      default = lib.composeManyExtensions [
        nl2bench.overlays.default
        (pkgs': pkgs: let
          callPackage = lib.callPackageWith pkgs';
        in {
          openroad = pkgs.openroad.overrideAttrs(attrs': attrs: {
            patches = [./nix/ord-scan_opt.patch];
          });
          yosys-difetto = callPackage ./yosys-plugin/default.nix {
            src = "${self}/yosys-plugin";
          };
        })
        (nix-eda.composePythonOverlay (pkgs': pkgs: pypkgs': pypkgs: let
          callPythonPackage = lib.callPackageWith (pkgs' // pypkgs');
        in {
          librelane-plugin-difetto = callPythonPackage ./default.nix {
            src = self;
          };
          nl2bench = pypkgs.nl2bench.overridePythonAttrs (attrs: {
            # i die of old age every time i wait for openjdk just to run antlr
            format = "wheel";
            src = pkgs'.fetchPypi {
              pname = "nl2bench";
              inherit (attrs) version;
              format = "wheel";
              dist = "py3";
              python = "py3";
              sha256 = "sha256-bgYpW3e8qQKiyci6Z8eIHsKiz/de951t4fL31Y574wI=";
            };
            doCheck = false;
            preBuild = "";
            nativeBuildInputs = with pypkgs'; [ poetry-core pythonRelaxDepsHook ];
            pythonRelaxDeps = [ "pyosys" ];
          });
          cocotb = pypkgs.cocotb.overridePythonAttrs {
            doCheck = false;
            meta.broken = false;
          };
        }))
      ];
    };

    legacyPackages = nix-eda.forAllSystems (
      system:
        import nix-eda.inputs.nixpkgs {
          inherit system;
          overlays = [nix-eda.overlays.default librelane.inputs.devshell.overlays.default librelane.overlays.default self.overlays.default];
        }
    );

    packages = nix-eda.forAllSystems (
      system: let
        pkgs = self.legacyPackages."${system}";
      in {
        inherit (pkgs) yosys-difetto;
      }
    );

    devShells = nix-eda.forAllSystems (
      system: let
        pkgs = self.legacyPackages."${system}";
      in {
        default = (pkgs.librelane-shell.override({
          extra-packages = with pkgs; [quaigh python3.pkgs.nl2bench qt5.qtbase qt5.qtcharts];
          extra-python-packages = ps: with ps; [
            # for testing/benchmarking
            xlsxwriter
          ];
          librelane-extra-python-interpreter-packages = ps: with ps; [bitarray marshmallow-dataclass
            # for testing/benchmarking
            matplotlib
            pyqt6
          ];
          librelane-plugins = ps: with ps; [librelane-plugin-difetto];
        })).overrideDerivation (old: {
          shellHook = (old.shellHook or "") + ''
            export PDK_ROOT=''${PDK_ROOT:-$HOME/.volare}
            export PATH=$PWD/build/with_venv:$PATH
          '';
        });
      }
    );
  };
}
