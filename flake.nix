{
  description = "TCP python SDK.";

  inputs = {
     poetry2nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, 
              nixpkgs, 
              utils, 
              poetry2nix}: utils.lib.eachDefaultSystem (system: 
    let

      version = self.lastModifiedDate;
      nixpkgs_ = nixpkgs.legacyPackages.${system};
      inherit (poetry2nix.lib.mkPoetry2Nix { pkgs = nixpkgs_; }) mkPoetryEnv;
      inherit (poetry2nix.lib.mkPoetry2Nix { pkgs = nixpkgs_; }) mkPoetryApplication;
      inherit (poetry2nix.lib.mkPoetry2Nix { pkgs = nixpkgs_; }) defaultPoetryOverrides;


    in
    rec {

      packages = rec {
        
        app = mkPoetryApplication { 
            projectDir = ./.; 
        };

        py_interpreter = mkPoetryEnv
        {
          projectDir = self;
          extras = ["ipython"];
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
              ${py_interpreter}/bin/python -m unittest discover -s ${test_files}
            '';

        default = app;
      };

      devShells.default = nixpkgs_.mkShell {
          buildInputs = [self.packages.${system}.py_interpreter]; 
      };
  
    });
}
