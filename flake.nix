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
        let
          pkgs = nixpkgs.legacyPackages.${system};
          # nixpkgs builds pygame from source, so we can compile it with AVX2
          # SIMD on x86_64. Without this, pygame's runtime AVX2 detection
          # warns that the CPU supports it but the build doesn't, and the
          # fast blitters stay compiled out (the warning means real blit
          # performance is left on the table).
          #
          # pygame 2.6.1's AVX2 build path has an upstream bug: its
          # CCompiler.spawn monkeypatch calls distutils.ccompiler.spawn,
          # which no longer exists on Python 3.13 / setuptools 80, so the
          # build crashes. pygame already saves the original method as
          # CCompiler.__spawn right before replacing it — delegate to that
          # instead. (Mirrors upstream's later fix.)
          pygame =
            if system == "x86_64-linux" then
              pkgs.python3Packages.pygame.overridePythonAttrs (old: {
                preConfigure = (old.preConfigure or "") + ''
                  export PYGAME_DETECT_AVX2=1
                '';
                postPatch = (old.postPatch or "") + ''
                  substituteInPlace setup.py --replace-fail \
                    "distutils.ccompiler.spawn(cmd, dry_run=self.dry_run, **kwargs)" \
                    "self.__spawn(cmd, **kwargs)"
                '';
              })
            else
              pkgs.python3Packages.pygame;
        in
        {
          # Everything comes from the nix store: python3 with pygame compiled
          # against the nix SDL2 stack (SDL2, SDL2_image, SDL2_ttf, SDL2_mixer,
          # libGL). No venv, no uv, no pip, nothing touches the host system.
          # `python` inside this shell already has pygame importable.
          default = pkgs.mkShell {
            packages = with pkgs; [
              (python3.withPackages (ps: [ pygame ]))
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
