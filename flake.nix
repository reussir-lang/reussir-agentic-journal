{
  description = "Reussir agentic journal: a Forester forest of design notes, decisions, changelog entries and open problems";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    flake-utils.url = "github:numtide/flake-utils";

    # Forester 6.0 bundles its theme, so the forest needs no theme submodule.
    # Forester is not in nixpkgs; its flake builds it with opam-nix against
    # its own nixpkgs pin, which is kept so that the compiler comes from the
    # NixOS binary cache.
    forester.url = "sourcehut:~jonsterling/ocaml-forester/6.0";
  };

  outputs = { self, nixpkgs, flake-utils, forester }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        lib = pkgs.lib;

        # The glibc build. The flake's default package is a static musl
        # build that compiles its own OCaml and runs the compiler test suite,
        # which is slow and does not pass in every sandbox.
        foresterPkg = forester.legacyPackages.${system}.forester;

        # Sources that determine the rendered site.
        forestSrc = lib.fileset.toSource {
          root = ./.;
          fileset = lib.fileset.unions [
            ./forest.toml
            ./trees
            ./assets
          ];
        };

        # The rendered forest. Links are absolute, so the tree below $out
        # mirrors the path component of `url` in forest.toml.
        site = pkgs.stdenvNoCC.mkDerivation {
          name = "reussir-agentic-journal-site";
          src = forestSrc;
          nativeBuildInputs = [ foresterPkg ];
          buildPhase = ''
            runHook preBuild
            forester build forest.toml 2>&1 | tee build.log
            if grep -qiE '(error|warning)' build.log; then
              echo "forester reported diagnostics; failing the build" >&2
              exit 1
            fi
            runHook postBuild
          '';
          installPhase = ''
            runHook preInstall
            cp -r output $out
            runHook postInstall
          '';
        };

        # Forester copies its bundled theme out of the Nix store and keeps the
        # store's read-only permissions, so a second build cannot overwrite
        # the first. Make a previous output writable before building.
        thaw = ''
          if [ -d output ]; then chmod -R u+w output; fi
        '';

        mkApp = drv: {
          type = "app";
          program = lib.getExe drv;
        };

        build = pkgs.writeShellApplication {
          name = "journal-build";
          runtimeInputs = [ foresterPkg ];
          text = thaw + ''
            exec forester build forest.toml "$@"
          '';
        };

        serve = pkgs.writeShellApplication {
          name = "journal-serve";
          runtimeInputs = [ foresterPkg pkgs.python3 ];
          text = thaw + ''
            forester build forest.toml
            port="''${1:-1313}"
            echo "serving on http://localhost:$port/reussir-agentic-journal/"
            exec python3 -m http.server "$port" -d output
          '';
        };

        # journal-new <kind>: allocate a fresh random address for a tree of
        # the given kind and print the path of the new file.
        new = pkgs.writeShellApplication {
          name = "journal-new";
          runtimeInputs = [ foresterPkg ];
          text = ''
            kind="''${1:-}"
            case "$kind" in
              design)     prefix="design"; dir="design" ;;
              decision)   prefix="dec"; dir="decision" ;;
              problem)    prefix="prob"; dir="problem" ;;
              log)        prefix="log"; dir="log" ;;
              example)    prefix="ex"; dir="example" ;;
              motivation) prefix="mot"; dir="motivation" ;;
              insight)    prefix="ins"; dir="insight" ;;
              session)    prefix="ses"; dir="session" ;;
              *)
                echo "usage: journal-new <design|decision|problem|log|example|motivation|insight|session>" >&2
                exit 2
                ;;
            esac
            mkdir -p "trees/$dir"
            exec forester new forest.toml --random --prefix "$prefix" --dest "trees/$dir"
          '';
        };
      in
      {
        packages = {
          inherit site;
          default = site;
          forester = foresterPkg;
        };

        checks.site = site;

        apps = {
          build = mkApp build;
          serve = mkApp serve;
          new = mkApp new;
        };

        devShells.default = pkgs.mkShell {
          name = "reussir-journal";
          packages = [
            foresterPkg
            pkgs.jujutsu
            pkgs.git
            pkgs.python3
            pkgs.ripgrep
            build
            serve
            new
          ];
        };
      });
}
