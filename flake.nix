{
  description = "Testing all TCP APIS.";

  inputs = {
    utils.url = "github:numtide/flake-utils";
    machnix.url = "github:DavHau/mach-nix";

#    tcp_api_utils.url = "git+ssh://git@github.com/TheCrossProduct/tcp-api-utils.git?ref=main";
    tcp_api_utils.url = "path:/home/chabardt/src/stab/tcp-api-utils";
    tcp.follows =       "tcp_api_utils/tcp"; 
#    tcp.url = "path:/home/chabardt/src/tcp";
    nixpkgs.follows =   "tcp_api_utils/nixpkgs";
  };

  outputs = { self, 
              nixpkgs, 
              utils, 
              machnix, 
              tcp, 
              tcp_api_utils}: utils.lib.eachDefaultSystem (system: 
    let

      requirements = builtins.readFile ./requirements.txt;
      version = builtins.substring 0 8 self.lastModifiedDate;

      nixpkgs_ = nixpkgs.legacyPackages.${system};
      tcp_ = {lib = tcp.lib.${system}; env = tcp.env.${system};}; 

      tcp_api_utils_ = tcp_api_utils.packages.${system}.default;

      packagesExtra = [ tcp_api_utils_ ];

    in
    rec {
  

      packages = rec {

        module = machnix.lib.${system}.buildPythonPackage  
        {
          python="python3Full";
          pname = "tcp-api-testing";
          src = ./.;
          inherit version;
          inherit requirements;
          doCheck = false;
          ignoreCollisions = true;
          packagesExtra = packagesExtra; 
        };

        pyInterpreter = machnix.lib.${system}.mkPython
        {
          python="python3Full";
          inherit requirements;
          packagesExtra = packagesExtra ++ [module];
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
        requirements = requirements+"\nipython"; 
        ignoreCollisions=true; 
        packagesExtra = packagesExtra ++ [self.packages.${system}.module];
      };
  
    });
}
