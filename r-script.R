# Einfaches R-Skript für GitHub Actions mit Tidyverse
# Installiere Abhängigkeiten
install.packages(c("ggplot2", "dplyr", "tidyr", "readr", "tibble"))

# Lade Bibliotheken
library(ggplot2)
library(dplyr)
library(readr)
library(tibble)

# Print Informationen zur R-Version
print("R-Version Information:")
print(R.version)

# Erstelle einen einfachen Datensatz
daten <- tibble(
  x = 1:50,
  y = rnorm(50, mean = 5, sd = 1.4)
)

# Berechne einige Statistiken
print("Deskriptive Statistik:")
daten %>%
  summarise(
    mean_y = mean(y),
    sd_y = sd(y),
    min_y = min(y),
    max_y = max(y)
  ) %>%
  print()

# Erstelle ein einfaches lineares Modell
modell <- lm(y ~ x, data = daten)
print("Lineares Modell Zusammenfassung:")
print(summary(modell))

# Erzeuge eine Ausgabedatei mit den Ergebnissen
ergebnisse <- tibble(
  x_wert = seq(1, 10, 0.5)
) %>%
  mutate(vorhersage = predict(modell, newdata = tibble(x = x_wert)))

# Speichere die Ergebnisse
write_csv(ergebnisse, "ergebnisse.csv")
print("Ergebnisse wurden in 'ergebnisse.csv' gespeichert.")

# Visualisierung der Daten und des Modells
p1 <- daten %>%
  ggplot(aes(x = x, y = y)) +
  geom_point() +
  geom_line(data = ergebnisse, aes(x = x_wert, y = vorhersage), color = "blue") +
  ggtitle("Lineares Modell: Daten und Vorhersagen") +
  theme_minimal()

ggsave("modell_visualisierung.png", plot = p1)
print("Die Visualisierung wurde als 'modell_visualisierung.png' gespeichert.")

# Residuenanalyse
residuen <- resid(modell)
p2 <- tibble(x = daten$x, residuen = residuen) %>%
  ggplot(aes(x = x, y = residuen)) +
  geom_point() +
  geom_hline(yintercept = 0, color = "red") +
  ggtitle("Residuenplot") +
  theme_minimal()

ggsave("residuen_visualisierung.png", plot = p2)
print("Residuen-Visualisierung wurde als 'residuen_visualisierung.png' gespeichert.")

# Automatische Überprüfung der Modellgüte
if(summary(modell)$r.squared < 0.8) {
  print("Warnung: Modellgüte (R²) ist unter 0.8!")
}

# Erweiterung: Komplexeres Modell mit einer zusätzlichen Variable
daten <- daten %>%
  mutate(z = rnorm(10, mean = 3, sd = 1))
modell_erweitert <- lm(y ~ x + z, data = daten)
print("Erweitertes Modell Zusammenfassung:")
print(summary(modell_erweitert))

# Modellzusammenfassung speichern
sink("modell_zusammenfassung.txt")
print(summary(modell))
print(summary(modell_erweitert))
sink()

# Hinweis
print("Die erweiterten Analysen und Ergebnisse wurden gespeichert.")
