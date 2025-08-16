{
  inputs = {
    librelane.url = "github:librelane/librelane/donn/yosys_plugin_tweaks";
    nl2bench = {
      url = "github:donn/nl2bench";
      inputs.nix-eda.follows = "librelane/nix-eda";
      inputs.libparse.follows = "librelane/libparse";
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
            patches = attrs.patches ++ [
              ./nix/openroad/dft_npe.patch
              ./nix/openroad/dft_save_clk.patch
            ];
          });
          yosys-difetto = callPackage ./yosys-plugin/default.nix {
            src = "${self}/yosys-plugin";
          };
        })
        (nix-eda.composePythonOverlay (pkgs': pkgs: pypkgs': pypkgs: let
          callPythonPackage = lib.callPackageWith (pkgs' // pypkgs');
        in {
          cocotb = pypkgs.cocotb.overridePythonAttrs({
            doCheck = false;
            meta.broken = false;
          });
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
        callPackage = lib.callPackageWith pkgs;
      in {
        default = callPackage (librelane.createOpenLaneShell {
          extra-packages = [ pkgs.quaigh pkgs.python3.pkgs.nl2bench ];
          extra-python-packages = [ pkgs.python3.pkgs.cocotb ];
          librelane-extra-yosys-plugins = [pkgs.yosys-difetto];
        }) {};
      }
    );
  };
}
