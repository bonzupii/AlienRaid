{
  description = "AlienRaid - a pygame roguelike. Hermetic dev environment (nixpkgs 26.05).";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      devShells = forAllSystems (system:
        let pkgs = nixpkgs.legacyPackages.${system}; in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              python3
              uv
              SDL2
              SDL2_image
              SDL2_ttf
              libGL
            ];

            # Create a local .venv with all project dependencies. No global
            # installs, nothing touches the host system.
            shellHook = ''
              if [ -f pyproject.toml ]; then
                uv sync
              fi
              echo ""
              echo "AlienRaid dev shell ready."
              echo "Run the game with:  .venv/bin/python launcher.py"
            '';
          };
        });
    };
}
