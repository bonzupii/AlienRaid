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
          # Everything comes from the nix store: python3 with pygame compiled
          # against the nix SDL2 stack (SDL2, SDL2_image, SDL2_ttf, SDL2_mixer,
          # libGL). No venv, no uv, no pip, nothing touches the host system.
          # `python` inside this shell already has pygame importable.
          default = pkgs.mkShell {
            packages = with pkgs; [
              (python3.withPackages (ps: [ ps.pygame ]))
              SDL2
              SDL2_image
              SDL2_ttf
              SDL2_mixer
              libGL
            ];

            shellHook = ''
              echo ""
              echo "AlienRaid dev shell ready."
              echo "Run the game with:  python launcher.py"
            '';
          };
        });
    };
}
