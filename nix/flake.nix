{
  description = "QuantumLeap dev tools.";

  inputs = {
    nixpkgs.url = "github:NixOs/nixpkgs/nixos-23.05";
    nixie = {
      url = "github:c0c0n3/nixie";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, nixie }:
    let
      buildWith = nixie.lib.flakes.mkOutputSetForCoreSystems nixpkgs;
      mkSysOutput = { system, sysPkgs }:
      {
        defaultPackage.${system} = with sysPkgs;
        let
          pyenv = python38.withPackages (ps: with ps;
            [ pipenv pip wheel setuptools ]
          );
        in buildEnv {
          name = "quantumleap-shell";
          paths = [ pyenv ];
        };
      };
    in
      buildWith mkSysOutput;
}
