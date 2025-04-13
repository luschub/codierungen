name: R-Analyse

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  r-job:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: R installieren
      uses: r-lib/actions/setup-r@v2
      with:
        r-version: '4.2.0'
    
    - name: R-Skript ausführen
      run: Rscript r-script.R
    
    - name: Ergebnisse speichern
      uses: actions/upload-artifact@v3
      with:
        name: Analyse-Ergebnisse
        path: ergebnisse.csv