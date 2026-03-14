{
  inputs = {
    librelane.url = "github:librelane/librelane/dev";
    nl2bench = {
      url = "github:donn/nl2bench/nixos_25.11";
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
            nativeBuildInputs = attrs.nativeBuildInputs ++ [ pypkgs.pythonRelaxDepsHook ];
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
        default = pkgs.librelane-shell.override({
          extra-packages = with pkgs; [quaigh python3.pkgs.nl2bench];
          librelane-extra-python-interpreter-packages = ps: with ps; [bitarray marshmallow-dataclass];
          librelane-plugins = ps: with ps; [librelane-plugin-difetto];
        });
      }
    );
  };
}
