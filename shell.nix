with import <nixpkgs> {};

mkShell {
    buildInputs = [
        python39
        python39Packages.poetry
        ripgrep
        jq
        datamash
        findutils
    ];
    shellHook = ''
        local  VIRTUAL_ENV_BIN=$(dirname $(poetry run which python))
        export VIRTUAL_ENV=$(dirname "$VIRTUAL_ENV_BIN")
        export POETRY_ACTIVE=1
        export PATH=$VIRTUAL_ENV_BIN:$PATH
    '';
}