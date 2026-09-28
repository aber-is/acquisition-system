{
  description = "Opportunity acquisition system for Aber Industrial Solutions Ltd";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in {
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python313.withPackages (ps: [
            ps.pydantic
            ps.pytest
            ps.pyyaml
          ]);
        in {
          default = pkgs.mkShell {
            packages = [ python pkgs.ruff ];
            shellHook = ''
              export PYTHONPATH="$PWD/src''${PYTHONPATH:+:$PYTHONPATH}"
            '';
          };
        });
    };
}
