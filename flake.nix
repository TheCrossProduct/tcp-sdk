{
  description = "TCP python SDK.";

  inputs = {
    utils.url = "github:numtide/flake-utils";
    machnix.url = "github:DavHau/mach-nix";
    nixpkgs.follows =   "machnix/nixpkgs";
  };

  outputs = { self, 
              nixpkgs, 
              utils, 
              machnix}: utils.lib.eachDefaultSystem (system: 
    let

      requirements = builtins.readFile ./requirements.txt;
      requirements-dev = builtins.readFile ./requirements.txt.dev;

      version = self.lastModifiedDate;

      nixpkgs_ = nixpkgs.legacyPackages.${system};

    in
    rec {
  

      packages = rec {

        module = machnix.lib.${system}.buildPythonPackage  
        {
          python="python3Full";
          pname = "tcp-sdk";
          src = ./.;
          inherit version;
          inherit requirements;
          doCheck = false;
          ignoreCollisions=true; 
          providers={notebook="nixpkgs";};
        };

        pyInterpreter = machnix.lib.${system}.mkPython
        {
          python="python3Full";
          inherit requirements;
          packagesExtra = [module];
          providers={notebook="nixpkgs";};
        };

        default = module;
      };

      apps = rec {
        default = {
          type="app";
          program="${self.packages.x86_64-linux.pyInterpreter}/bin/test.sh";
        };
      };

      devShells.default = machnix.lib.${system}.mkPythonShell {
        python="python3Full";
        requirements = requirements-dev+"\nipython"; 
        ignoreCollisions=true; 
        packagesExtra = [self.packages.${system}.module];
        providers={notebook="nixpkgs";};
      };
  
    });
}
