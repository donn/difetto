{
  inputs = {
    nix-eda.url = "github:fossi-foundation/nix-eda";
    nl2bench = {
      url = "github:donn/nl2bench";
      inputs.nix-eda.follows = "nix-eda";
    };
  };

  outputs = {
    self,
    nix-eda,
    nl2bench,
    ...
  }: let
    nixpkgs = nix-eda.inputs.nixpkgs;
    lib = nixpkgs.lib;
  in {
    overlays = {
      default = lib.composeManyExtensions [
      nl2bench.overlays.default
        (pkgs': pkgs: let
          callPackage = lib.callPackageWith pkgs';
        in {
          yosys-difetto = callPackage ./yosys-plugin/default.nix {};
        })
      ];
    };
    # Packages
    legacyPackages = nix-eda.forAllSystems (
      system:
        import nix-eda.inputs.nixpkgs {
          inherit system;
          overlays = [nix-eda.overlays.default self.overlays.default];
        }
    );

    packages = nix-eda.forAllSystems (
      system: let
        pkgs = self.legacyPackages."${system}";
      in {
        inherit (pkgs) yosys-difetto;
      }
    );

    # devshells

    devShells = nix-eda.forAllSystems (
      system: let
        pkgs = self.legacyPackages."${system}";
        callPackage = lib.callPackageWith pkgs;
      in {
      }
    );
  };
}
