{
  description = "TCP python SDK.";

  inputs = {
    treefmt-nix.url = "github:numtide/treefmt-nix";

    poetry2nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = {
    self,
    nixpkgs,
    utils,
    poetry2nix,
    treefmt-nix,
  }:
    utils.lib.eachDefaultSystem (system: let
      version = self.lastModifiedDate;
      nixpkgs_ = nixpkgs.legacyPackages.${system};
      poetry = poetry2nix.lib.mkPoetry2Nix {pkgs = nixpkgs_;};
      inherit (poetry) mkPoetryEnv;
      inherit (poetry) mkPoetryApplication;

      pypkgs-build-requirements = {
        scaleway = ["poetry"];
        scaleway-core = ["poetry"];
      };
      overrides = poetry.defaultPoetryOverrides.extend (
        self: super:
          builtins.mapAttrs
          (
            package: build-requirements:
              (builtins.getAttr package super).overridePythonAttrs (old: {
                buildInputs =
                  (old.buildInputs or [])
                  ++ (builtins.map (pkg:
                    if builtins.isString pkg
                    then builtins.getAttr pkg super
                    else pkg)
                  build-requirements);
              })
          )
          pypkgs-build-requirements
      );

      fmtConfig = {
        projectRootFile = "flake.nix";
        programs.black.enable = true;
        programs.alejandra.enable = true;
      };

      treefmtEval = treefmt-nix.lib.evalModule nixpkgs_ fmtConfig;
    in rec {
      formatter = treefmtEval.config.build.wrapper;
      checks = {formatting = treefmtEval.config.build.check self;};

      packages = rec {
        app = mkPoetryApplication {
          projectDir = ./.;
          inherit overrides;
          extras = [];
        };

        py_env =
          mkPoetryEnv
          {
            projectDir = self;
            extras = ["ipython"];
            groups = ["build"];
          };

        test_files = nixpkgs_.stdenv.mkDerivation {
          name = "tests_sdk_files";
          src = ./tests;
          installPhase = ''
            mkdir $out
            cp -v $src/* $out
          '';
        };

        tests = nixpkgs_.writeShellScript "tests_sdk.sh" ''
          set source
          ${py_env}/bin/python -m unittest discover -s ${test_files}
        '';

        default = app;
      };

      devShells.default = nixpkgs_.mkShell {
        buildInputs = [self.packages.${system}.py_env];
      };
    });
}
