```r
# Einfaches R-Skript für GitHub Actions

# Print Informationen zur R-Version
print("R-Version Information:")
print(R.version)

# Erstelle einen einfachen Datensatz
daten <- data.frame(
  x = 1:10,
  y = rnorm(10, mean = 5, sd = 1.5)
)

# Berechne einige Statistiken
print("Deskriptive Statistik:")
print(summary(daten))

# Erstelle ein einfaches lineares Modell
modell <- lm(y ~ x, data = daten)
print("Lineares Modell Zusammenfassung:")
print(summary(modell))

# Erzeuge eine Ausgabedatei mit den Ergebnissen
ergebnisse <- data.frame(
  x_wert = seq(1, 10, 0.5),
  vorhersage = predict(modell, newdata = data.frame(x = seq(1, 10, 0.5)))
)

# Speichere die Ergebnisse
write.csv(ergebnisse, "ergebnisse.csv", row.names = FALSE)
print("Ergebnisse wurden in 'ergebnisse.csv' gespeichert.")
```

